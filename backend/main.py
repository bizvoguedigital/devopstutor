from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, status, Request, Response, Query
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Literal

from config import settings
from database import init_db, get_db, get_database
from schemas import (
    SessionCreate, SessionResponse, QuestionRequest, QuestionResponse,
    AnswerSubmit, AnswerEvaluation, TranscriptionResponse,
    SessionSummary, HealthCheck, AwsStudyRequest, AwsStudyResponse,
    UserCreate, UserLogin, Token, UserResponse, UserUpdate, UserDashboard,
    AuthMessage, EmailVerificationRequest, EmailVerificationConfirm,
    PasswordResetRequest, PasswordResetConfirm,
    InterviewHistoryItem, InterviewAnalyticsResponse, AnalyticsDimension, PlatformAnalyticsItem,
    CareerJourneyRequest, CareerJourneyResponse, LearningPathResponse,
    UserProgressResponse, UserStatsResponse, ProgressUpdate, ExperienceLevel, CareerTrack,
    ExamStartRequest, ExamSessionResponse, ExamSubmitRequest, ExamResultResponse,
    JourneyPlanResponse, TopicProgressUpdate, TopicProgressResponse,
    ModuleAssessmentUpdate, ModuleAssessmentProgressResponse, ModuleAssessmentReset,
    TtsVoice, TtsStatusResponse, TtsSynthesizeRequest, TtsCacheStatsResponse,
    AdminOverviewResponse, AdminConfigResponse, AdminConfigUpdateRequest,
    AdminTtsProviderStatusResponse, AdminTtsTestRequest, AdminTtsTestResponse,
    ExamProgressUpdateRequest, JourneyContentSyncRequest, JourneyContentSyncResponse,
    JourneyContentSyncJobStartResponse, JourneyContentSyncStatusResponse,
    VoiceRuntimeStatusResponse, VoiceSessionTokenRequest, VoiceSessionTokenResponse,
    InterviewerV2CvUploadResponse, InterviewerV2JobDescriptionUploadResponse,
    InterviewerV2BlueprintGenerateRequest, InterviewerV2BlueprintResponse,
    InterviewerV2SessionStartRequest, InterviewerV2SessionStartResponse,
    InterviewerV2SessionTurnRequest, InterviewerV2SessionTurnResponse,
    InterviewerV2SessionStatusResponse, InterviewerV2SessionCompleteResponse,
    InterviewerV2SessionArtifactResponse, InterviewerV2SessionArtifactListResponse,
    InterviewerV2ArtifactDeleteResponse, InterviewerV2ArtifactCleanupRequest,
    InterviewerV2ArtifactCleanupResponse
)
from services.groq_service import GroqService
from services.interview_engine import interview_engine
from services.exam_service import exam_service
from services.speech_service import speech_to_text_service
from services.tts_service import tts_service
from services.async_auth_service import async_auth_service
from services.learning_service import learning_service
from services.interview_analytics_service import (
    estimate_communication_score,
    dimension_status,
    extract_insight_phrases,
    count_words,
)
from services.aws_learning_service import generate_aws_learning_response
from services.cv_jd_service import cv_jd_service
from services.interview_orchestrator_service import interview_orchestrator_service
from services.interview_policy_service import interview_policy_service
from services.interviewer_v2_session_service import interviewer_v2_session_service
from services.livekit_service import livekit_service
import os

# Initialize services
groq_service = GroqService()
security = HTTPBearer()
RUNTIME_CONFIG_ID = "runtime_config"

def set_auth_cookies(response: Response, access_token: str, refresh_token: str, access_expires_in: int) -> None:
    cookie_kwargs = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": "/",
    }
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.set_cookie(
        key=settings.ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=access_expires_in,
        **cookie_kwargs
    )
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        **cookie_kwargs
    )


def clear_auth_cookies(response: Response) -> None:
    cookie_kwargs = {
        "path": "/",
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
    }
    if settings.COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.COOKIE_DOMAIN

    response.delete_cookie(settings.ACCESS_COOKIE_NAME, **cookie_kwargs)
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, **cookie_kwargs)


def build_user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=str(user.get("_id")) if user.get("_id") else None,
        user_id=user.get("user_id"),
        email=user.get("email"),
        username=user.get("username"),
        full_name=user.get("full_name"),
        career_track=user.get("career_track"),
        experience_level=user.get("experience_level"),
        profile_picture=user.get("profile_picture"),
        created_at=user.get("created_at"),
        last_login=user.get("last_login"),
        is_active=user.get("is_active", True),
        is_admin=user.get("is_admin", False),
    )


def build_progress_response(progress: dict) -> UserProgressResponse:
    data = dict(progress)
    if "_id" in data:
        data["id"] = str(data["_id"])
        data.pop("_id", None)
    return UserProgressResponse.model_validate(data)


def get_default_runtime_config() -> dict:
    return {
        "tts_default_voice_id": settings.ELEVENLABS_VOICE_ID or "",
        "tts_model_id": settings.ELEVENLABS_MODEL_ID,
        "tts_stability": settings.ELEVENLABS_STABILITY,
        "tts_similarity": settings.ELEVENLABS_SIMILARITY,
        "tts_cache_enabled": settings.TTS_CACHE_ENABLED,
        "tts_cache_ttl_seconds": settings.TTS_CACHE_TTL_SECONDS,
        "tts_cache_max_files": settings.TTS_CACHE_MAX_FILES,
        "max_question_count": settings.MAX_QUESTION_COUNT,
        "session_timeout": settings.SESSION_TIMEOUT,
    }


def normalize_runtime_config(doc: Optional[dict]) -> dict:
    config = get_default_runtime_config()
    if doc:
        for key in config.keys():
            if key in doc and doc.get(key) is not None:
                config[key] = doc.get(key)
    return config


async def get_runtime_config(db: AsyncIOMotorDatabase) -> dict:
    doc = await db.app_config.find_one({"config_id": RUNTIME_CONFIG_ID})
    return normalize_runtime_config(doc)

# Authentication dependency
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> dict:
    """Get current authenticated user"""
    token = credentials.credentials if credentials else None
    if not token:
        token = request.cookies.get(settings.ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get username from token
    payload = async_auth_service.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    
    # Get user from database (async)
    user = await async_auth_service.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Optional authentication dependency (for endpoints that work with or without auth)
async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> Optional[dict]:
    """Get current user if authenticated, None otherwise"""
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("Database initialized")

    try:
        db = get_database()
        await learning_service.ensure_paths_initialized(db)
        print("Learning paths initialized")
    except Exception as e:
        print(f"Warning: Could not initialize learning paths: {e}")

    yield

app = FastAPI(
    title="Ops Mentor AI",
    description="AI-powered cloud, DevOps, and interview practice platform",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register", response_model=Token)
async def register_user(
    user_data: UserCreate,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Register a new user"""
    try:
        token, refresh_token, expires_in = await async_auth_service.register_user(db, user_data)
        set_auth_cookies(response, token.access_token, refresh_token, expires_in)
        return token
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the actual error for debugging
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Login user and return access token"""
    try:
        token, refresh_token, expires_in = await async_auth_service.login_user(db, login_data)
        set_auth_cookies(response, token.access_token, refresh_token, expires_in)
        return token
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        token, new_refresh_token, expires_in = await async_auth_service.rotate_refresh_token(db, refresh_token)
        set_auth_cookies(response, token.access_token, new_refresh_token, expires_in)
        return token
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/api/auth/logout", response_model=AuthMessage)
async def logout_user(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if refresh_token:
        await async_auth_service.revoke_refresh_token(db, refresh_token)
    clear_auth_cookies(response)
    return AuthMessage(message="Logged out")


@app.get("/api/voice/runtime", response_model=VoiceRuntimeStatusResponse)
async def get_voice_runtime_status():
    return VoiceRuntimeStatusResponse(**livekit_service.get_runtime_status())


@app.post("/api/voice/livekit/token", response_model=VoiceSessionTokenResponse)
async def create_livekit_voice_token(
    payload: VoiceSessionTokenRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    try:
        user_id = current_user.get("user_id") if current_user else None
        display_name = current_user.get("username") if current_user else "candidate"

        token, room_name, identity, expires_in = livekit_service.issue_session_token(
            session_id=payload.session_id,
            user_id=user_id,
            room_name=payload.room_name,
            display_name=display_name,
        )

        return VoiceSessionTokenResponse(
            provider="livekit",
            room_name=room_name,
            identity=identity,
            token=token,
            expires_in=expires_in,
            livekit_url=settings.LIVEKIT_URL,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/api/auth/request-email-verification", response_model=AuthMessage)
async def request_email_verification(
    payload: EmailVerificationRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await async_auth_service.get_user_by_email(db, payload.email)
    if not user:
        return AuthMessage(message="If the account exists, a verification link has been generated.")

    token = await async_auth_service.create_email_verification_token(db, user)
    if settings.DEBUG:
        return AuthMessage(
            message="Verification token generated.",
            token=token
        )
    return AuthMessage(message="If the account exists, a verification link has been generated.")

@app.post("/api/auth/verify-email", response_model=AuthMessage)
async def verify_email(payload: EmailVerificationConfirm, db: AsyncIOMotorDatabase = Depends(get_db)):
    success = await async_auth_service.verify_email_token(db, payload.token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return AuthMessage(message="Email verified")

@app.post("/api/auth/request-password-reset", response_model=AuthMessage)
async def request_password_reset(
    payload: PasswordResetRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user = await async_auth_service.get_user_by_email(db, payload.email)
    if not user:
        return AuthMessage(message="If the account exists, a reset link has been generated.")

    token = await async_auth_service.create_password_reset_token(db, user)
    if settings.DEBUG:
        return AuthMessage(message="Reset token generated.", token=token)
    return AuthMessage(message="If the account exists, a reset link has been generated.")

@app.post("/api/auth/reset-password", response_model=AuthMessage)
async def reset_password(payload: PasswordResetConfirm, db: AsyncIOMotorDatabase = Depends(get_db)):
    success = await async_auth_service.reset_password(db, payload.token, payload.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    return AuthMessage(message="Password updated")

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return build_user_response(current_user)

@app.put("/api/auth/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update current user profile"""
    updates = {}
    if update_data.full_name is not None:
        updates["full_name"] = update_data.full_name
    if update_data.career_track is not None:
        updates["career_track"] = update_data.career_track
    if update_data.experience_level is not None:
        updates["experience_level"] = update_data.experience_level

    if updates:
        await db.users.update_one(
            {"user_id": current_user.get("user_id")},
            {"$set": updates},
        )

    user = await async_auth_service.get_user_by_id(db, current_user.get("user_id"))
    return build_user_response(user)


def _calculate_streak(activity_dates: List[datetime]) -> tuple[int, int]:
    if not activity_dates:
        return 0, 0

    unique_dates = sorted({dt.date() for dt in activity_dates}, reverse=True)
    current_streak = 1
    for index in range(1, len(unique_dates)):
        if unique_dates[index - 1] - unique_dates[index] == timedelta(days=1):
            current_streak += 1
        else:
            break

    longest_streak = 1
    run = 1
    for index in range(1, len(unique_dates)):
        if unique_dates[index - 1] - unique_dates[index] == timedelta(days=1):
            run += 1
        else:
            longest_streak = max(longest_streak, run)
            run = 1
    longest_streak = max(longest_streak, run)

    return current_streak, longest_streak


@app.post("/api/auth/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Avatar must be under 5MB")

    extension = Path(file.filename or "").suffix or ".png"
    filename = f"{current_user.get('user_id')}_{uuid.uuid4().hex}{extension}"
    file_path = Path(settings.AVATAR_UPLOAD_DIR) / filename
    file_path.write_bytes(contents)

    await db.users.update_one(
        {"user_id": current_user.get("user_id")},
        {"$set": {"profile_picture": f"/uploads/avatars/{filename}"}},
    )
    updated_user = await async_auth_service.get_user_by_id(db, current_user.get("user_id"))

    return build_user_response(updated_user)


@app.get("/api/auth/dashboard", response_model=UserDashboard)
async def get_user_dashboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    sessions_cursor = db.interview_sessions.find(
        {"user_id": current_user.get("user_id")}
    ).sort("started_at", -1)
    sessions = await sessions_cursor.to_list(length=None)

    activity_dates = [
        (s.get("ended_at") or s.get("started_at"))
        for s in sessions
        if s.get("started_at")
    ]
    current_streak, longest_streak = _calculate_streak(activity_dates)

    completed_sessions = [s for s in sessions if s.get("score") is not None]
    average_score = (
        sum(s.get("score") for s in completed_sessions if s.get("score") is not None) / len(completed_sessions)
        if completed_sessions
        else 0.0
    )
    total_minutes = 0
    for session in sessions:
        if session.get("started_at") and session.get("ended_at"):
            delta = session.get("ended_at") - session.get("started_at")
            total_minutes += int(delta.total_seconds() / 60)

    last_activity = max(activity_dates) if activity_dates else None

    progress_rows = await db.user_progress.find(
        {"user_id": current_user.get("user_id")}
    ).to_list(length=None)
    active_paths = [
        build_progress_response(row)
        for row in progress_rows
        if not row.get("is_completed", False)
    ]
    paths_completed = sum(1 for row in progress_rows if row.get("is_completed", False))

    recommended_paths = await learning_service.get_learning_paths(
        db,
        current_user.get("career_track")
    )
    recommended_paths = recommended_paths[:3]

    recent_sessions = [
        SessionResponse(
            session_id=s.get("session_id"),
            platform=s.get("platform"),
            difficulty=s.get("difficulty"),
            career_track=s.get("career_track"),
            module_id=s.get("module_id"),
            started_at=s.get("started_at"),
            status=s.get("status"),
            user_id=s.get("user_id")
        )
        for s in sessions[:5]
    ]

    interview_history = [
        InterviewHistoryItem(
            session_id=s.get("session_id"),
            platform=s.get("platform"),
            difficulty=s.get("difficulty"),
            started_at=s.get("started_at"),
            ended_at=s.get("ended_at"),
            score=s.get("score"),
            status=s.get("status")
        )
        for s in sessions[:20]
    ]

    stats = UserStatsResponse(
        total_sessions=len(sessions),
        total_time_minutes=total_minutes,
        average_session_score=round(average_score, 1),
        current_streak=current_streak,
        longest_streak=longest_streak,
        paths_completed=paths_completed,
        modules_completed=0,
        achievements_earned=0,
        last_activity=last_activity
    )

    user_response = build_user_response(current_user)

    return UserDashboard(
        user=user_response,
        stats=stats,
        active_paths=active_paths,
        recommended_paths=recommended_paths,
        recent_sessions=recent_sessions,
        interview_history=interview_history
    )


@app.get("/api/auth/interview-analytics", response_model=InterviewAnalyticsResponse)
async def get_interview_analytics(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    user_id = current_user.get("user_id")
    sessions = await db.interview_sessions.find(
        {"user_id": user_id, "score": {"$ne": None}}
    ).to_list(length=None)

    if not sessions:
        now = datetime.utcnow()
        technical_benchmark = 7.5
        communication_benchmark = 7.0
        return InterviewAnalyticsResponse(
            completed_sessions=0,
            total_answered_questions=0,
            interview_readiness=0.0,
            technical_accuracy=AnalyticsDimension(
                name="Technical Accuracy",
                score=0.0,
                benchmark=technical_benchmark,
                status="needs_improvement",
            ),
            communication_effectiveness=AnalyticsDimension(
                name="Communication Effectiveness",
                score=0.0,
                benchmark=communication_benchmark,
                status="needs_improvement",
            ),
            benchmark_percentile=0.0,
            strengths=["Complete your first interview to unlock strengths analysis."],
            improvement_areas=["Practice one full interview to generate personalized feedback."],
            platform_breakdown=[],
            last_updated=now,
        )

    session_ids = [session.get("session_id") for session in sessions if session.get("session_id")]
    responses = await db.question_responses.find(
        {
            "session_id": {"$in": session_ids},
            "user_answer": {"$ne": None},
            "score": {"$ne": None},
        }
    ).to_list(length=None)

    technical_scores = [float(item.get("score", 0.0)) for item in responses]
    technical_avg = round(sum(technical_scores) / len(technical_scores), 2) if technical_scores else 0.0

    communication_scores = []
    for item in responses:
        stored = item.get("communication_score")
        if isinstance(stored, (int, float)):
            communication_scores.append(float(stored))
        else:
            communication_scores.append(estimate_communication_score(str(item.get("user_answer") or "")))
    communication_avg = round(sum(communication_scores) / len(communication_scores), 2) if communication_scores else 0.0

    readiness = round((technical_avg * 0.75) + (communication_avg * 0.25), 2)
    percentile = round(max(0.0, min(100.0, readiness * 10.0)), 1)

    strengths_source = [
        str(item.get("strengths") or "") for item in responses
    ] + [
        str(item.get("best_practices") or "") for item in responses
    ] + [
        str(item.get("real_world_insights") or "") for item in responses
    ]
    strengths = extract_insight_phrases(
        strengths_source,
        ["You are building consistency by completing interviews and collecting actionable feedback."],
    )

    improvement_source = [
        str(item.get("weaknesses") or "") for item in responses
    ] + [
        str(item.get("learning_opportunities") or "") for item in responses
    ]
    improvement_areas = extract_insight_phrases(
        improvement_source,
        ["Focus on adding clearer architecture trade-offs and implementation detail in each answer."],
    )

    platform_map = {}
    for session in sessions:
        platform = str(session.get("platform") or "unknown").lower()
        score = float(session.get("score") or 0.0)
        if platform not in platform_map:
            platform_map[platform] = {"total": 0.0, "count": 0}
        platform_map[platform]["total"] += score
        platform_map[platform]["count"] += 1

    platform_breakdown = [
        PlatformAnalyticsItem(
            platform=platform,
            sessions=data["count"],
            average_score=round(data["total"] / data["count"], 2) if data["count"] else 0.0,
        )
        for platform, data in sorted(platform_map.items(), key=lambda item: item[0])
    ]

    technical_benchmark = 7.5
    communication_benchmark = 7.0
    return InterviewAnalyticsResponse(
        completed_sessions=len(sessions),
        total_answered_questions=len(responses),
        interview_readiness=readiness,
        technical_accuracy=AnalyticsDimension(
            name="Technical Accuracy",
            score=technical_avg,
            benchmark=technical_benchmark,
            status=dimension_status(technical_avg, technical_benchmark),
        ),
        communication_effectiveness=AnalyticsDimension(
            name="Communication Effectiveness",
            score=communication_avg,
            benchmark=communication_benchmark,
            status=dimension_status(communication_avg, communication_benchmark),
        ),
        benchmark_percentile=percentile,
        strengths=strengths,
        improvement_areas=improvement_areas,
        platform_breakdown=platform_breakdown,
        last_updated=datetime.utcnow(),
    )

# ============================================================================
# LEARNING JOURNEY ENDPOINTS
# ============================================================================

@app.post("/api/journey/recommend", response_model=CareerJourneyResponse)
async def get_career_journey(
    journey_request: CareerJourneyRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get personalized career journey recommendations"""
    try:
        return await learning_service.get_career_journey(db, journey_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/journey/plan", response_model=JourneyPlanResponse)
async def get_journey_plan(
    journey_request: CareerJourneyRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get step-by-step journey plan with teaching, hands-on, and MCQs"""
    try:
        return await learning_service.get_journey_plan(
            db,
            journey_request,
            user_id=current_user.get("user_id") if current_user else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/journey/topics/progress", response_model=TopicProgressResponse)
async def update_topic_progress(
    progress_update: TopicProgressUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update topic-level progress for a journey module"""
    try:
        return await learning_service.update_topic_progress(db, current_user.get("user_id"), progress_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/journey/modules/assessment", response_model=ModuleAssessmentProgressResponse)
async def update_module_assessment(
    progress_update: ModuleAssessmentUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update module assessment progress"""
    try:
        return await learning_service.update_module_assessment(db, current_user.get("user_id"), progress_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/journey/modules/assessment/reset", response_model=ModuleAssessmentProgressResponse)
async def reset_module_assessment(
    reset_data: ModuleAssessmentReset,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Reset module assessment progress"""
    try:
        return await learning_service.reset_module_assessment(db, current_user.get("user_id"), reset_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/learning/paths", response_model=List[LearningPathResponse])
async def get_learning_paths(
    career_track: Optional[CareerTrack] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all learning paths, optionally filtered by career track"""
    try:
        paths = await learning_service.get_learning_paths(db, career_track)
        return paths
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch learning paths")

@app.post("/api/learning/paths/{path_id}/start", response_model=UserProgressResponse)
async def start_learning_path(
    path_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start a learning path for the authenticated user"""
    try:
        progress = await learning_service.start_learning_path(db, current_user.get("user_id"), path_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start learning path")

@app.get("/api/learning/progress", response_model=List[UserProgressResponse])
async def get_user_progress(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all learning progress for the authenticated user"""
    try:
        progress = await learning_service.get_user_progress(db, current_user.get("user_id"))
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch user progress")

@app.put("/api/learning/progress", response_model=dict)
async def update_module_progress(
    progress_update: ProgressUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update progress for a specific module"""
    try:
        result = await learning_service.update_module_progress(db, current_user.get("user_id"), progress_update)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update progress")


# ============================================================================
# AI INTERVIEWER V2 ENDPOINTS (CV + JD + BLUEPRINT)
# ============================================================================

@app.post("/api/interviewer-v2/documents/cv", response_model=InterviewerV2CvUploadResponse)
async def upload_cv_document(
    file: UploadFile = File(...),
    raw_text: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="CV filename is required")

    allowed_content_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown",
    }
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Unsupported CV file type")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="CV file must be under 5MB")

    try:
        doc = await cv_jd_service.ingest_cv(
            db=db,
            user_id=current_user.get("user_id"),
            filename=file.filename,
            content_type=content_type,
            content=content,
            raw_text=raw_text,
        )
        return InterviewerV2CvUploadResponse(**doc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to ingest CV: {exc}")


@app.post("/api/interviewer-v2/documents/job-description", response_model=InterviewerV2JobDescriptionUploadResponse)
async def upload_job_description_document(
    file: UploadFile = File(...),
    raw_text: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Job description filename is required")

    allowed_content_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown",
    }
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Unsupported job description file type")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Job description file must be under 5MB")

    try:
        doc = await cv_jd_service.ingest_job_description(
            db=db,
            user_id=current_user.get("user_id"),
            filename=file.filename,
            content_type=content_type,
            content=content,
            raw_text=raw_text,
        )
        return InterviewerV2JobDescriptionUploadResponse(**doc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to ingest job description: {exc}")


@app.post("/api/interviewer-v2/blueprints/generate", response_model=InterviewerV2BlueprintResponse)
async def generate_interviewer_v2_blueprint(
    payload: InterviewerV2BlueprintGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        blueprint = await interview_orchestrator_service.generate_blueprint(
            db=db,
            user_id=current_user.get("user_id"),
            cv_document_id=payload.cv_document_id,
            jd_document_id=payload.jd_document_id,
            target_duration_minutes=payload.target_duration_minutes,
            strict_mode=payload.strict_mode,
        )
        return InterviewerV2BlueprintResponse(**blueprint)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate interview blueprint: {exc}")


@app.post("/api/interviewer-v2/sessions/start", response_model=InterviewerV2SessionStartResponse)
async def start_interviewer_v2_session(
    payload: InterviewerV2SessionStartRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.start_session(
            db=db,
            user_id=current_user.get("user_id"),
            blueprint_id=payload.blueprint_id,
        )
        return InterviewerV2SessionStartResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start interviewer-v2 session: {exc}")


@app.post("/api/interviewer-v2/sessions/{session_id}/turn", response_model=InterviewerV2SessionTurnResponse)
async def submit_interviewer_v2_turn(
    session_id: str,
    payload: InterviewerV2SessionTurnRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        session_status = await interviewer_v2_session_service.get_session_status(
            db=db,
            user_id=current_user.get("user_id"),
            session_id=session_id,
        )

        policy_result = interview_policy_service.evaluate_user_response(
            user_response=payload.user_response,
            active_question=session_status.get("current_question"),
            strict_mode=bool(session_status.get("strict_mode", True)),
        )

        result = await interviewer_v2_session_service.submit_turn(
            db=db,
            user_id=current_user.get("user_id"),
            session_id=session_id,
            user_response=payload.user_response,
            policy_result=policy_result,
        )
        return InterviewerV2SessionTurnResponse(**result)
    except ValueError as exc:
        detail = str(exc)
        code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=code, detail=detail)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process interviewer-v2 turn: {exc}")


@app.get("/api/interviewer-v2/sessions/{session_id}/status", response_model=InterviewerV2SessionStatusResponse)
async def get_interviewer_v2_session_status(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.get_session_status(
            db=db,
            user_id=current_user.get("user_id"),
            session_id=session_id,
        )
        return InterviewerV2SessionStatusResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch interviewer-v2 session status: {exc}")


@app.post("/api/interviewer-v2/sessions/{session_id}/complete", response_model=InterviewerV2SessionCompleteResponse)
async def complete_interviewer_v2_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.complete_session(
            db=db,
            user_id=current_user.get("user_id"),
            session_id=session_id,
        )
        return InterviewerV2SessionCompleteResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to complete interviewer-v2 session: {exc}")


@app.get("/api/interviewer-v2/sessions/{session_id}/artifact", response_model=InterviewerV2SessionArtifactResponse)
async def get_interviewer_v2_session_artifact(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.get_session_artifact(
            db=db,
            user_id=current_user.get("user_id"),
            session_id=session_id,
        )
        return InterviewerV2SessionArtifactResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch interviewer-v2 session artifact: {exc}")


@app.get("/api/interviewer-v2/artifacts/{session_artifact_id}", response_model=InterviewerV2SessionArtifactResponse)
async def get_interviewer_v2_artifact_by_id(
    session_artifact_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.get_artifact_by_id(
            db=db,
            user_id=current_user.get("user_id"),
            session_artifact_id=session_artifact_id,
        )
        return InterviewerV2SessionArtifactResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch interviewer-v2 artifact: {exc}")


@app.get("/api/interviewer-v2/artifacts", response_model=InterviewerV2SessionArtifactListResponse)
async def list_interviewer_v2_artifacts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
    status: Optional[str] = Query(None, min_length=1, max_length=32),
    readiness_band: Optional[Literal["emerging", "progressing", "interview_ready"]] = Query(None),
    sort_by: Literal["created_at", "average_score", "interview_readiness_score"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.list_artifacts(
            db=db,
            user_id=current_user.get("user_id"),
            limit=limit,
            offset=offset,
            status=status,
            readiness_band=readiness_band,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return InterviewerV2SessionArtifactListResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list interviewer-v2 artifacts: {exc}")


@app.delete("/api/interviewer-v2/artifacts/{session_artifact_id}", response_model=InterviewerV2ArtifactDeleteResponse)
async def delete_interviewer_v2_artifact_by_id(
    session_artifact_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.delete_artifact_by_id(
            db=db,
            user_id=current_user.get("user_id"),
            session_artifact_id=session_artifact_id,
        )
        return InterviewerV2ArtifactDeleteResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete interviewer-v2 artifact: {exc}")


@app.post("/api/interviewer-v2/artifacts/cleanup", response_model=InterviewerV2ArtifactCleanupResponse)
async def cleanup_interviewer_v2_artifacts(
    payload: InterviewerV2ArtifactCleanupRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        result = await interviewer_v2_session_service.cleanup_artifacts(
            db=db,
            user_id=current_user.get("user_id"),
            keep_latest=payload.keep_latest,
            dry_run=payload.dry_run,
        )
        return InterviewerV2ArtifactCleanupResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup interviewer-v2 artifacts: {exc}")

# Health check endpoint
@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    groq_status = await groq_service.check_connection()
    return HealthCheck(
        status="healthy" if groq_status else "degraded",
        llm_connected=groq_status,
        model=settings.GROQ_MODEL,
        whisper_available=speech_to_text_service.available,
        whisper_model=settings.WHISPER_MODEL if speech_to_text_service.available else None
    )

# Certification Exam Simulator
@app.post("/api/exams/start", response_model=ExamSessionResponse)
async def start_exam(
    request: ExamStartRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    exam_id = str(uuid.uuid4())
    duration_minutes = exam_service.get_exam_duration_minutes(request.certificate)
    started_at = datetime.utcnow()

    exam_session = {
        "exam_id": exam_id,
        "user_id": current_user.get("user_id") if current_user else None,
        "certificate": request.certificate,
        "question_count": request.question_count,
        "duration_minutes": duration_minutes,
        "status": "active",
        "started_at": started_at,
        "remaining_seconds": duration_minutes * 60,
        "current_index": 0,
        "answers": {},
        "flagged": {},
        "ended_at": None,
        "score": None,
    }
    await db.exam_sessions.insert_one(exam_session)

    questions = await exam_service.generate_exam_questions(
        certificate=request.certificate,
        question_count=request.question_count
    )

    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate exam questions")

    exam_questions: List[dict] = []
    for index, item in enumerate(questions, start=1):
        question_id = str(uuid.uuid4())
        exam_questions.append({
            "question_id": question_id,
            "exam_id": exam_id,
            "question_number": index,
            "prompt": item.get("prompt", ""),
            "options": item.get("options", []),
            "correct_option": item.get("correct_option", "A"),
            "explanation": item.get("explanation", ""),
            "category": item.get("category", "general"),
        })

    if exam_questions:
        await db.exam_questions.insert_many(exam_questions)

    response_questions = [
        {
            "id": question["question_id"],
            "question_number": question["question_number"],
            "prompt": question["prompt"],
            "options": question["options"],
            "category": question["category"],
        }
        for question in exam_questions
    ]

    return ExamSessionResponse(
        exam_id=exam_id,
        certificate=request.certificate,
        question_count=request.question_count,
        duration_minutes=duration_minutes,
        started_at=started_at,
        remaining_seconds=duration_minutes * 60,
        current_index=0,
        answers={},
        flagged={},
        is_resumed=False,
        questions=response_questions
    )


@app.get("/api/exams/active", response_model=ExamSessionResponse)
async def get_active_exam(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    exam_session = await db.exam_sessions.find_one(
        {"user_id": current_user.get("user_id"), "status": "active"},
        sort=[("started_at", -1)],
    )

    if not exam_session:
        raise HTTPException(status_code=404, detail="No active exam found")

    questions = await db.exam_questions.find(
        {"exam_id": exam_session.get("exam_id")}
    ).sort("question_number", 1).to_list(length=None)

    response_questions = [
        {
            "id": question.get("question_id"),
            "question_number": question.get("question_number"),
            "prompt": question.get("prompt"),
            "options": question.get("options", []),
            "category": question.get("category"),
        }
        for question in questions
    ]

    return ExamSessionResponse(
        exam_id=exam_session.get("exam_id"),
        certificate=exam_session.get("certificate"),
        question_count=exam_session.get("question_count", len(response_questions)),
        duration_minutes=exam_session.get("duration_minutes", 130),
        started_at=exam_session.get("started_at"),
        remaining_seconds=exam_session.get("remaining_seconds"),
        current_index=exam_session.get("current_index", 0),
        answers=exam_session.get("answers", {}),
        flagged=exam_session.get("flagged", {}),
        is_resumed=True,
        questions=response_questions,
    )


@app.put("/api/exams/{exam_id}/progress")
async def save_exam_progress(
    exam_id: str,
    payload: ExamProgressUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    exam_session = await db.exam_sessions.find_one({"exam_id": exam_id})
    if not exam_session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    if exam_session.get("user_id") != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="You cannot modify this exam session")

    if exam_session.get("status") != "active":
        raise HTTPException(status_code=400, detail="Exam session is not active")

    updates = {
        "answers": payload.answers,
        "flagged": payload.flagged,
        "current_index": payload.current_index,
        "updated_at": datetime.utcnow(),
    }
    if payload.remaining_seconds is not None:
        updates["remaining_seconds"] = payload.remaining_seconds

    await db.exam_sessions.update_one(
        {"exam_id": exam_id},
        {"$set": updates},
    )

    return {"saved": True}


@app.post("/api/exams/submit", response_model=ExamResultResponse)
async def submit_exam(
    request: ExamSubmitRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    exam_session = await db.exam_sessions.find_one({"exam_id": request.exam_id})

    if not exam_session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    questions = await db.exam_questions.find({"exam_id": request.exam_id}).sort("question_number", 1).to_list(length=None)

    answer_map = dict(exam_session.get("answers", {}))
    for answer in request.answers:
        if answer.question_id is None:
            continue
        answer_key = str(answer.question_id).strip()
        if not answer_key:
            continue
        selected_value = (answer.selected_option or "").strip()
        answer_map[answer_key] = selected_value

    correct_count = 0
    unanswered_count = 0
    review = []
    answer_docs = []
    category_totals = {}
    category_correct = {}

    for question in questions:
        selected_raw = (answer_map.get(question.get("question_id")) or "").strip().upper()
        selected = selected_raw[0] if selected_raw[:1] in {"A", "B", "C", "D"} else ""
        is_correct = selected == question.get("correct_option")

        category = (question.get("category") or "general").strip().lower()
        category_totals[category] = category_totals.get(category, 0) + 1

        if is_correct:
            correct_count += 1
            category_correct[category] = category_correct.get(category, 0) + 1
        elif not selected:
            unanswered_count += 1

        answer_docs.append({
            "exam_id": request.exam_id,
            "question_id": question.get("question_id"),
            "selected_option": selected,
            "is_correct": is_correct,
        })

        review.append({
            "question_id": question.get("question_id"),
            "question_number": question.get("question_number"),
            "prompt": question.get("prompt"),
            "options": question.get("options"),
            "selected_option": selected,
            "correct_option": question.get("correct_option"),
            "is_correct": is_correct,
            "explanation": question.get("explanation"),
            "category": category,
        })

    total_questions = len(questions)
    score_percent = round((correct_count / total_questions) * 100, 1) if total_questions else 0.0
    pass_mark = 70.0

    category_breakdown = []
    for category, total in category_totals.items():
        correct = category_correct.get(category, 0)
        accuracy = round((correct / total) * 100, 1) if total else 0.0
        category_breakdown.append({
            "category": category,
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
        })

    category_breakdown.sort(key=lambda item: item["accuracy"])

    recommendations = []
    weak_domains = [item for item in category_breakdown if item["accuracy"] < 70]
    if weak_domains:
        recommendations.append(
            f"Prioritize weakest domains: {', '.join(item['category'] for item in weak_domains[:3])}."
        )
    if unanswered_count > 0:
        recommendations.append(
            f"You left {unanswered_count} question(s) unanswered. Practice pacing and eliminate unlikely options faster."
        )
    if score_percent >= pass_mark:
        recommendations.append("Great progress. Keep practicing mixed-domain sets to maintain consistency.")
    else:
        recommendations.append("Revisit core service decision patterns and scenario trade-off analysis before your next attempt.")

    if answer_docs:
        await db.exam_answers.insert_many(answer_docs)

    await db.exam_sessions.update_one(
        {"exam_id": request.exam_id},
        {
            "$set": {
                "score": score_percent,
                "status": "completed",
                "ended_at": datetime.utcnow(),
                "remaining_seconds": 0,
            }
        },
    )

    return ExamResultResponse(
        exam_id=request.exam_id,
        certificate=exam_session.get("certificate"),
        total_questions=total_questions,
        correct_count=correct_count,
        unanswered_count=unanswered_count,
        score_percent=score_percent,
        pass_mark=pass_mark,
        passed=score_percent >= pass_mark,
        category_breakdown=category_breakdown,
        recommendations=recommendations,
        review=review
    )

# Session endpoints
@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new interview session (supports both authenticated and anonymous users)"""
    try:
        print(f"Creating session with data: {session_data}")
        print(f"Platform: {session_data.platform}, Difficulty: {session_data.difficulty}")
        print(f"Career track: {session_data.career_track}, Module ID: {session_data.module_id}")
        print(f"Current user: {current_user.get('user_id') if current_user else 'Anonymous'}")
        
        session_id = str(uuid.uuid4())

        new_session = {
            "session_id": session_id,
            "user_id": current_user.get("user_id") if current_user else None,
            "platform": session_data.platform,
            "difficulty": session_data.difficulty,
            "career_track": session_data.career_track,
            "module_id": session_data.module_id,
            "started_at": datetime.utcnow(),
            "ended_at": None,
            "total_questions": 0,
            "score": None,
            "status": "active",
            "performance_data": {},
            "feedback_summary": None,
        }

        await db.interview_sessions.insert_one(new_session)
        print("Session stored in MongoDB")

        response = SessionResponse(
            session_id=new_session["session_id"],
            platform=new_session["platform"],
            difficulty=new_session["difficulty"],
            career_track=new_session.get("career_track"),
            module_id=new_session.get("module_id"),
            started_at=new_session["started_at"],
            status=new_session["status"],
            user_id=new_session.get("user_id")
        )
        
        print(f"Session created successfully: {new_session['session_id']}")
        return response
        
    except ValueError as ve:
        print(f"Validation error creating session: {ve}")
        raise HTTPException(status_code=400, detail=f"Invalid session data: {str(ve)}")
    except Exception as e:
        print(f"Unexpected error creating session: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get session details"""
    session = await db.interview_sessions.find_one({"session_id": session_id})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        session_id=session.get("session_id"),
        platform=session.get("platform"),
        difficulty=session.get("difficulty"),
        started_at=session.get("started_at"),
        status=session.get("status")
    )

# Question endpoints
@app.post("/api/questions/generate", response_model=QuestionResponse)
async def generate_question(
    request: QuestionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Generate a new interview question"""

    session = await db.interview_sessions.find_one({"session_id": request.session_id})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    runtime_config = await get_runtime_config(db)
    configured_max_questions = int(runtime_config.get("max_question_count", settings.MAX_QUESTION_COUNT))

    # Get previous Q&A for context
    prev_questions = await db.question_responses.find(
        {"session_id": request.session_id}
    ).sort("question_number", 1).to_list(length=None)

    if len(prev_questions) >= configured_max_questions:
        raise HTTPException(status_code=400, detail="Maximum question limit reached for this session")

    previous_context = [
        {
            "question": q.get("question_text"),
            "answer": q.get("user_answer") or "No answer"
        }
        for q in prev_questions
    ]

    previous_scores = [
        float(q.get("score"))
        for q in prev_questions
        if q.get("score") is not None
    ]

    last_answer = None
    for item in reversed(prev_questions):
        if item.get("user_answer"):
            last_answer = item.get("user_answer")
            break

    # Generate question
    question_text = await interview_engine.generate_question(
        platform=session.get("platform"),
        difficulty=session.get("difficulty"),
        category=request.category,
        previous_context=previous_context,
        previous_scores=previous_scores,
        last_answer=last_answer,
    )

    # Save question to DB
    question_number = len(prev_questions) + 1
    new_question = {
        "session_id": request.session_id,
        "question_number": question_number,
        "question_text": question_text,
        "question_category": request.category,
        "user_answer": None,
        "ai_feedback": None,
        "score": None,
        "timestamp": datetime.utcnow(),
        "audio_path": None,
        "response_time_seconds": None,
        "created_at": datetime.utcnow(),
    }
    await db.question_responses.insert_one(new_question)

    return QuestionResponse(
        question=question_text,
        question_number=question_number,
        category=request.category
    )

# Answer endpoints
@app.post("/api/answers/submit", response_model=AnswerEvaluation)
async def submit_answer(
    answer_data: AnswerSubmit,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Submit an answer and get evaluation"""

    question = await db.question_responses.find_one(
        {
            "session_id": answer_data.session_id,
            "question_number": answer_data.question_id,
        },
        sort=[("created_at", -1)],
    )

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Evaluate answer
    evaluation = await interview_engine.evaluate_answer(
        question=question.get("question_text"),
        answer=answer_data.answer_text
    )

    # Update question with answer and feedback
    communication_score = estimate_communication_score(answer_data.answer_text)
    await db.question_responses.update_one(
        {"_id": question.get("_id")},
        {
            "$set": {
                "user_answer": answer_data.answer_text,
                "ai_feedback": evaluation.get("feedback", ""),
                "score": float(evaluation.get("score", 0)),
                "audio_path": answer_data.audio_path,
                "communication_score": communication_score,
                "word_count": count_words(answer_data.answer_text),
                "learning_opportunities": evaluation.get("learning_opportunities", ""),
                "best_practices": evaluation.get("best_practices", ""),
                "real_world_insights": evaluation.get("real_world_insights", ""),
                "model_answer": evaluation.get("model_answer", ""),
                "strengths": evaluation.get("strengths", ""),
                "weaknesses": evaluation.get("weaknesses", ""),
                "overall": evaluation.get("overall", ""),
            }
        },
    )

    # Generate follow-up question if appropriate
    follow_up = None
    if evaluation.get("score", 0) >= 5:
        follow_up = await interview_engine.generate_follow_up(
            original_question=question.get("question_text"),
            answer=answer_data.answer_text,
            evaluation=evaluation
        )

    return AnswerEvaluation(
        score=evaluation.get("score", 0),
        feedback=evaluation.get("feedback", ""),
        model_answer=evaluation.get("model_answer", ""),
        learning_opportunities=evaluation.get("learning_opportunities", ""),
        best_practices=evaluation.get("best_practices", ""),
        real_world_insights=evaluation.get("real_world_insights", ""),
        # Legacy fields for backward compatibility
        strengths=evaluation.get("strengths", ""),
        weaknesses=evaluation.get("weaknesses", ""),
        overall=evaluation.get("overall", ""),
        follow_up_question=follow_up
    )

# Speech endpoints
@app.post("/api/speech/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio to text"""

    # Save uploaded file temporarily
    file_path = os.path.join(settings.AUDIO_UPLOAD_DIR, f"{uuid.uuid4()}.wav")

    with open(file_path, "wb") as f:
        content = await audio.read()
        f.write(content)

    try:
        # Transcribe
        transcription = await speech_to_text_service.transcribe_audio(file_path)

        return TranscriptionResponse(
            text=transcription
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)

# TTS endpoints
@app.get("/api/tts/status", response_model=TtsStatusResponse)
async def tts_status(db: AsyncIOMotorDatabase = Depends(get_db)):
    runtime_config = await get_runtime_config(db)
    tts_service.apply_runtime_config(runtime_config)
    provider_ready, availability_reason = await tts_service.check_provider_health()
    return TtsStatusResponse(
        available=provider_ready,
        provider="elevenlabs",
        provider_configured=tts_service.available,
        availability_reason=availability_reason,
        default_voice_id=runtime_config.get("tts_default_voice_id") or None,
        model_id=runtime_config.get("tts_model_id") or None,
    )


@app.get("/api/tts/voices", response_model=List[TtsVoice])
async def list_tts_voices():
    provider_ready, availability_reason = await tts_service.check_provider_health()
    if not provider_ready:
        detail = "TTS provider not configured" if availability_reason == "api_key_missing" else f"TTS provider unavailable: {availability_reason}"
        raise HTTPException(status_code=503, detail=detail)

    try:
        voices = await tts_service.list_voices()
        return [TtsVoice(**voice) for voice in voices]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"TTS provider error: {exc}")


@app.post("/api/tts/synthesize")
async def synthesize_tts(payload: TtsSynthesizeRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    provider_ready, availability_reason = await tts_service.check_provider_health()
    if not provider_ready:
        detail = "TTS provider not configured" if availability_reason == "api_key_missing" else f"TTS provider unavailable: {availability_reason}"
        raise HTTPException(status_code=503, detail=detail)

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    runtime_config = await get_runtime_config(db)
    tts_service.apply_runtime_config(runtime_config)

    stability_value = payload.stability
    if stability_value is None:
        stability_value = runtime_config.get("tts_stability", settings.ELEVENLABS_STABILITY)

    similarity_value = payload.similarity_boost
    if similarity_value is None:
        similarity_value = runtime_config.get("tts_similarity", settings.ELEVENLABS_SIMILARITY)

    try:
        audio_bytes, content_type = await tts_service.synthesize(
            text=text,
            voice_id=payload.voice_id,
            stability=stability_value,
            similarity_boost=similarity_value,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"TTS provider error: {exc}")

    return Response(content=audio_bytes, media_type=content_type)


@app.get("/api/tts/cache/stats", response_model=TtsCacheStatsResponse)
async def tts_cache_stats():
    return TtsCacheStatsResponse(**tts_service.get_cache_stats())


@app.get("/api/admin/overview", response_model=AdminOverviewResponse)
async def admin_overview(
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    runtime_config = await get_runtime_config(db)
    tts_service.apply_runtime_config(runtime_config)

    total_users = await db.users.count_documents({})
    active_sessions = await db.interview_sessions.count_documents({"status": "active"})
    completed_sessions = await db.interview_sessions.count_documents({"status": "completed"})

    return AdminOverviewResponse(
        total_users=total_users,
        active_sessions=active_sessions,
        completed_sessions=completed_sessions,
        tts_cache=TtsCacheStatsResponse(**tts_service.get_cache_stats()),
    )


@app.get("/api/admin/config", response_model=AdminConfigResponse)
async def admin_get_config(
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    runtime_config = await get_runtime_config(db)
    return AdminConfigResponse(**runtime_config)


@app.put("/api/admin/config", response_model=AdminConfigResponse)
async def admin_update_config(
    payload: AdminConfigUpdateRequest,
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    updates = payload.model_dump(exclude_none=True)

    if "tts_stability" in updates:
        updates["tts_stability"] = max(0.0, min(1.0, float(updates["tts_stability"])))
    if "tts_similarity" in updates:
        updates["tts_similarity"] = max(0.0, min(1.0, float(updates["tts_similarity"])))
    if "tts_cache_ttl_seconds" in updates:
        updates["tts_cache_ttl_seconds"] = max(0, int(updates["tts_cache_ttl_seconds"]))
    if "tts_cache_max_files" in updates:
        updates["tts_cache_max_files"] = max(0, int(updates["tts_cache_max_files"]))
    if "max_question_count" in updates:
        updates["max_question_count"] = max(1, int(updates["max_question_count"]))
    if "session_timeout" in updates:
        updates["session_timeout"] = max(300, int(updates["session_timeout"]))

    if updates:
        await db.app_config.update_one(
            {"config_id": RUNTIME_CONFIG_ID},
            {
                "$set": {
                    **updates,
                    "updated_at": datetime.utcnow(),
                    "updated_by": admin_user.get("user_id"),
                }
            },
            upsert=True,
        )

    runtime_config = await get_runtime_config(db)
    tts_service.apply_runtime_config(runtime_config)
    return AdminConfigResponse(**runtime_config)


@app.post("/api/admin/tts/cache/clear")
async def admin_clear_tts_cache(
    admin_user: dict = Depends(require_admin)
):
    removed = tts_service.clear_cache()
    return {"removed_files": removed}


@app.get("/api/admin/tts/provider-status", response_model=AdminTtsProviderStatusResponse)
async def admin_tts_provider_status(
    force_check: bool = True,
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    runtime_config = await get_runtime_config(db)
    tts_service.apply_runtime_config(runtime_config)
    provider_ready, availability_reason = await tts_service.check_provider_health(force=force_check)
    return AdminTtsProviderStatusResponse(
        available=provider_ready,
        provider="elevenlabs",
        provider_configured=tts_service.available,
        availability_reason=availability_reason,
        default_voice_id=runtime_config.get("tts_default_voice_id") or None,
        model_id=runtime_config.get("tts_model_id") or None,
    )


@app.post("/api/admin/tts/test", response_model=AdminTtsTestResponse)
async def admin_tts_test(
    payload: AdminTtsTestRequest,
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    runtime_config = await get_runtime_config(db)
    tts_service.apply_runtime_config(runtime_config)
    provider_ready, availability_reason = await tts_service.check_provider_health(force=True)

    if not provider_ready:
        reason = availability_reason or "provider_unavailable"
        message = "TTS provider not configured" if reason == "api_key_missing" else f"TTS provider unavailable: {reason}"
        return AdminTtsTestResponse(
            success=False,
            provider="elevenlabs",
            availability_reason=reason,
            message=message,
            generated_bytes=0,
        )

    test_text = (payload.text or "ElevenLabs test successful. Admin TTS is ready.").strip()
    if not test_text:
        test_text = "ElevenLabs test successful. Admin TTS is ready."

    stability_value = runtime_config.get("tts_stability", settings.ELEVENLABS_STABILITY)
    similarity_value = runtime_config.get("tts_similarity", settings.ELEVENLABS_SIMILARITY)

    try:
        audio_bytes, _content_type = await tts_service.synthesize(
            text=test_text,
            voice_id=payload.voice_id,
            stability=stability_value,
            similarity_boost=similarity_value,
        )
        generated_bytes = len(audio_bytes or b"")
        return AdminTtsTestResponse(
            success=generated_bytes > 0,
            provider="elevenlabs",
            availability_reason=None,
            message="TTS test succeeded." if generated_bytes > 0 else "TTS test failed: empty audio response.",
            generated_bytes=generated_bytes,
        )
    except Exception as exc:
        return AdminTtsTestResponse(
            success=False,
            provider="elevenlabs",
            availability_reason="synthesis_failed",
            message=f"TTS test failed: {exc}",
            generated_bytes=0,
        )


@app.post("/api/admin/journey/content/sync", response_model=JourneyContentSyncResponse)
async def admin_sync_journey_content(
    payload: JourneyContentSyncRequest,
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        result = await learning_service.sync_cloud_content_cache(
            db,
            cloud_provider=payload.cloud_provider,
            experience_level=payload.experience_level,
            force_refresh=payload.force_refresh,
        )
        return JourneyContentSyncResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Journey content sync failed: {exc}")


@app.post("/api/admin/journey/content/sync/start", response_model=JourneyContentSyncJobStartResponse)
async def admin_start_journey_content_sync(
    payload: JourneyContentSyncRequest,
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        result = await learning_service.start_cloud_content_sync_job(
            db,
            requested_by=admin_user.get("user_id") or admin_user.get("username") or "admin",
            cloud_provider=payload.cloud_provider,
            experience_level=payload.experience_level,
            force_refresh=payload.force_refresh,
        )
        return JourneyContentSyncJobStartResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Journey content background sync failed to start: {exc}")


@app.get("/api/admin/journey/content/sync/status", response_model=JourneyContentSyncStatusResponse)
async def admin_get_journey_content_sync_status(
    admin_user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        result = await learning_service.get_cloud_content_sync_status(db)
        return JourneyContentSyncStatusResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read journey sync status: {exc}")

# Session summary
@app.post("/api/sessions/{session_id}/complete", response_model=SessionSummary)
async def complete_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Complete session and generate summary"""

    session = await db.interview_sessions.find_one({"session_id": session_id})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = await db.question_responses.find({"session_id": session_id}).sort("question_number", 1).to_list(length=None)

    questions_and_answers = [
        {
            "question": q.get("question_text"),
            "answer": q.get("user_answer") or "No answer",
            "score": q.get("score") or 0
        }
        for q in questions
    ]

    # Generate summary
    summary = await interview_engine.generate_session_summary(
        questions_and_answers=questions_and_answers,
        platform=session.get("platform"),
        difficulty=session.get("difficulty")
    )

    await db.interview_sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "status": "completed",
                "ended_at": datetime.utcnow(),
                "total_questions": len(questions),
                "score": summary.get("overall_score", 0),
            }
        },
    )

    return SessionSummary(
        session_id=session_id,
        overall_score=summary.get("overall_score", 0),
        strengths=summary.get("strengths", []),
        improvements=summary.get("improvements", []),
        study_topics=summary.get("study_topics", []),
        readiness=summary.get("readiness", ""),
        summary=summary.get("summary", ""),
        total_questions=len(questions),
        platform=session.get("platform"),
        difficulty=session.get("difficulty")
    )

# AWS Study Mode endpoint
@app.post("/api/aws/learn", response_model=AwsStudyResponse)
async def start_aws_learning(request: AwsStudyRequest):
    """Start an AWS service learning session."""
    try:
        return await generate_aws_learning_response(groq_service, request.service_name)
    except Exception as e:
        print(f"Error generating AWS learning content: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate learning content")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
