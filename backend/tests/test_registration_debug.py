import pytest
from httpx import AsyncClient


class TestRegistrationDebugging:
    """Debug registration issues"""

    @pytest.mark.asyncio
    async def test_registration_debug_detailed_error(self, client: AsyncClient, sample_user_data):
        """Test registration and capture the exact error."""

        response = await client.post("/api/auth/register", json=sample_user_data)

        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Content: {response.text}")
        print(f"JSON: {response.json() if response.headers.get('content-type', '').startswith('application/json') else 'Not JSON'}")
        print(f"Request data: {sample_user_data}")

        assert response.status_code == 200

    @pytest.mark.asyncio  
    async def test_direct_auth_service_call(self, test_db, sample_user_data):
        """Test calling auth service directly."""
        from services.async_auth_service import async_auth_service
        from schemas import UserCreate

        user_data = UserCreate(**sample_user_data)
        result = await async_auth_service.register_user(test_db, user_data)
        assert result is not None