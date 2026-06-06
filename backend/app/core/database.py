"""PostgreSQL + SQLModel async database layer with Neon resilience."""
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlencode
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlmodel import SQLModel
import ssl
from app.core.config import get_settings

settings = get_settings()

# Parse and fix for asyncpg compatibility (Neon uses sslmode which asyncpg doesn't understand)
parsed = urlparse(settings.database_url)
query_params = parse_qs(parsed.query)

# Extract sslmode if present
ssl_mode = query_params.pop("sslmode", [None])[0]
query_params.pop("channel_binding", [None])

# Rebuild query string without asyncpg-incompatible params
# Use urlencode to properly handle multi-value params and special chars
new_query = urlencode(query_params, doseq=True) if query_params else ""

# For file-based URLs (sqlite), netloc is empty and geturl() drops slashes.
# Only reconstruct if we actually modified the query or if netloc exists.
if parsed.netloc or new_query:
    clean_url = parsed._replace(query=new_query).geturl()
else:
    # File-based URL — preserve original to avoid slash mangling
    clean_url = settings.database_url

# SSL config for asyncpg — proper TLS context with hostname verification
connect_args = {
    "timeout": settings.db_connect_timeout,
    "command_timeout": settings.db_command_timeout,
}
if ssl_mode == "require" or (parsed.hostname and ".neon.tech" in parsed.hostname):
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = True
    ssl_ctx.load_default_certs()
    connect_args["ssl"] = ssl_ctx

engine = create_async_engine(
    clean_url,
    echo=False,
    future=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,
    pool_recycle=settings.db_pool_recycle,
    pool_timeout=settings.db_pool_timeout,
    connect_args=connect_args,
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db() -> None:
    """Create all tables. Call once at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def health_check() -> bool:
    """Ping the database. Returns True if reachable."""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False
