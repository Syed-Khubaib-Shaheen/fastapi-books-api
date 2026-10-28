import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hasher.verify(password, stored_hash)


def create_access_token(user_id: int) -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")

def decode_access_token(token: str) -> dict:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    return jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]}
    )