import pytest
import pytest_asyncio
from datetime import timedelta

from services.async_auth_service import async_auth_service
from schemas import UserCreate


class TestAsyncAuthService:
    """Unit tests for AsyncAuthService"""

    def test_password_hashing(self):
        password = "test_password_123"
        hashed = async_auth_service.get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert async_auth_service.verify_password(password, hashed) is True
        assert async_auth_service.verify_password("wrong_password", hashed) is False

    def test_jwt_token_creation_and_verification(self):
        token, jti, _expires_at = async_auth_service.create_access_token("testuser", "123")
        assert token
        payload = async_auth_service.verify_token(token)
        assert payload["sub"] == "testuser"
        assert payload["user_id"] == "123"
        assert payload["jti"] == jti

        invalid_payload = async_auth_service.verify_token("invalid_token")
        assert invalid_payload is None

    @pytest_asyncio.fixture
    async def test_user_in_db(self, test_db):
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            full_name="Test User"
        )
        user = await async_auth_service.create_user(test_db, user_data)
        return user

    @pytest.mark.asyncio
    async def test_register_and_login_user_async(self, test_db, sample_user_data):
        user_data = UserCreate(**sample_user_data)
        token_response, refresh_token, expires_in = await async_auth_service.register_user(test_db, user_data)
        assert token_response.access_token
        assert refresh_token
        assert expires_in > 0

    @pytest.mark.asyncio
    async def test_authenticate_user_async(self, test_db, test_user_in_db):
        user = await async_auth_service.authenticate_user(test_db, "test@example.com", "testpass123")
        assert user is not None