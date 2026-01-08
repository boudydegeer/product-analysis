"""Tests for configuration settings."""
from app.config import Settings


class TestWebhookConfig:
    """Tests for webhook configuration."""

    def test_webhook_secret_is_configurable(self):
        """Webhook secret should be configurable via env var."""
        settings = Settings(webhook_secret="test-secret-123")
        assert settings.webhook_secret == "test-secret-123"

    def test_webhook_base_url_is_configurable(self):
        """Webhook base URL should be configurable for different environments."""
        settings = Settings(webhook_base_url="https://api.example.com")
        assert settings.webhook_base_url == "https://api.example.com"

    def test_webhook_base_url_defaults_to_none_for_localhost(self):
        """Webhook base URL should default to None for localhost development."""
        settings = Settings()
        assert settings.webhook_base_url is None


class TestPollingConfig:
    """Tests for polling configuration."""

    def test_polling_interval_is_configurable(self):
        """Polling interval should be configurable."""
        settings = Settings(analysis_polling_interval_seconds=60)
        assert settings.analysis_polling_interval_seconds == 60

    def test_polling_interval_has_default(self):
        """Polling interval should have a sensible default."""
        settings = Settings()
        assert settings.analysis_polling_interval_seconds == 30

    def test_polling_timeout_is_configurable(self):
        """Polling timeout should be configurable."""
        settings = Settings(analysis_polling_timeout_seconds=1800)
        assert settings.analysis_polling_timeout_seconds == 1800

    def test_polling_timeout_has_default(self):
        """Polling timeout should have default of 15 minutes."""
        settings = Settings()
        assert settings.analysis_polling_timeout_seconds == 900  # 15 minutes
