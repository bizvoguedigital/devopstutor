import pytest
import pytest_asyncio
from httpx import AsyncClient
from mongomock_motor import AsyncMongoMockClient
import os
from typing import AsyncGenerator

# Import application components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import get_db
from config import settings


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator:
    """Create a fresh MongoDB database for each test."""
    client = AsyncMongoMockClient()
    db = client[settings.MONGODB_DB_NAME]
    yield db
    await client.drop_database(settings.MONGODB_DB_NAME)


@pytest_asyncio.fixture
async def client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with dependency override."""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }


@pytest.fixture
def sample_user_data_2():
    """Second sample user for testing conflicts"""
    return {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpass456",
        "full_name": "Test User 2"
    }


@pytest.fixture
def sample_login_data():
    """Sample login data"""
    return {
        "email": "test@example.com",
        "password": "testpass123"
    }