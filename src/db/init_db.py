# Ensure all models are imported so Base.metadata knows about them
import src.models.lap  # noqa: F401
import src.models.session  # noqa: F401
import src.models.setup  # noqa: F401
import src.models.telemetry  # noqa: F401
from src.db.engine import engine
from src.models.base import Base


async def init_db() -> None:
    """Create all tables. Called on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
