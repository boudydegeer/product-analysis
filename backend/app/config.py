from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Product Analysis Platform"
    debug: bool = False
    port: int = 8891

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_analysis"

    # GitHub
    github_token: str = "placeholder"
    github_repo: str = "boudydegeer/product-analysis"

    # Security
    secret_key: str = "change-this-in-production"

    # Webhooks
    webhook_secret: str = "change-this-webhook-secret-in-production"
    webhook_base_url: str | None = None  # Set for production, leave None for localhost

    # Analysis Polling
    analysis_polling_interval_seconds: int = 30  # Check every 30 seconds
    analysis_polling_timeout_seconds: int = 900  # Give up after 15 minutes

    # CORS
    cors_origins: list[str] = [
        "http://localhost:8892",  # Frontend dev server (default)
        "http://localhost:5173",  # Vite dev server (fallback)
        "http://localhost:5174",  # Vite fallback port
        "http://localhost:5175",  # Vite fallback port
        "http://localhost:5176",  # Vite fallback port
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:8892",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
