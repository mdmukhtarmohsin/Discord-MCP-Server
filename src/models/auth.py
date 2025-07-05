"""Authentication models for the MCP Discord Server."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """Permission levels for API access."""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    MODERATE = "moderate"
    ADMIN = "admin"


class APIKey(BaseModel):
    """API Key model for authentication."""
    key_id: str = Field(..., description="Unique identifier for the API key")
    hashed_key: str = Field(..., description="Hashed API key")
    name: str = Field(..., description="Human-readable name for the key")
    permissions: List[PermissionLevel] = Field(default=[], description="List of permissions")
    guild_ids: List[str] = Field(default=[], description="Allowed Discord guild IDs")
    channel_ids: List[str] = Field(default=[], description="Allowed Discord channel IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(True, description="Whether the key is active")
    rate_limit_override: Optional[int] = Field(None, description="Custom rate limit")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class User(BaseModel):
    """User model for multi-tenancy support."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    discord_user_id: Optional[str] = Field(None, description="Discord user ID")
    api_keys: List[str] = Field(default=[], description="List of API key IDs")
    permissions: List[PermissionLevel] = Field(default=[], description="Global permissions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Whether the user is active")


class AuthToken(BaseModel):
    """Authentication token model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenData(BaseModel):
    """Token payload data."""
    key_id: Optional[str] = None
    user_id: Optional[str] = None
    permissions: List[PermissionLevel] = Field(default=[])
    guild_ids: List[str] = Field(default=[])
    channel_ids: List[str] = Field(default=[])


class AuditLog(BaseModel):
    """Audit log entry for tracking operations."""
    log_id: str = Field(..., description="Unique log entry ID")
    user_id: Optional[str] = Field(None, description="User who performed the action")
    key_id: Optional[str] = Field(None, description="API key used")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    guild_id: Optional[str] = Field(None, description="Discord guild ID")
    channel_id: Optional[str] = Field(None, description="Discord channel ID")
    success: bool = Field(..., description="Whether the action succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data") 