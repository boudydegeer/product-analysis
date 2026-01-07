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

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_analysis"

    # GitHub
    github_token: str = "placeholder"
    github_repo: str = "boudydegeer/product-analysis"

    # Security
    secret_key: str = "change-this-in-production"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",  # Vite dev server (default)
        "http://localhost:5174",  # Vite fallback port
        "http://localhost:5175",  # Vite fallback port
        "http://localhost:5176",  # Vite fallback port
        "http://localhost:3000",  # Alternative port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
