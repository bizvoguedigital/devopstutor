from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import hashlib
import hmac
import secrets
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase

from config import settings
from schemas import UserCreate, UserLogin, Token, UserResponse

ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS

pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto"
)


class AsyncAuthService:
    """Async-compatible authentication service for MongoDB."""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def _hash_token(self, token: str) -> str:
        key = settings.JWT_SECRET_KEY.encode("utf-8")
        return hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()

    def _ensure_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _build_token(
        self,
        subject: str,
        user_id: str,
        token_type: str,
        expires_delta: timedelta,
    ) -> Tuple[str, str, datetime]:
        now = datetime.now(timezone.utc)
        jti = str(uuid.uuid4())
        expires_at = now + expires_delta
        payload = {
            "sub": subject,
            "user_id": user_id,
            "type": token_type,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": expires_at,
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
        }
        encoded = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
        return encoded, jti, expires_at

    def create_access_token(self, subject: str, user_id: str) -> Tuple[str, str, datetime]:
        return self._build_token(
            subject=subject,
            user_id=user_id,
            token_type="access",
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    def create_refresh_token(self, subject: str, user_id: str) -> Tuple[str, str, datetime]:
        return self._build_token(
            subject=subject,
            user_id=user_id,
            token_type="refresh",
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )

    def verify_token(self, token: str, expected_type: str = "access") -> Optional[dict]:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
        except JWTError:
            return None

        if payload.get("type") != expected_type:
            return None
        if not payload.get("sub") or not payload.get("user_id"):
            return None
        return payload

    def _user_response(self, user: dict) -> UserResponse:
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

    async def get_user_by_email(self, db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
        return await db.users.find_one({"email": email})

    async def get_user_by_username(self, db: AsyncIOMotorDatabase, username: str) -> Optional[dict]:
        return await db.users.find_one({"username": username})

    async def get_user_by_id(self, db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
        return await db.users.find_one({"user_id": user_id})

    async def create_user(self, db: AsyncIOMotorDatabase, user_data: UserCreate) -> dict:
        existing_email = await self.get_user_by_email(db, user_data.email)
        if existing_email:
            raise ValueError("Email already registered")

        existing_username = await self.get_user_by_username(db, user_data.username)
        if existing_username:
            raise ValueError("Username already taken")

        hashed_password = self.get_password_hash(user_data.password)
        existing_user_count = await db.users.count_documents({})
        doc = {
            "user_id": str(uuid.uuid4()),
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "hashed_password": hashed_password,
            "career_track": None,
            "experience_level": None,
            "profile_picture": None,
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "is_active": True,
            "email_verified": False,
            "is_admin": existing_user_count == 0,
        }

        result = await db.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def authenticate_user(self, db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[dict]:
        user = await self.get_user_by_email(db, email)
        if not user:
            return None
        if not self.verify_password(password, user.get("hashed_password", "")):
            return None
        return user

    async def authenticate_user_by_username(
        self,
        db: AsyncIOMotorDatabase,
        username: str,
        password: str,
    ) -> Optional[dict]:
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        if not self.verify_password(password, user.get("hashed_password", "")):
            return None
        return user

    async def register_user(self, db: AsyncIOMotorDatabase, user_data: UserCreate) -> Tuple[Token, str, int]:
        user = await self.create_user(db, user_data)
        access_token, refresh_token, expires_in = await self._issue_tokens(db, user)
        return access_token, refresh_token, expires_in

    async def login_user(self, db: AsyncIOMotorDatabase, login_data: UserLogin) -> Tuple[Token, str, int]:
        user = await self.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            user = await self.authenticate_user_by_username(db, login_data.email, login_data.password)

        if not user:
            raise ValueError("Invalid credentials")
        if not user.get("is_active", True):
            raise ValueError("User account is disabled")

        access_token, refresh_token, expires_in = await self._issue_tokens(db, user)
        return access_token, refresh_token, expires_in

    async def _issue_tokens(
        self,
        db: AsyncIOMotorDatabase,
        user: dict,
        rotated_from_jti: Optional[str] = None,
    ) -> Tuple[Token, str, int]:
        access_token_value, _access_jti, access_expires_at = self.create_access_token(
            subject=user.get("username"),
            user_id=user.get("user_id"),
        )
        refresh_token_value, refresh_jti, refresh_expires_at = self.create_refresh_token(
            subject=user.get("username"),
            user_id=user.get("user_id"),
        )

        refresh_record = {
            "user_id": user.get("user_id"),
            "token_hash": self._hash_token(refresh_token_value),
            "jti": refresh_jti,
            "created_at": datetime.now(timezone.utc),
            "expires_at": refresh_expires_at,
            "revoked_at": None,
            "rotated_from_jti": rotated_from_jti,
        }
        await db.refresh_tokens.insert_one(refresh_record)

        now = datetime.now(timezone.utc)
        await db.users.update_one(
            {"user_id": user.get("user_id")},
            {"$set": {"last_login": now}},
        )
        user["last_login"] = now

        token_response = Token(
            access_token=access_token_value,
            token_type="bearer",
            expires_in=int((access_expires_at - datetime.now(timezone.utc)).total_seconds()),
            user=self._user_response(user),
        )

        return token_response, refresh_token_value, token_response.expires_in or 0

    async def rotate_refresh_token(
        self,
        db: AsyncIOMotorDatabase,
        refresh_token: str,
    ) -> Tuple[Token, str, int]:
        payload = self.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            raise ValueError("Invalid refresh token")

        jti = payload.get("jti")
        user_id = payload.get("user_id")
        if not jti or not user_id:
            raise ValueError("Invalid refresh token")

        stored = await db.refresh_tokens.find_one({"jti": jti})
        if not stored or stored.get("user_id") != user_id:
            raise ValueError("Refresh token not recognized")

        stored_expires_at = self._ensure_utc(stored.get("expires_at"))
        if stored.get("revoked_at") is not None or stored_expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired")

        if stored.get("token_hash") != self._hash_token(refresh_token):
            raise ValueError("Refresh token mismatch")

        await db.refresh_tokens.update_one(
            {"jti": jti},
            {"$set": {"revoked_at": datetime.now(timezone.utc)}},
        )

        user = await self.get_user_by_id(db, user_id)
        if not user or not user.get("is_active", True):
            raise ValueError("User account is disabled")

        access_token, new_refresh_token, expires_in = await self._issue_tokens(
            db,
            user,
            rotated_from_jti=jti,
        )

        return access_token, new_refresh_token, expires_in

    async def revoke_refresh_token(self, db: AsyncIOMotorDatabase, refresh_token: str) -> None:
        payload = self.verify_token(refresh_token, expected_type="refresh")
        if not payload:
            return
        jti = payload.get("jti")
        if not jti:
            return

        await db.refresh_tokens.update_one(
            {"jti": jti, "revoked_at": None},
            {"$set": {"revoked_at": datetime.now(timezone.utc)}},
        )

    async def create_email_verification_token(self, db: AsyncIOMotorDatabase, user: dict) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
        record = {
            "user_id": user.get("user_id"),
            "token_hash": self._hash_token(token),
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "used_at": None,
        }
        await db.email_verification_tokens.insert_one(record)
        return token

    async def verify_email_token(self, db: AsyncIOMotorDatabase, token: str) -> bool:
        token_hash = self._hash_token(token)
        record = await db.email_verification_tokens.find_one({"token_hash": token_hash})
        if not record or record.get("used_at") is not None:
            return False
        record_expires_at = self._ensure_utc(record.get("expires_at"))
        if record_expires_at < datetime.now(timezone.utc):
            return False

        await db.email_verification_tokens.update_one(
            {"_id": record.get("_id")},
            {"$set": {"used_at": datetime.now(timezone.utc)}},
        )
        await db.users.update_one(
            {"user_id": record.get("user_id")},
            {"$set": {"email_verified": True}},
        )
        return True

    async def create_password_reset_token(self, db: AsyncIOMotorDatabase, user: dict) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        record = {
            "user_id": user.get("user_id"),
            "token_hash": self._hash_token(token),
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "used_at": None,
        }
        await db.password_reset_tokens.insert_one(record)
        return token

    async def reset_password(self, db: AsyncIOMotorDatabase, token: str, new_password: str) -> bool:
        token_hash = self._hash_token(token)
        record = await db.password_reset_tokens.find_one({"token_hash": token_hash})
        if not record or record.get("used_at") is not None:
            return False
        record_expires_at = self._ensure_utc(record.get("expires_at"))
        if record_expires_at < datetime.now(timezone.utc):
            return False

        await db.users.update_one(
            {"user_id": record.get("user_id")},
            {"$set": {"hashed_password": self.get_password_hash(new_password)}},
        )
        await db.password_reset_tokens.update_one(
            {"_id": record.get("_id")},
            {"$set": {"used_at": datetime.now(timezone.utc)}},
        )
        return True


async_auth_service = AsyncAuthService()
