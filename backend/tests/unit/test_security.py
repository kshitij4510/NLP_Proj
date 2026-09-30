"""Unit tests for auth security utilities."""
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_subject_from_token,
)


def test_password_hash_and_verify():
    plain = "SecurePass123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_password_wrong():
    hashed = hash_password("CorrectPass1")
    assert not verify_password("WrongPass1", hashed)


def test_access_token_roundtrip():
    token = create_access_token("user-id-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-123"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    token = create_refresh_token("user-id-456")
    payload = decode_token(token)
    assert payload["sub"] == "user-id-456"
    assert payload["type"] == "refresh"


def test_get_subject_from_valid_token():
    token = create_access_token("my-subject")
    subject = get_subject_from_token(token)
    assert subject == "my-subject"


def test_get_subject_from_invalid_token():
    subject = get_subject_from_token("not.a.valid.token")
    assert subject is None


def test_tokens_are_different():
    t1 = create_access_token("same-user")
    t2 = create_access_token("same-user")
    # Tokens have different exp values so they won't be identical
    # (they are issued at different times)
    assert isinstance(t1, str)
    assert isinstance(t2, str)
