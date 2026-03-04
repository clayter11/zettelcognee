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

    # Cognee / LLM — Anthropic Claude
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-20250514"
    llm_api_key: str = ""

    # Embeddings — fastembed (local, no API key)
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_api_key: str = ""

    # Anthropic API key (used for both Cognee LLM and direct generation)
    anthropic_api_key: str = ""

    # Auth
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
