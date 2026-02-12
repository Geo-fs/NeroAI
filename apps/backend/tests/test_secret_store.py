from app.services.secret_store import get_secret, secret_is_encrypted, set_secret


def test_secret_encrypted_at_rest() -> None:
    set_secret("test:key", "super-secret-value")
    assert get_secret("test:key") == "super-secret-value"
    assert secret_is_encrypted("test:key", "super-secret-value") is True
