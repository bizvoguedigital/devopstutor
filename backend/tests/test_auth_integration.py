import pytest
import pytest_asyncio
from httpx import AsyncClient


class TestAuthEndpoints:
    """Integration tests for authentication endpoints"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health endpoint works"""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_user_registration_success(self, client: AsyncClient, sample_user_data):
        """Test successful user registration"""
        response = await client.post("/api/auth/register", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_user_registration_duplicate_email(self, client: AsyncClient, sample_user_data):
        """Test registration with duplicate email"""
        # Try to register the same user twice
        response1 = await client.post("/api/auth/register", json=sample_user_data)
        response2 = await client.post("/api/auth/register", json=sample_user_data)

        assert response1.status_code == 200
        assert response2.status_code == 400

    @pytest.mark.asyncio
    async def test_user_registration_invalid_data(self, client: AsyncClient):
        """Test registration with invalid data"""
        invalid_data = {
            "username": "",  # Empty username
            "email": "not-an-email",  # Invalid email
            "password": "123",  # Too short password
            "full_name": ""
        }
        
        response = await client.post("/api/auth/register", json=invalid_data)
        print(f"Invalid data response: {response.status_code}")
        print(f"Invalid data response text: {response.text}")
        
        # Should return validation error
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_user_login(self, client: AsyncClient, sample_user_data):
        """Test user login"""
        # First, try to register (may fail)
        registration_response = await client.post("/api/auth/register", json=sample_user_data)

        assert registration_response.status_code == 200
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token"""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_valid_token(self, client: AsyncClient, sample_user_data):
        """Test accessing protected endpoint with valid token"""
        # First register user (may fail due to async issue)
        registration_response = await client.post("/api/auth/register", json=sample_user_data)

        assert registration_response.status_code == 200
        response = await client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]

    @pytest.mark.asyncio
    async def test_refresh_and_logout(self, client: AsyncClient, sample_user_data):
        """Test refresh token rotation and logout"""
        registration_response = await client.post("/api/auth/register", json=sample_user_data)
        assert registration_response.status_code == 200

        refresh_response = await client.post("/api/auth/refresh")
        assert refresh_response.status_code == 200
        assert "access_token" in refresh_response.json()

        logout_response = await client.post("/api/auth/logout")
        assert logout_response.status_code == 200

        me_response = await client.get("/api/auth/me")
        assert me_response.status_code == 401


class TestApiErrorHandling:
    """Test API error handling"""

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, client: AsyncClient):
        """Test invalid endpoint returns 404"""
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_method(self, client: AsyncClient):
        """Test invalid HTTP method"""
        response = await client.delete("/api/auth/register")
        assert response.status_code == 405

    @pytest.mark.asyncio
    async def test_missing_request_body(self, client: AsyncClient):
        """Test missing request body"""
        response = await client.post("/api/auth/register")
        assert response.status_code in [400, 422]