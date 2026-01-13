"""
Authentication and authorization utilities.
"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import secrets
from typing import Optional

from app.db.base import get_db
from app.models.models import Host, ApiKey
from app.core.config import settings

security = HTTPBearer()


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(
        f"{api_key}{settings.API_KEY_SALT}".encode()
    ).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    return secrets.token_urlsafe(32)


async def get_current_host(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Host:
    """
    Dependency to get the current authenticated host from API key.
    Used for agent authentication.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )

    api_key = credentials.credentials
    api_key_hash = hash_api_key(api_key)

    # Find host with this API key
    query = select(Host).where(Host.api_key_hash == api_key_hash)
    result = await db.execute(query)
    host = result.scalar_one_or_none()

    if not host:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return host


async def verify_api_key(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> ApiKey:
    """
    Dependency to verify API key for general API access.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    api_key = authorization.replace("Bearer ", "")
    api_key_hash = hash_api_key(api_key)

    # Find API key
    query = select(ApiKey).where(
        ApiKey.key_hash == api_key_hash,
        ApiKey.revoked == "false"
    )
    result = await db.execute(query)
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key"
        )

    # Update last used timestamp
    from datetime import datetime
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()

    return api_key_obj
