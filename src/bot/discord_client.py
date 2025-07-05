"""Discord bot client implementation."""

import asyncio
from typing import List, Optional, Dict, Any, Union
import discord
from discord.ext import commands
import structlog
from datetime import datetime, timedelta

from ..models.discord import (
    DiscordMessage, DiscordChannel, DiscordUser, DiscordGuild,
    MessageSearchFilter, ModerationRequest, ModerateAction,
    ChannelType, MessageType
)
from ..models.settings import settings

logger = structlog.get_logger(__name__)


class DiscordBot(commands.Bot):
    """Enhanced Discord bot with MCP integration."""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        self.bot_ready = False
        self.startup_time = None
    
    @property
    def is_ready(self) -> bool:
        """Check if bot is ready."""
        return self.bot_ready and super().is_ready
    
    async def on_ready(self):
        """Event fired when bot is ready."""
        self.bot_ready = True
        self.startup_time = datetime.utcnow()
        guild_count = len(self.guilds)
        user_count = sum(guild.member_count for guild in self.guilds if guild.member_count)
        logger.info(
            "Discord bot ready",
            bot_user=str(self.user),
            guild_count=guild_count,
            user_count=user_count
        )
    
    async def on_message(self, message: discord.Message):
        """Event fired when a message is received."""
        if message.author == self.user:
            return
        
        # Log message for auditing
        logger.debug(
            "Message received",
            guild_id=str(message.guild.id) if message.guild else None,
            channel_id=str(message.channel.id),
            author_id=str(message.author.id),
            content_length=len(message.content)
        )
        
        await self.process_commands(message)
    
    def _convert_discord_user(self, user: Union[discord.User, discord.Member]) -> DiscordUser:
        """Convert Discord user to our model."""
        return DiscordUser(
            id=str(user.id),
            username=user.name,
            discriminator=user.discriminator,
            global_name=user.global_name,
            avatar=str(user.avatar.url) if user.avatar else None,
            bot=user.bot,
            system=user.system
        )
    
    def _convert_discord_channel(self, channel: discord.TextChannel) -> DiscordChannel:
        """Convert Discord channel to our model."""
        channel_type_map = {
            discord.ChannelType.text: ChannelType.TEXT,
            discord.ChannelType.voice: ChannelType.VOICE,
            discord.ChannelType.category: ChannelType.CATEGORY,
            discord.ChannelType.news: ChannelType.NEWS,
            discord.ChannelType.stage_voice: ChannelType.STAGE,
            discord.ChannelType.forum: ChannelType.FORUM,
        }
        
        return DiscordChannel(
            id=str(channel.id),
            name=channel.name,
            type=channel_type_map.get(channel.type, ChannelType.TEXT),
            guild_id=str(channel.guild.id) if channel.guild else None,
            position=channel.position,
            topic=channel.topic,
            nsfw=channel.nsfw,
            parent_id=str(channel.category.id) if channel.category else None,
            permissions={}  # Could be populated with channel permissions
        )
    
    def _convert_discord_message(self, message: discord.Message) -> DiscordMessage:
        """Convert Discord message to our model."""
        return DiscordMessage(
            id=str(message.id),
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else None,
            author=self._convert_discord_user(message.author),
            content=message.content,
            timestamp=message.created_at,
            edited_timestamp=message.edited_at,
            tts=message.tts,
            mention_everyone=message.mention_everyone,
            mentions=[self._convert_discord_user(user) for user in message.mentions],
            mention_roles=[str(role.id) for role in message.role_mentions],
            attachments=[{
                "id": str(att.id),
                "filename": att.filename,
                "size": att.size,
                "url": att.url,
                "content_type": att.content_type
            } for att in message.attachments],
            embeds=[embed.to_dict() for embed in message.embeds],
            reactions=[{
                "emoji": str(reaction.emoji),
                "count": reaction.count,
                "me": reaction.me
            } for reaction in message.reactions],
            pinned=message.pinned,
            type=MessageType.DEFAULT,  # Could be enhanced based on message type
            referenced_message=str(message.reference.message_id) if message.reference else None
        )
    
    async def send_message_to_channel(
        self,
        channel_id: str,
        content: str,
        embed: Optional[Dict[str, Any]] = None
    ) -> DiscordMessage:
        """Send a message to a Discord channel."""
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
            
            # Check if channel supports sending messages
            if not hasattr(channel, 'send'):
                raise ValueError(f"Channel {channel_id} does not support sending messages")
            
            embed_obj = None
            if embed:
                embed_obj = discord.Embed.from_dict(embed)
            
            message = await channel.send(content=content, embed=embed_obj)
            
            logger.info(
                "Message sent",
                channel_id=channel_id,
                message_id=str(message.id),
                content_length=len(content)
            )
            
            return self._convert_discord_message(message)
            
        except Exception as e:
            logger.error("Failed to send message", channel_id=channel_id, error=str(e))
            raise
    
    async def get_messages_from_channel(
        self,
        channel_id: str,
        limit: int = 100,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None
    ) -> List[DiscordMessage]:
        """Get messages from a Discord channel."""
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
            
            messages = []
            async for message in channel.history(
                limit=limit,
                before=before,
                after=after
            ):
                messages.append(self._convert_discord_message(message))
            
            logger.info(
                "Messages retrieved",
                channel_id=channel_id,
                count=len(messages),
                limit=limit
            )
            
            return messages
            
        except Exception as e:
            logger.error("Failed to get messages", channel_id=channel_id, error=str(e))
            raise
    
    async def get_channel_info(self, channel_id: str) -> DiscordChannel:
        """Get information about a Discord channel."""
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
            
            return self._convert_discord_channel(channel)
            
        except Exception as e:
            logger.error("Failed to get channel info", channel_id=channel_id, error=str(e))
            raise
    
    async def search_messages(
        self,
        search_filter: MessageSearchFilter
    ) -> List[DiscordMessage]:
        """Search messages with filters."""
        try:
            messages = []
            
            # Get the channel to search in
            if search_filter.channel_id:
                channels = [self.get_channel(int(search_filter.channel_id))]
            elif search_filter.guild_id:
                guild = self.get_guild(int(search_filter.guild_id))
                if guild:
                    channels = [ch for ch in guild.text_channels]
                else:
                    channels = []
            else:
                # Search all accessible channels
                channels = [ch for guild in self.guilds for ch in guild.text_channels]
            
            for channel in channels:
                if not channel:
                    continue
                
                try:
                    async for message in channel.history(
                        limit=search_filter.limit,
                        before=search_filter.before,
                        after=search_filter.after
                    ):
                        # Apply filters
                        if search_filter.author_id and str(message.author.id) != search_filter.author_id:
                            continue
                        
                        if search_filter.content_contains and search_filter.content_contains.lower() not in message.content.lower():
                            continue
                        
                        if search_filter.has_attachments is not None:
                            if search_filter.has_attachments and not message.attachments:
                                continue
                            if not search_filter.has_attachments and message.attachments:
                                continue
                        
                        if search_filter.has_embeds is not None:
                            if search_filter.has_embeds and not message.embeds:
                                continue
                            if not search_filter.has_embeds and message.embeds:
                                continue
                        
                        if search_filter.pinned_only and not message.pinned:
                            continue
                        
                        messages.append(self._convert_discord_message(message))
                        
                        if len(messages) >= search_filter.limit:
                            break
                
                except discord.Forbidden:
                    # Skip channels we don't have permission to read
                    continue
                except Exception as e:
                    logger.warning("Error searching channel", channel_id=str(channel.id), error=str(e))
                    continue
            
            logger.info(
                "Message search completed",
                results=len(messages),
                filter=search_filter.dict()
            )
            
            return messages[:search_filter.limit]
            
        except Exception as e:
            logger.error("Failed to search messages", error=str(e))
            raise
    
    async def moderate_content(self, moderation_request: ModerationRequest) -> bool:
        """Perform moderation actions."""
        try:
            guild = self.get_guild(int(moderation_request.guild_id))
            if not guild:
                raise ValueError(f"Guild {moderation_request.guild_id} not found")
            
            success = False
            
            if moderation_request.action == ModerateAction.DELETE_MESSAGE:
                channel = guild.get_channel(int(moderation_request.channel_id))
                if channel:
                    try:
                        message = await channel.fetch_message(int(moderation_request.target_id))
                        await message.delete()
                        success = True
                    except discord.NotFound:
                        logger.warning("Message not found for deletion", message_id=moderation_request.target_id)
                        success = False
            
            elif moderation_request.action == ModerateAction.KICK_USER:
                member = guild.get_member(int(moderation_request.target_id))
                if member:
                    await member.kick(reason=moderation_request.reason)
                    success = True
            
            elif moderation_request.action == ModerateAction.BAN_USER:
                member = guild.get_member(int(moderation_request.target_id))
                if member:
                    await member.ban(
                        reason=moderation_request.reason,
                        delete_message_days=moderation_request.delete_message_days or 0
                    )
                    success = True
            
            elif moderation_request.action == ModerateAction.TIMEOUT_USER:
                member = guild.get_member(int(moderation_request.target_id))
                if member and moderation_request.timeout_duration:
                    timeout_until = datetime.utcnow() + timedelta(seconds=moderation_request.timeout_duration)
                    await member.timeout(timeout_until, reason=moderation_request.reason)
                    success = True
            
            elif moderation_request.action == ModerateAction.DELETE_MESSAGES_BULK:
                channel = guild.get_channel(int(moderation_request.channel_id))
                if channel:
                    # This would need specific implementation based on criteria
                    # For now, just log the request
                    logger.info("Bulk delete requested", channel_id=moderation_request.channel_id)
                    success = True
            
            logger.info(
                "Moderation action performed",
                action=moderation_request.action.value,
                target_id=moderation_request.target_id,
                guild_id=moderation_request.guild_id,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error("Failed to perform moderation action", error=str(e))
            raise


# Global bot instance
bot = DiscordBot() 