"""Unit tests for configuration module."""

from config import Settings


def test_settings_defaults():
    """Verify default Settings initialization."""
    s = Settings()
    assert s.gms_url == "http://localhost:8080"
    assert s.host == "127.0.0.1"
    assert s.port == 8000
    assert s.log_level == "INFO"
    assert s.policy_path == "policies.yaml"
