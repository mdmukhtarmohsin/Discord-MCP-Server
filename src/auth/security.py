"""Security utilities for authentication and authorization."""

import secrets
import hashlib
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from passlib.hash import bcrypt
import structlog

from models.auth import PermissionLevel, TokenData, APIKey
from models.settings import settings

logger = structlog.get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return pwd_context.verify(plain_key, hashed_key)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.api_key_expire_hours)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error("Failed to create access token", error=str(e))
        raise


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        key_id: Optional[str] = payload.get("key_id")
        user_id: Optional[str] = payload.get("user_id")
        permissions: List[str] = payload.get("permissions", [])
        guild_ids: List[str] = payload.get("guild_ids", [])
        channel_ids: List[str] = payload.get("channel_ids", [])
        
        # Convert permission strings back to PermissionLevel enums
        permission_levels = [PermissionLevel(p) for p in permissions if p in PermissionLevel.__members__.values()]
        
        return TokenData(
            key_id=key_id,
            user_id=user_id,
            permissions=permission_levels,
            guild_ids=guild_ids,
            channel_ids=channel_ids
        )
    except jwt.JWTError as e:
        logger.warning("Invalid token", error=str(e))
        return None
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        return None


def check_permission(
    token_data: TokenData,
    required_permission: PermissionLevel,
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None
) -> bool:
    """Check if token has required permission for the specified scope."""
    
    # Check if user has the required permission level
    if required_permission not in token_data.permissions:
        # Check if user has a higher permission level
        permission_hierarchy = {
            PermissionLevel.READ_ONLY: 1,
            PermissionLevel.READ_WRITE: 2,
            PermissionLevel.MODERATE: 3,
            PermissionLevel.ADMIN: 4
        }
        
        required_level = permission_hierarchy.get(required_permission, 0)
        user_max_level = max(
            [permission_hierarchy.get(p, 0) for p in token_data.permissions],
            default=0
        )
        
        if user_max_level < required_level:
            return False
    
    # Check guild scope if specified
    if guild_id and token_data.guild_ids:
        if guild_id not in token_data.guild_ids:
            return False
    
    # Check channel scope if specified
    if channel_id and token_data.channel_ids:
        if channel_id not in token_data.channel_ids:
            return False
    
    return True


def generate_key_id() -> str:
    """Generate a unique API key identifier."""
    return f"key_{secrets.token_hex(16)}"


def create_api_key_token(api_key: APIKey) -> str:
    """Create a JWT token for an API key."""
    token_data = {
        "key_id": api_key.key_id,
        "permissions": [p.value for p in api_key.permissions],
        "guild_ids": api_key.guild_ids,
        "channel_ids": api_key.channel_ids,
        "type": "api_key"
    }
    
    expires_delta = None
    if api_key.expires_at:
        expires_delta = api_key.expires_at - datetime.utcnow()
    
    return create_access_token(token_data, expires_delta)


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password) 