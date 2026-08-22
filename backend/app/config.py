from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://inboxpilot:inboxpilot@db:5432/inboxpilot"
    # Postgres schema to operate in. Lets one physical database (e.g. one
    # Supabase project) cleanly separate local dev from production without
    # touching any model or migration file - everything resolves through
    # Postgres's own search_path. Leave as "public" in production.
    db_schema: str = "public"

    # JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # AI providers (set whichever you have; Anthropic takes precedence if both are set)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Frontend URL (for CORS)
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        # backend/.env is often a straight copy of the repo-root .env, which
        # also carries frontend-only vars like NEXT_PUBLIC_API_URL - ignore
        # anything this Settings class doesn't declare instead of erroring.
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
