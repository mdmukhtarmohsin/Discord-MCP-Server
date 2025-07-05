"""Configuration settings for the MCP Discord Server."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Discord Bot Configuration
    discord_bot_token: str = Field(default="your_bot_token_here")
    discord_guild_id: str = Field(default="your_guild_id_here")
    
    # MCP Server Configuration
    mcp_server_name: str = "discord-mcp-server"
    mcp_server_version: str = "1.0.0"
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8000
    
    # Authentication
    secret_key: str = Field(default="dev_secret_key_change_in_production")
    api_key_expire_hours: int = 24
    algorithm: str = "HS256"
    
    # Database (Redis)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Security
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_enabled: bool = True
    
    # MCP Inspector
    inspector_enabled: bool = True
    inspector_port: int = 8001
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get settings instance with proper error handling."""
    try:
        return Settings()
    except Exception as e:
        # For development, provide fallback values
        if not os.getenv("DISCORD_BOT_TOKEN"):
            os.environ["DISCORD_BOT_TOKEN"] = "your_bot_token_here"
        if not os.getenv("DISCORD_GUILD_ID"):
            os.environ["DISCORD_GUILD_ID"] = "your_guild_id_here"
        if not os.getenv("SECRET_KEY"):
            os.environ["SECRET_KEY"] = "dev_secret_key_change_in_production"
        return Settings()


# Global settings instance
settings = get_settings() 