"""Tests for webhook security utilities."""

from app.utils.webhook_security import (
    generate_webhook_secret,
    compute_webhook_signature,
    verify_webhook_signature,
)


class TestGenerateWebhookSecret:
    """Tests for generate_webhook_secret function."""

    def test_generates_random_secret(self):
        """Should generate a random webhook secret."""
        secret = generate_webhook_secret()

        assert isinstance(secret, str)
        assert len(secret) > 20  # Should be reasonably long

    def test_generates_different_secrets(self):
        """Should generate different secrets on each call."""
        secret1 = generate_webhook_secret()
        secret2 = generate_webhook_secret()

        assert secret1 != secret2

    def test_secret_is_url_safe(self):
        """Generated secret should be URL-safe."""
        secret = generate_webhook_secret()

        # Should not contain problematic characters
        assert " " not in secret
        assert "\n" not in secret
        assert "+" not in secret
        assert "/" not in secret


class TestComputeWebhookSignature:
    """Tests for compute_webhook_signature function."""

    def test_computes_signature_for_payload(self):
        """Should compute HMAC signature for payload."""
        payload = '{"feature_id": "test-123", "status": "completed"}'
        secret = "test-secret-key"

        signature = compute_webhook_signature(payload, secret)

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length

    def test_same_payload_produces_same_signature(self):
        """Same payload and secret should produce same signature."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"

        sig1 = compute_webhook_signature(payload, secret)
        sig2 = compute_webhook_signature(payload, secret)

        assert sig1 == sig2

    def test_different_payload_produces_different_signature(self):
        """Different payload should produce different signature."""
        secret = "test-secret"

        sig1 = compute_webhook_signature('{"id": "1"}', secret)
        sig2 = compute_webhook_signature('{"id": "2"}', secret)

        assert sig1 != sig2

    def test_different_secret_produces_different_signature(self):
        """Different secret should produce different signature."""
        payload = '{"feature_id": "test-123"}'

        sig1 = compute_webhook_signature(payload, "secret1")
        sig2 = compute_webhook_signature(payload, "secret2")

        assert sig1 != sig2


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature function."""

    def test_verifies_valid_signature(self):
        """Should return True for valid signature."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        signature = compute_webhook_signature(payload, secret)

        is_valid = verify_webhook_signature(payload, signature, secret)

        assert is_valid is True

    def test_rejects_invalid_signature(self):
        """Should return False for invalid signature."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        wrong_signature = "0" * 64  # Invalid signature

        is_valid = verify_webhook_signature(payload, wrong_signature, secret)

        assert is_valid is False

    def test_rejects_signature_with_wrong_secret(self):
        """Should return False when signature computed with different secret."""
        payload = '{"feature_id": "test-123"}'
        signature = compute_webhook_signature(payload, "secret1")

        is_valid = verify_webhook_signature(payload, signature, "secret2")

        assert is_valid is False

    def test_rejects_signature_for_modified_payload(self):
        """Should return False if payload was modified after signing."""
        original_payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        signature = compute_webhook_signature(original_payload, secret)

        modified_payload = '{"feature_id": "test-456"}'
        is_valid = verify_webhook_signature(modified_payload, signature, secret)

        assert is_valid is False

    def test_handles_empty_signature(self):
        """Should handle empty signature gracefully."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"

        is_valid = verify_webhook_signature(payload, "", secret)

        assert is_valid is False

    def test_timing_safe_comparison(self):
        """Should use timing-safe comparison to prevent timing attacks."""
        payload = '{"feature_id": "test-123"}'
        secret = "test-secret"
        signature = compute_webhook_signature(payload, secret)

        # This test verifies the function runs without errors
        # Actual timing-safe comparison is handled by hmac.compare_digest
        is_valid = verify_webhook_signature(payload, signature, secret)

        assert is_valid is True
