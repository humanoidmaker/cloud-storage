import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.utils.tokens import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    decode_token,
)


def test_create_access_token_valid():
    uid = uuid.uuid4()
    token = create_access_token(uid, "test@example.com", "user")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_valid():
    uid = uuid.uuid4()
    token = create_refresh_token(uid)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_valid_token():
    uid = uuid.uuid4()
    token = create_access_token(uid, "test@example.com", "user")
    payload = decode_token(token)
    assert payload["sub"] == str(uid)
    assert payload["email"] == "test@example.com"


def test_decode_expired_token():
    from jose import jwt
    from app.config import settings

    payload = {
        "sub": str(uuid.uuid4()),
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(TokenError):
        decode_token(token)


def test_decode_invalid_token():
    with pytest.raises(TokenError):
        decode_token("not-a-valid-token")


def test_decode_tampered_token():
    uid = uuid.uuid4()
    token = create_access_token(uid, "test@example.com", "user")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(TokenError):
        decode_token(tampered)


def test_token_contains_correct_role():
    uid = uuid.uuid4()
    token = create_access_token(uid, "test@example.com", "admin")
    payload = decode_access_token(token)
    assert payload["role"] == "admin"


def test_token_contains_correct_user_id():
    uid = uuid.uuid4()
    token = create_access_token(uid, "test@example.com", "user")
    payload = decode_access_token(token)
    assert payload["sub"] == str(uid)
