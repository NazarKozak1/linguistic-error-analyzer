from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# resolve() gets absolute path, parents[2] goes up 3 levels to project root
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

# create directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# construct db url
DB_PATH = f"sqlite+aiosqlite:///{DATA_DIR / 'database.db'}"

# initialize async engine
engine = create_async_engine(DB_PATH, echo=False)

# create session factory for database operations
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def get_db():
    """dependency for getting db session."""
    async with AsyncSessionLocal() as session:
        yield session