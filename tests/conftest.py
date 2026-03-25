import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.engine import get_db
from src.main import app
from src.models.base import Base

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db() -> AsyncSession:
    async with test_session_factory() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_database():
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_session_data() -> dict:
    return {
        "track_name": "Le Mans 24h Circuit",
        "car_name": "Toyota GR010 Hybrid",
        "driver_name": "Test Driver",
        "session_type": "practice",
    }


@pytest.fixture
def sample_frame_data() -> dict:
    return {
        "timestamp": "2026-03-24T14:30:00Z",
        "lap_number": 3,
        "sector": 2,
        "throttle": 0.85,
        "brake": 0.0,
        "steering": -0.12,
        "gear": 4,
        "speed": 245.6,
        "rpm": 8500.0,
        "position_x": 1234.56,
        "position_y": 12.34,
        "position_z": -567.89,
        "tire_temps": {
            "front_left": 95.2,
            "front_right": 96.1,
            "rear_left": 98.0,
            "rear_right": 97.5,
        },
        "tire_pressures": {
            "front_left": 172.0,
            "front_right": 173.0,
            "rear_left": 165.0,
            "rear_right": 166.0,
        },
        "fuel_level": 42.5,
        "weather_conditions": "dry",
    }
