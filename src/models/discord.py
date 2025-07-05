"""Discord models for the MCP Discord Server."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    """Discord channel types."""
    TEXT = "text"
    VOICE = "voice"
    CATEGORY = "category"
    NEWS = "news"
    THREAD = "thread"
    FORUM = "forum"
    STAGE = "stage"


class MessageType(str, Enum):
    """Discord message types."""
    DEFAULT = "default"
    REPLY = "reply"
    SLASH_COMMAND = "slash_command"
    CONTEXT_MENU = "context_menu"
    AUTO_MODERATION = "auto_moderation"


class DiscordUser(BaseModel):
    """Discord user model."""
    id: str = Field(..., description="Discord user ID")
    username: str = Field(..., description="Username")
    discriminator: str = Field(..., description="User discriminator")
    global_name: Optional[str] = Field(None, description="Global display name")
    avatar: Optional[str] = Field(None, description="Avatar hash")
    bot: bool = Field(False, description="Whether the user is a bot")
    system: bool = Field(False, description="Whether the user is a system user")


class DiscordChannel(BaseModel):
    """Discord channel model."""
    id: str = Field(..., description="Channel ID")
    name: str = Field(..., description="Channel name")
    type: ChannelType = Field(..., description="Channel type")
    guild_id: Optional[str] = Field(None, description="Guild ID")
    position: Optional[int] = Field(None, description="Channel position")
    topic: Optional[str] = Field(None, description="Channel topic")
    nsfw: bool = Field(False, description="Whether the channel is NSFW")
    parent_id: Optional[str] = Field(None, description="Parent category ID")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="Channel permissions")


class DiscordMessage(BaseModel):
    """Discord message model."""
    id: str = Field(..., description="Message ID")
    channel_id: str = Field(..., description="Channel ID")
    guild_id: Optional[str] = Field(None, description="Guild ID")
    author: DiscordUser = Field(..., description="Message author")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    edited_timestamp: Optional[datetime] = Field(None, description="Edit timestamp")
    tts: bool = Field(False, description="Whether the message is TTS")
    mention_everyone: bool = Field(False, description="Whether @everyone is mentioned")
    mentions: List[DiscordUser] = Field(default=[], description="Mentioned users")
    mention_roles: List[str] = Field(default=[], description="Mentioned role IDs")
    attachments: List[Dict[str, Any]] = Field(default=[], description="Message attachments")
    embeds: List[Dict[str, Any]] = Field(default=[], description="Message embeds")
    reactions: List[Dict[str, Any]] = Field(default=[], description="Message reactions")
    pinned: bool = Field(False, description="Whether the message is pinned")
    type: MessageType = Field(MessageType.DEFAULT, description="Message type")
    referenced_message: Optional[str] = Field(None, description="Referenced message ID")


class DiscordGuild(BaseModel):
    """Discord guild (server) model."""
    id: str = Field(..., description="Guild ID")
    name: str = Field(..., description="Guild name")
    icon: Optional[str] = Field(None, description="Guild icon hash")
    description: Optional[str] = Field(None, description="Guild description")
    member_count: int = Field(..., description="Member count")
    owner_id: str = Field(..., description="Guild owner ID")
    verification_level: int = Field(..., description="Verification level")
    default_message_notifications: int = Field(..., description="Default notification level")
    explicit_content_filter: int = Field(..., description="Explicit content filter level")
    features: List[str] = Field(default=[], description="Guild features")


class MessageSearchFilter(BaseModel):
    """Filter options for message search."""
    author_id: Optional[str] = Field(None, description="Filter by author ID")
    channel_id: Optional[str] = Field(None, description="Filter by channel ID")
    guild_id: Optional[str] = Field(None, description="Filter by guild ID")
    content_contains: Optional[str] = Field(None, description="Content contains text")
    has_attachments: Optional[bool] = Field(None, description="Has attachments")
    has_embeds: Optional[bool] = Field(None, description="Has embeds")
    before: Optional[datetime] = Field(None, description="Messages before timestamp")
    after: Optional[datetime] = Field(None, description="Messages after timestamp")
    limit: int = Field(100, description="Maximum number of results")
    pinned_only: bool = Field(False, description="Only pinned messages")


class ModerateAction(str, Enum):
    """Moderation actions."""
    DELETE_MESSAGE = "delete_message"
    KICK_USER = "kick_user"
    BAN_USER = "ban_user"
    TIMEOUT_USER = "timeout_user"
    DELETE_MESSAGES_BULK = "delete_messages_bulk"


class ModerationRequest(BaseModel):
    """Moderation request model."""
    action: ModerateAction = Field(..., description="Moderation action to perform")
    target_id: str = Field(..., description="Target ID (message, user, etc.)")
    guild_id: str = Field(..., description="Guild ID")
    channel_id: Optional[str] = Field(None, description="Channel ID")
    reason: Optional[str] = Field(None, description="Reason for the action")
    delete_message_days: Optional[int] = Field(None, description="Days of messages to delete")
    timeout_duration: Optional[int] = Field(None, description="Timeout duration in seconds") 