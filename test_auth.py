import os
from datetime import datetime, timedelta, timezone

import jwt
from auth import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing():
    password = "example-test-password"
    stored_hash = hash_password(password)

    assert stored_hash != password
    assert verify_password(password, stored_hash) is True
    assert verify_password("wrong-password", stored_hash) is False


def test_create_access_token(monkeypatch):
    test_secret = "test-only-signing-secret-not-for-real-use"
    monkeypatch.setenv("JWT_SECRET_KEY", test_secret)

    token = create_access_token(user_id=7)

    payload = jwt.decode(
        token,
        test_secret,
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]}
    )

    assert payload["sub"] == "7"

def test_decode_access_token(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-only-signing-secret-not-for-real-use"
    )

    token = create_access_token(user_id=7)
    payload = decode_access_token(token)

    assert payload["sub"] == "7"