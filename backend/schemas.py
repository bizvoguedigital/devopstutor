from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional, List, Dict, Union
from datetime import datetime
from enum import Enum

# Enums
class CareerTrack(str, Enum):
    CLOUD_ENGINEERING = "cloud_engineering"
    DEVOPS_PLATFORM = "devops_platform"
    HYBRID = "hybrid"

class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    EXPERT = "expert"


class CloudPlatform(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

# User Authentication Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    career_track: Optional[CareerTrack] = None
    experience_level: Optional[ExperienceLevel] = None

class UserResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    career_track: Optional[CareerTrack] = None
    experience_level: Optional[ExperienceLevel] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None


class AuthMessage(BaseModel):
    message: str
    token: Optional[str] = None


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

# Learning Path Schemas
class LearningPathResponse(BaseModel):
    id: Optional[str] = None
    path_id: str
    name: str
    description: str
    career_track: CareerTrack
    difficulty_level: ExperienceLevel
    estimated_duration: str
    prerequisites: List[str]
    skills_earned: List[str]
    completion_badge: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class LearningModuleResponse(BaseModel):
    id: Optional[str] = None
    module_id: str
    path_id: str
    name: str
    description: str
    topics: List[str]
    order_index: int
    estimated_time: str
    content: Dict

    model_config = ConfigDict(from_attributes=True)

# Progress Schemas
class UserProgressResponse(BaseModel):
    id: Optional[str] = None
    user_id: str
    path_id: str
    current_module_id: Optional[str] = None
    completed_modules: List[str]
    overall_progress: float
    started_at: datetime
    last_accessed: datetime
    estimated_completion: Optional[datetime] = None
    is_completed: bool
    completion_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ProgressUpdate(BaseModel):
    module_id: str
    progress_percentage: Optional[float] = None
    time_spent_minutes: Optional[int] = None
    questions_attempted: Optional[int] = None
    questions_correct: Optional[int] = None

# Enhanced Session Schemas
class SessionCreate(BaseModel):
    platform: str = Field(..., description="aws, azure, gcp, or devops")
    difficulty: str = Field(..., description="junior, mid, or senior")
    career_track: Optional[CareerTrack] = None
    module_id: Optional[str] = None

class SessionResponse(BaseModel):
    session_id: str
    platform: str
    difficulty: str
    career_track: Optional[CareerTrack] = None
    module_id: Optional[str] = None
    started_at: datetime
    status: str
    user_id: Optional[str] = None

class QuestionRequest(BaseModel):
    session_id: str
    category: Optional[str] = "general"

class QuestionResponse(BaseModel):
    question: str
    question_number: int
    category: str

class AnswerSubmit(BaseModel):
    session_id: str
    question_id: int
    answer_text: str
    audio_path: Optional[str] = None

class AnswerEvaluation(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    score: float
    feedback: str
    model_answer: str
    learning_opportunities: str
    best_practices: str
    real_world_insights: str
    
    # Legacy fields for backward compatibility
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    overall: Optional[str] = None
    
    follow_up_question: Optional[str] = None

# User Statistics Schemas
class UserStatsResponse(BaseModel):
    total_sessions: int
    total_time_minutes: int
    average_session_score: float
    current_streak: int
    longest_streak: int
    paths_completed: int
    modules_completed: int
    achievements_earned: int
    last_activity: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class InterviewHistoryItem(BaseModel):
    session_id: str
    platform: str
    difficulty: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    score: Optional[float] = None
    status: str


class AnalyticsDimension(BaseModel):
    name: str
    score: float
    benchmark: float
    status: str


class PlatformAnalyticsItem(BaseModel):
    platform: str
    sessions: int
    average_score: float


class InterviewAnalyticsResponse(BaseModel):
    completed_sessions: int
    total_answered_questions: int
    interview_readiness: float
    technical_accuracy: AnalyticsDimension
    communication_effectiveness: AnalyticsDimension
    benchmark_percentile: float
    strengths: List[str]
    improvement_areas: List[str]
    platform_breakdown: List[PlatformAnalyticsItem]
    last_updated: datetime


# Dashboard and Analytics
class UserDashboard(BaseModel):
    user: UserResponse
    stats: UserStatsResponse
    active_paths: List[UserProgressResponse]
    recommended_paths: List[LearningPathResponse]
    recent_sessions: List[SessionResponse]
    interview_history: List[InterviewHistoryItem]

class TranscriptionResponse(BaseModel):
    text: str
    duration: Optional[float] = None


class TtsVoice(BaseModel):
    voice_id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)


class TtsStatusResponse(BaseModel):
    available: bool
    provider: str
    provider_configured: bool = False
    availability_reason: Optional[str] = None
    default_voice_id: Optional[str] = None
    model_id: Optional[str] = None

    model_config = ConfigDict(protected_namespaces=())


class TtsSynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    stability: Optional[float] = None
    similarity_boost: Optional[float] = None


class TtsCacheStatsResponse(BaseModel):
    enabled: bool
    ttl_seconds: int
    max_files: int
    file_count: int
    size_bytes: int
    hits: int
    misses: int
    writes: int
    evictions: int
    hit_rate: float


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_sessions: int
    completed_sessions: int
    tts_cache: TtsCacheStatsResponse


class AdminConfigResponse(BaseModel):
    tts_default_voice_id: str
    tts_model_id: str
    tts_stability: float
    tts_similarity: float
    tts_cache_enabled: bool
    tts_cache_ttl_seconds: int
    tts_cache_max_files: int
    max_question_count: int
    session_timeout: int


class AdminConfigUpdateRequest(BaseModel):
    tts_default_voice_id: Optional[str] = None
    tts_model_id: Optional[str] = None
    tts_stability: Optional[float] = None
    tts_similarity: Optional[float] = None
    tts_cache_enabled: Optional[bool] = None
    tts_cache_ttl_seconds: Optional[int] = None
    tts_cache_max_files: Optional[int] = None
    max_question_count: Optional[int] = None
    session_timeout: Optional[int] = None


class AdminTtsProviderStatusResponse(BaseModel):
    available: bool
    provider: str
    provider_configured: bool
    availability_reason: Optional[str] = None
    default_voice_id: Optional[str] = None
    model_id: Optional[str] = None


class AdminTtsTestRequest(BaseModel):
    text: Optional[str] = None
    voice_id: Optional[str] = None


class AdminTtsTestResponse(BaseModel):
    success: bool
    provider: str
    availability_reason: Optional[str] = None
    message: str
    generated_bytes: int = 0


class JourneyContentSyncRequest(BaseModel):
    cloud_provider: Optional[CloudPlatform] = None
    experience_level: Optional[ExperienceLevel] = None
    force_refresh: bool = False


class JourneyContentSyncResponse(BaseModel):
    synced_modules: int
    reused_modules: int
    failed_modules: int
    provider_scope: List[str]
    level_scope: List[str]
    errors: List[str] = Field(default_factory=list)


class JourneyContentSyncJobStartResponse(BaseModel):
    run_id: str
    status: str
    provider_scope: List[str]
    level_scope: List[str]
    force_refresh: bool
    started_at: datetime


class JourneyContentSyncStatusResponse(BaseModel):
    run_id: Optional[str] = None
    status: str
    is_running: bool
    provider_scope: List[str] = Field(default_factory=list)
    level_scope: List[str] = Field(default_factory=list)
    force_refresh: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    synced_modules: int = 0
    reused_modules: int = 0
    failed_modules: int = 0
    errors: List[str] = Field(default_factory=list)


class VoiceRuntimeStatusResponse(BaseModel):
    enabled: bool
    provider: str
    configured: bool
    livekit_url: Optional[str] = None


class VoiceSessionTokenRequest(BaseModel):
    session_id: str = Field(..., min_length=3, max_length=128)
    room_name: Optional[str] = Field(default=None, min_length=3, max_length=128)


class VoiceSessionTokenResponse(BaseModel):
    provider: str
    room_name: str
    identity: str
    token: str
    expires_in: int
    livekit_url: str


class InterviewerV2CvUploadResponse(BaseModel):
    document_id: str
    filename: str
    content_type: Optional[str] = None
    extracted_skills: List[str] = Field(default_factory=list)
    cloud_native_focus_score: float = 0.0
    created_at: datetime


class InterviewerV2JobDescriptionUploadResponse(BaseModel):
    document_id: str
    filename: str
    content_type: Optional[str] = None
    inferred_role: Optional[str] = None
    inferred_seniority: Optional[str] = None
    must_have_skills: List[str] = Field(default_factory=list)
    cloud_native_focus_score: float = 0.0
    created_at: datetime


class InterviewerV2BlueprintGenerateRequest(BaseModel):
    cv_document_id: str = Field(..., min_length=6, max_length=128)
    jd_document_id: str = Field(..., min_length=6, max_length=128)
    target_duration_minutes: int = Field(default=30, ge=15, le=90)
    strict_mode: bool = True


class InterviewerV2QuestionPlanItem(BaseModel):
    competency: str
    question: str
    expected_signals: List[str] = Field(default_factory=list)


class InterviewerV2BlueprintResponse(BaseModel):
    blueprint_id: str
    user_id: str
    cv_document_id: str
    jd_document_id: str
    target_duration_minutes: int
    strict_mode: bool
    delivery_mode: str
    competencies: List[str] = Field(default_factory=list)
    question_plan: List[InterviewerV2QuestionPlanItem] = Field(default_factory=list)
    created_at: datetime


class InterviewerV2SessionStartRequest(BaseModel):
    blueprint_id: str = Field(..., min_length=6, max_length=128)


class InterviewerV2SessionStartResponse(BaseModel):
    session_id: str
    blueprint_id: str
    status: str
    strict_mode: bool
    current_turn: int
    total_turns: int
    current_question: Optional[str] = None
    started_at: datetime


class InterviewerV2SessionTurnRequest(BaseModel):
    user_response: str = Field(..., min_length=1, max_length=4000)

    @field_validator("user_response")
    @classmethod
    def validate_user_response(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("user_response cannot be empty")
        return cleaned


class InterviewerV2EvidenceRef(BaseModel):
    signal: str
    source: str
    snippet: str


class InterviewerV2CompetencyCoverage(BaseModel):
    competency: str
    expected_signals: List[str] = Field(default_factory=list)
    covered_signals: List[str] = Field(default_factory=list)
    missed_signals: List[str] = Field(default_factory=list)
    coverage_ratio: float = 0.0
    answered_turns: int = 0
    average_score: float = 0.0


class InterviewerV2SessionTurnResponse(BaseModel):
    session_id: str
    status: str
    turn_number: int
    refusal: bool = False
    refusal_reason: Optional[str] = None
    assistant_message: str
    score: Optional[float] = None
    feedback: Optional[str] = None
    next_question: Optional[str] = None
    evidence_refs: List[InterviewerV2EvidenceRef] = Field(default_factory=list)
    completed: bool = False


class InterviewerV2SessionStatusResponse(BaseModel):
    session_id: str
    blueprint_id: str
    status: str
    strict_mode: bool
    current_turn: int
    total_turns: int
    current_question: Optional[str] = None
    started_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    recent_evidence_refs: List[InterviewerV2EvidenceRef] = Field(default_factory=list)
    competency_coverage: List[InterviewerV2CompetencyCoverage] = Field(default_factory=list)
    overall_signal_coverage_ratio: float = 0.0


class InterviewerV2TurnReview(BaseModel):
    turn_number: int
    competency: str
    question: str
    user_response: str
    score: float = 0.0
    feedback: str = ""
    model_answer: str = ""


class InterviewerV2SessionCompleteResponse(BaseModel):
    session_id: str
    blueprint_id: str
    session_artifact_id: str
    status: str
    turns_answered: int
    average_score: float
    completed_at: datetime
    summary: str
    evidence_refs: List[InterviewerV2EvidenceRef] = Field(default_factory=list)
    competency_coverage: List[InterviewerV2CompetencyCoverage] = Field(default_factory=list)
    overall_signal_coverage_ratio: float = 0.0
    interview_readiness_score: float = 0.0
    readiness_band: str = "emerging"
    top_strengths: List[str] = Field(default_factory=list)
    improvement_focus: List[str] = Field(default_factory=list)
    turn_reviews: List[InterviewerV2TurnReview] = Field(default_factory=list)


class InterviewerV2SessionArtifactResponse(BaseModel):
    session_artifact_id: str
    session_id: str
    blueprint_id: str
    status: str
    turns_answered: int
    average_score: float
    overall_signal_coverage_ratio: float = 0.0
    interview_readiness_score: float = 0.0
    readiness_band: str = "emerging"
    top_strengths: List[str] = Field(default_factory=list)
    improvement_focus: List[str] = Field(default_factory=list)
    competency_coverage: List[InterviewerV2CompetencyCoverage] = Field(default_factory=list)
    created_at: datetime


class InterviewerV2SessionArtifactListResponse(BaseModel):
    items: List[InterviewerV2SessionArtifactResponse] = Field(default_factory=list)
    total: int = 0
    limit: int = 20
    offset: int = 0
    has_more: bool = False
    status_filter: Optional[str] = None
    readiness_band_filter: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class InterviewerV2ArtifactDeleteResponse(BaseModel):
    session_artifact_id: str
    deleted: bool
    message: str


class InterviewerV2ArtifactCleanupRequest(BaseModel):
    keep_latest: int = Field(10, ge=0, le=1000)
    dry_run: bool = False


class InterviewerV2ArtifactCleanupResponse(BaseModel):
    total_before: int
    keep_latest: int
    dry_run: bool
    removed_count: int
    kept_count: int
    removed_artifact_ids: List[str] = Field(default_factory=list)

class SessionSummary(BaseModel):
    session_id: str
    overall_score: float
    strengths: List[str]
    improvements: List[str]
    study_topics: List[str]
    readiness: str

# AWS Study Mode Schemas
class AwsStudyRequest(BaseModel):
    service_name: str = Field(..., description="AWS service to learn about")

class AwsStudyResponse(BaseModel):
    service_name: str
    category: str
    description: str
    use_cases: str
    implementation: str
    best_practices: Optional[str] = None
    related_services: Optional[List[str]] = None

# Journey and Roadmap Schemas
class CareerJourneyRequest(BaseModel):
    career_track: CareerTrack
    experience_level: ExperienceLevel
    cloud_provider: Optional[CloudPlatform] = None
    preferred_platforms: List[str] = []
    learning_goals: List[str] = []

class CareerJourneyResponse(BaseModel):
    recommended_paths: List[LearningPathResponse]
    skill_roadmap: Dict[str, List[str]]
    estimated_timeline: str
    next_steps: List[str]
    selected_platform: Optional[CloudPlatform] = None

class JourneyHandsOn(BaseModel):
    scenario: str
    tasks: List[str]
    validation: Optional[List[str]] = None

class JourneyMcq(BaseModel):
    question: str
    options: List[str]
    correct_option: str
    explanation: str

class JourneyModuleAssessment(BaseModel):
    scenario: str
    tasks: List[str]
    validation: Optional[List[str]] = None
    mcqs: List[JourneyMcq]

class JourneyTopicContent(BaseModel):
    topic_id: str
    title: str
    teaching: str
    lesson_content: str = ""
    key_points: List[str]
    steps: List[str]
    hands_on: JourneyHandsOn
    mcq: JourneyMcq
    source_urls: List[str] = Field(default_factory=list)

class JourneyModuleDetail(BaseModel):
    module_id: str
    name: str
    description: str
    order_index: int
    estimated_time: str
    topics: List[JourneyTopicContent]
    assessment: Optional[JourneyModuleAssessment] = None

class JourneyPathDetail(BaseModel):
    path_id: str
    name: str
    description: str
    career_track: CareerTrack
    difficulty_level: ExperienceLevel
    selected_platform: Optional[CloudPlatform] = None
    estimated_duration: str
    skills_earned: List[str]

class TopicProgressResponse(BaseModel):
    module_id: str
    topic_id: str
    scenario_completed: bool
    mcq_correct: bool
    mcq_attempts: int
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_spent_minutes: int = 0
    last_updated: datetime

class ModuleProgressSummary(BaseModel):
    module_id: str
    progress_percentage: float
    completed_topics: int
    total_topics: int
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None

class ModuleAssessmentProgressResponse(BaseModel):
    module_id: str
    scenario_completed: bool
    mcq_attempts: int
    mcq_correct: int
    is_completed: bool
    last_updated: datetime

class JourneyPlanResponse(BaseModel):
    path: JourneyPathDetail
    modules: List[JourneyModuleDetail]
    topic_progress: List[TopicProgressResponse]
    module_progress: List[ModuleProgressSummary]
    module_assessment_progress: List[ModuleAssessmentProgressResponse]
    overall_progress: float

class TopicProgressUpdate(BaseModel):
    module_id: str
    topic_id: str
    scenario_completed: Optional[bool] = None
    mcq_answer: Optional[str] = None
    time_spent_minutes: Optional[int] = Field(default=None, ge=0)

class ModuleAssessmentUpdate(BaseModel):
    module_id: str
    scenario_completed: Optional[bool] = None
    mcq_index: Optional[int] = None
    mcq_answer: Optional[str] = None

class ModuleAssessmentReset(BaseModel):
    module_id: str

class HealthCheck(BaseModel):
    status: str
    llm_connected: bool
    model: str
    whisper_available: bool
    whisper_model: Optional[str] = None

# Certification Exam Schemas
class ExamStartRequest(BaseModel):
    certificate: str = Field(..., description="AWS Cloud Practitioner, etc")
    question_count: int = Field(10, ge=5, le=100)

class ExamQuestion(BaseModel):
    id: Optional[str] = None
    question_number: int
    prompt: str
    options: List[str]
    category: Optional[str] = None

class ExamSessionResponse(BaseModel):
    exam_id: str
    certificate: str
    question_count: int
    duration_minutes: int
    started_at: datetime
    remaining_seconds: Optional[int] = None
    current_index: int = 0
    answers: Dict[str, str] = Field(default_factory=dict)
    flagged: Dict[str, bool] = Field(default_factory=dict)
    is_resumed: bool = False
    questions: List[ExamQuestion]

class ExamAnswerSubmission(BaseModel):
    question_id: Optional[Union[str, int]] = None
    selected_option: Optional[str] = ""

class ExamSubmitRequest(BaseModel):
    exam_id: str
    answers: List[ExamAnswerSubmission]


class ExamProgressUpdateRequest(BaseModel):
    answers: Dict[str, str] = Field(default_factory=dict)
    flagged: Dict[str, bool] = Field(default_factory=dict)
    current_index: int = Field(0, ge=0)
    remaining_seconds: Optional[int] = Field(default=None, ge=0)

class ExamAnswerReview(BaseModel):
    question_id: str
    question_number: int
    prompt: str
    options: List[str]
    category: Optional[str] = None
    selected_option: str
    correct_option: str
    is_correct: bool
    explanation: str


class ExamCategoryBreakdown(BaseModel):
    category: str
    total: int
    correct: int
    accuracy: float

class ExamResultResponse(BaseModel):
    exam_id: str
    certificate: str
    total_questions: int
    correct_count: int
    unanswered_count: int
    score_percent: float
    pass_mark: float
    passed: bool
    category_breakdown: List[ExamCategoryBreakdown]
    recommendations: List[str]
    review: List[ExamAnswerReview]
