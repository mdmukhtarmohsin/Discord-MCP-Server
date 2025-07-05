"""MCP Server implementation for Discord integration."""

import asyncio
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
import structlog
from fastmcp import FastMCP

from ..bot.discord_client import bot
from ..models.discord import (
    DiscordMessage, DiscordChannel, MessageSearchFilter, 
    ModerationRequest, ModerateAction
)
from ..models.auth import PermissionLevel
from ..models.settings import settings

logger = structlog.get_logger(__name__)

# Initialize FastMCP server
mcp_server = FastMCP(settings.mcp_server_name)


@mcp_server.tool()
async def send_message(
    channel_id: str,
    content: str,
    embed: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send a message to a Discord channel.
    
    Args:
        channel_id: The Discord channel ID to send the message to
        content: The message content to send
        embed: Optional embed object to include with the message
    
    Returns:
        Dictionary containing the sent message information
    """
    try:
        # Send message via Discord bot
        message = await bot.send_message_to_channel(channel_id, content, embed)
        
        logger.info(
            "Message sent via MCP",
            channel_id=channel_id,
            message_id=message.id
        )
        
        return {
            "success": True,
            "message_id": message.id,
            "channel_id": message.channel_id,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "author": {
                "id": message.author.id,
                "username": message.author.username
            }
        }
        
    except Exception as e:
        logger.error("Failed to send message via MCP", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@mcp_server.tool()
async def get_messages(
    channel_id: str,
    limit: int = 100,
    before: Optional[str] = None,
    after: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve message history from a Discord channel.
    
    Args:
        channel_id: The Discord channel ID to get messages from
        limit: Maximum number of messages to retrieve (default: 100)
        before: Get messages before this timestamp (ISO format)
        after: Get messages after this timestamp (ISO format)
    
    Returns:
        Dictionary containing the retrieved messages
    """
    try:
        # Convert timestamp strings to datetime objects
        before_dt = datetime.fromisoformat(before) if before else None
        after_dt = datetime.fromisoformat(after) if after else None
        
        # Get messages via Discord bot
        messages = await bot.get_messages_from_channel(
            channel_id, limit, before_dt, after_dt
        )
        
        logger.info(
            "Messages retrieved via MCP",
            channel_id=channel_id,
            count=len(messages)
        )
        
        return {
            "success": True,
            "channel_id": channel_id,
            "message_count": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "author": {
                        "id": msg.author.id,
                        "username": msg.author.username,
                        "bot": msg.author.bot
                    },
                    "timestamp": msg.timestamp.isoformat(),
                    "edited_timestamp": msg.edited_timestamp.isoformat() if msg.edited_timestamp else None,
                    "attachments": msg.attachments,
                    "embeds": msg.embeds,
                    "reactions": msg.reactions,
                    "pinned": msg.pinned
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        logger.error("Failed to get messages via MCP", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@mcp_server.tool()
async def get_channel_info(
    channel_id: str
) -> Dict[str, Any]:
    """
    Get information about a Discord channel.
    
    Args:
        channel_id: The Discord channel ID to get information about
    
    Returns:
        Dictionary containing the channel information
    """
    try:
        # Get channel info via Discord bot
        channel = await bot.get_channel_info(channel_id)
        
        logger.info(
            "Channel info retrieved via MCP",
            channel_id=channel_id
        )
        
        return {
            "success": True,
            "channel": {
                "id": channel.id,
                "name": channel.name,
                "type": channel.type,
                "guild_id": channel.guild_id,
                "position": channel.position,
                "topic": channel.topic,
                "nsfw": channel.nsfw,
                "created_at": channel.created_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error("Failed to get channel info via MCP", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@mcp_server.tool()
async def search_messages(
    query: Optional[str] = None,
    channel_id: Optional[str] = None,
    guild_id: Optional[str] = None,
    author_id: Optional[str] = None,
    has_attachments: Optional[bool] = None,
    has_embeds: Optional[bool] = None,
    pinned_only: bool = False,
    limit: int = 100,
    before: Optional[str] = None,
    after: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for messages with various filters.
    
    Args:
        query: Text to search for in message content
        channel_id: Limit search to specific channel
        guild_id: Limit search to specific guild
        author_id: Limit search to specific author
        has_attachments: Filter by presence of attachments
        has_embeds: Filter by presence of embeds
        pinned_only: Only return pinned messages
        limit: Maximum number of messages to return
        before: Get messages before this timestamp
        after: Get messages after this timestamp
    
    Returns:
        Dictionary containing the search results
    """
    try:
        # Convert timestamp strings to datetime objects
        before_dt = datetime.fromisoformat(before) if before else None
        after_dt = datetime.fromisoformat(after) if after else None
        
        # Create search filter
        search_filter = MessageSearchFilter(
            content_contains=query,
            channel_id=channel_id,
            guild_id=guild_id,
            author_id=author_id,
            has_attachments=has_attachments,
            has_embeds=has_embeds,
            pinned_only=pinned_only,
            limit=limit,
            before=before_dt,
            after=after_dt
        )
        
        # Search messages via Discord bot
        messages = await bot.search_messages(search_filter)
        
        logger.info(
            "Message search via MCP",
            query=query,
            results=len(messages)
        )
        
        return {
            "success": True,
            "query": query,
            "result_count": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "channel_id": msg.channel_id,
                    "guild_id": msg.guild_id,
                    "author": {
                        "id": msg.author.id,
                        "username": msg.author.username,
                        "bot": msg.author.bot
                    },
                    "timestamp": msg.timestamp.isoformat(),
                    "attachments": msg.attachments,
                    "embeds": msg.embeds,
                    "pinned": msg.pinned
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        logger.error("Failed to search messages via MCP", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@mcp_server.tool()
async def moderate_content(
    action: str,
    target_id: str,
    guild_id: str,
    channel_id: Optional[str] = None,
    reason: Optional[str] = None,
    delete_message_days: Optional[int] = None,
    timeout_duration: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform moderation actions on Discord content.
    
    Args:
        action: Moderation action (delete_message, kick_user, ban_user, timeout_user, delete_messages_bulk)
        target_id: ID of the target (message ID or user ID)
        guild_id: Guild where the action should be performed
        channel_id: Channel ID (required for message actions)
        reason: Reason for the moderation action
        delete_message_days: Days of messages to delete (for bans)
        timeout_duration: Timeout duration in seconds
    
    Returns:
        Dictionary containing the moderation result
    """
    try:
        # Validate action
        try:
            moderate_action = ModerateAction(action)
        except ValueError:
            raise ValueError(f"Invalid moderation action: {action}")
        
        # Create moderation request
        moderation_request = ModerationRequest(
            action=moderate_action,
            target_id=target_id,
            guild_id=guild_id,
            channel_id=channel_id,
            reason=reason,
            delete_message_days=delete_message_days,
            timeout_duration=timeout_duration
        )
        
        # Perform moderation action via Discord bot
        success = await bot.moderate_content(moderation_request)
        
        logger.info(
            "Moderation action via MCP",
            action=action,
            target_id=target_id,
            guild_id=guild_id,
            success=success
        )
        
        return {
            "success": success,
            "action": action,
            "target_id": target_id,
            "guild_id": guild_id,
            "reason": reason
        }
        
    except Exception as e:
        logger.error("Failed to perform moderation action via MCP", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


# Additional MCP server configuration
@mcp_server.resource("discord://status")
async def get_bot_status() -> str:
    """Get the current status of the Discord bot."""
    if bot.is_ready:
        guild_count = len(bot.guilds)
        # Fix the sum function issue by handling None values
        user_count = sum(guild.member_count or 0 for guild in bot.guilds)
        uptime = datetime.utcnow() - bot.startup_time if hasattr(bot, 'startup_time') and bot.startup_time else None
        
        status = {
            "status": "connected",
            "user": str(bot.user) if bot.user else None,
            "guilds": guild_count,
            "users": user_count,
            "uptime_seconds": uptime.total_seconds() if uptime else None
        }
    else:
        status = {
            "status": "disconnected",
            "user": None,
            "guilds": 0,
            "users": 0,
            "uptime_seconds": None
        }
    
    return f"Discord Bot Status: {status}"


# MCP server instance
def get_mcp_server():
    """Get the configured MCP server instance."""
    return mcp_server 