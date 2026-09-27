from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(
    *,
    subject: str,
    roles: list[str],
    private_key: str,
    issuer: str,
    audience: str,
    expires_minutes: int,
) -> str:
    now = datetime.now(UTC)

    claims = {
        "sub": subject,
        "roles": roles,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": str(uuid4()),
    }

    return jwt.encode(claims, private_key, algorithm="RS256")


def decode_access_token(
    *,
    token: str,
    public_key: str,
    issuer: str,
    audience: str,
) -> dict:
    return jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        issuer=issuer,
        audience=audience,
        options={
            "require": ["sub", "iss", "aud", "iat", "exp", "jti"],
        },
    )