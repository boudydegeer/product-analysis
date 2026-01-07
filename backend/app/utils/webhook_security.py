"""Security utilities for webhook validation."""

import hmac
import hashlib
import secrets


def generate_webhook_secret(length: int = 32) -> str:
    """Generate a random webhook secret.

    Args:
        length: Length of the secret in bytes (default 32).

    Returns:
        A URL-safe random string to use as webhook secret.
    """
    return secrets.token_urlsafe(length)


def compute_webhook_signature(payload: str, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload.

    Args:
        payload: The webhook payload as a string (JSON).
        secret: The webhook secret key.

    Returns:
        Hexadecimal string of the HMAC signature.
    """
    payload_bytes = payload.encode("utf-8")
    secret_bytes = secret.encode("utf-8")

    signature = hmac.new(
        secret_bytes,
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    return signature


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature matches expected value.

    Uses timing-safe comparison to prevent timing attacks.

    Args:
        payload: The webhook payload as a string (JSON).
        signature: The signature to verify (hex string).
        secret: The webhook secret key.

    Returns:
        True if signature is valid, False otherwise.
    """
    if not signature:
        return False

    expected_signature = compute_webhook_signature(payload, secret)

    # Use timing-safe comparison
    return hmac.compare_digest(signature, expected_signature)
