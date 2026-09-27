from collections.abc import Callable
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


@dataclass(frozen=True)
class Identity:
    subject: str
    roles: frozenset[str]


async def get_current_identity(
    token: str = Depends(oauth2_scheme),
) -> Identity:
    try:
        claims = decode_configured_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return Identity(
        subject=claims["sub"],
        roles=frozenset(claims.get("roles", [])),
    )


def require_roles(*allowed_roles: str) -> Callable:
    allowed = frozenset(allowed_roles)

    async def authorise(
        identity: Identity = Depends(get_current_identity),
    ) -> Identity:
        if identity.roles.isdisjoint(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission",
            )

        return identity

    return authorise