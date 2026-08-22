from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# When db_schema isn't "public" (e.g. local dev sharing a Supabase project
# with production), point every unqualified table reference - migrations
# included - at that schema via search_path, instead of qualifying every
# model/migration individually.
_connect_args = (
    {"server_settings": {"search_path": settings.db_schema}}
    if settings.db_schema != "public"
    else {}
)

engine = create_async_engine(settings.database_url, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
