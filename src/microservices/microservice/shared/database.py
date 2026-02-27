import os
import re
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def parse_npgsql_connection_string(npgsql_string: str) -> str:
    """Convert an Npgsql connection string to an asyncpg SQLAlchemy URL.

    Aspire injects: Host=localhost;Port=5432;Database=hackathondb;Username=postgres;Password=...
    We need: postgresql+asyncpg://postgres:...@localhost:5432/hackathondb
    """
    pairs: dict[str, str] = {}
    for part in npgsql_string.split(";"):
        part = part.strip()
        if not part:
            continue
        match = re.match(r"^([^=]+)=(.*)$", part)
        if match:
            pairs[match.group(1).strip().lower()] = match.group(2).strip()

    host = pairs.get("host", "localhost")
    port = pairs.get("port", "5432")
    database = pairs.get("database", "hackathondb")
    username = pairs.get("username", "postgres")
    password = pairs.get("password", "")

    return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"


def get_database_url() -> str:
    """Build the async database URL from environment variables."""
    conn_string = os.environ.get("ConnectionStrings__hackathondb", "")
    if conn_string:
        return parse_npgsql_connection_string(conn_string)

    # Fallback for local dev without Aspire
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/hackathondb",
    )


def init_db() -> None:
    global engine, SessionLocal
    url = get_database_url()
    engine = create_async_engine(url, echo=False, pool_size=5, max_overflow=10)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with SessionLocal() as session:
        yield session
