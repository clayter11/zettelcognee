from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "ZettelCognee"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/zettelcognee"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/zettelcognee"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # GCS
    gcs_bucket: str = "zettelcognee-files"
    gcs_credentials_path: str | None = None

    # Cognee / LLM
    llm_provider: str = "gemini"
    llm_model: str = "gemini/gemini-2.0-flash"
    llm_api_key: str = ""

    embedding_provider: str = "gemini"
    embedding_model: str = "models/text-embedding-004"
    embedding_api_key: str = ""

    # Claude (for high-quality generation)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Auth
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
