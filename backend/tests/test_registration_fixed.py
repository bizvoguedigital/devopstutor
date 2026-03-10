import pytest
from httpx import AsyncClient


class TestFixedRegistration:
    """Test fixed registration with proper passwords"""

    @pytest.mark.asyncio
    async def test_registration_success_short_password(self, client: AsyncClient):
        """Test registration with bcrypt-compatible password"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "test12345",  # 9 characters - meets minimum requirement
            "full_name": "Test User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Should work now!
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["username"] == user_data["username"]

    @pytest.mark.asyncio
    async def test_registration_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com", 
            "password": "test12345",  # 9 characters
            "full_name": "Test User"
        }
        
        # First registration should work
        response1 = await client.post("/api/auth/register", json=user_data)
        print(f"First registration: {response1.status_code}")
        
        # Second registration should fail
        user_data2 = {
            "username": "testuser2", 
            "email": "test@example.com",  # Same email
            "password": "test12346",  # 9 characters
            "full_name": "Test User 2"
        }
        
        response2 = await client.post("/api/auth/register", json=user_data2)
        print(f"Second registration: {response2.status_code}")
        print(f"Second response: {response2.text}")
        
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert "Email already registered" in response2.text

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test login after registration"""
        # Register user first
        user_data = {
            "username": "logintest",
            "email": "login@example.com",
            "password": "test12345",  # 9 characters
            "full_name": "Login Test"
        }
        
        reg_response = await client.post("/api/auth/register", json=user_data)
        assert reg_response.status_code == 200
        
        # Now test login
        login_data = {
            "email": "login@example.com",
            "password": "test12345"
        }
        
        login_response = await client.post("/api/auth/login", json=login_data)
        print(f"Login status: {login_response.status_code}")
        print(f"Login response: {login_response.text}")
        
        assert login_response.status_code == 200
        login_data_resp = login_response.json()
        assert "access_token" in login_data_resp

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_auth(self, client: AsyncClient):
        """Test protected endpoint after registration"""
        # Register and get token
        user_data = {
            "username": "protectedtest", 
            "email": "protected@example.com",
            "password": "test12345",  # 9 characters
            "full_name": "Protected Test"
        }
        
        reg_response = await client.post("/api/auth/register", json=user_data)
        assert reg_response.status_code == 200
        
        token = reg_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test protected endpoint
        me_response = await client.get("/api/auth/me", headers=headers)
        print(f"Protected endpoint status: {me_response.status_code}")
        print(f"Protected endpoint response: {me_response.text}")
        
        assert me_response.status_code == 200
        user_info = me_response.json()
        assert user_info["email"] == user_data["email"]