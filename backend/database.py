from typing import AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


def _get_client() -> AsyncIOMotorClient:
    global _client, _database
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
        _database = _client[settings.MONGODB_DB_NAME]
    return _client


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        _get_client()
    return _database


async def init_db() -> None:
    db = get_database()

    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)

    await db.refresh_tokens.create_index("jti", unique=True)
    await db.refresh_tokens.create_index("token_hash")
    await db.email_verification_tokens.create_index("token_hash")
    await db.password_reset_tokens.create_index("token_hash")

    await db.interview_sessions.create_index("session_id", unique=True)
    await db.question_responses.create_index([("session_id", 1), ("question_number", 1)])

    await db.exam_sessions.create_index("exam_id", unique=True)
    await db.exam_questions.create_index("exam_id")
    await db.exam_answers.create_index("exam_id")

    await db.learning_paths.create_index("path_id", unique=True)
    await db.learning_modules.create_index("module_id", unique=True)
    await db.learning_modules.create_index([("path_id", 1), ("order_index", 1)])
    await db.user_progress.create_index([("user_id", 1), ("path_id", 1)], unique=True)
    await db.module_progress.create_index([("user_id", 1), ("module_id", 1)], unique=True)
    await db.topic_progress.create_index([("user_id", 1), ("module_id", 1), ("topic_id", 1)], unique=True)
    await db.module_assessment_progress.create_index([("user_id", 1), ("module_id", 1)], unique=True)
    await db.learning_content_cache.create_index(
        [("provider", 1), ("experience_level", 1), ("module_id", 1)],
        unique=True,
    )
    await db.learning_content_cache.create_index("updated_at")
    await db.learning_content_sync_runs.create_index("run_id", unique=True)
    await db.learning_content_sync_runs.create_index([("started_at", -1)])


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield get_database()
