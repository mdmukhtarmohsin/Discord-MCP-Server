"""Main application entry point for Discord MCP Server."""

import asyncio
import signal
import sys
from typing import Optional
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .bot.discord_client import bot
from .mcp.server import get_mcp_server
from .models.settings import settings
from .auth.middleware import rate_limit_middleware, auth_manager
from .utils.logging import setup_logging


# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting Discord MCP Server")
    
    # Start Discord bot
    bot_task = asyncio.create_task(bot.start(settings.discord_bot_token))
    
    # Wait a bit for bot to connect
    await asyncio.sleep(5)
    
    if not bot.is_ready:
        logger.warning("Discord bot not ready after 5 seconds")
    
    logger.info(
        "Discord MCP Server started",
        mcp_server_name=settings.mcp_server_name,
        discord_ready=bot.is_ready
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Discord MCP Server")
    
    # Close Discord bot
    if not bot.is_closed():
        await bot.close()
    
    # Cancel bot task
    if not bot_task.done():
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Discord MCP Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Discord MCP Server",
    description="Model Context Protocol server for Discord integration",
    version=settings.mcp_server_version,
    lifespan=lifespan
)

# Add CORS middleware
if settings.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": settings.mcp_server_name,
        "version": settings.mcp_server_version,
        "status": "running",
        "discord_bot_ready": bot.is_ready,
        "discord_user": str(bot.user) if bot.user else None,
        "guild_count": len(bot.guilds) if bot.is_ready else 0
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "discord_connected": bot.is_ready,
        "timestamp": asyncio.get_event_loop().time()
    }


@app.get("/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools."""
    mcp_server = get_mcp_server()
    tools = []
    
    # This would normally be handled by the MCP server itself
    # For demonstration, we'll list the known tools
    return {
        "tools": [
            {
                "name": "send_message",
                "description": "Send a message to a Discord channel",
                "parameters": {
                    "channel_id": {"type": "string", "required": True},
                    "content": {"type": "string", "required": True},
                    "embed": {"type": "object", "required": False}
                }
            },
            {
                "name": "get_messages",
                "description": "Retrieve message history from a Discord channel",
                "parameters": {
                    "channel_id": {"type": "string", "required": True},
                    "limit": {"type": "integer", "default": 100},
                    "before": {"type": "string", "required": False},
                    "after": {"type": "string", "required": False}
                }
            },
            {
                "name": "get_channel_info",
                "description": "Get information about a Discord channel",
                "parameters": {
                    "channel_id": {"type": "string", "required": True}
                }
            },
            {
                "name": "search_messages",
                "description": "Search for messages with various filters",
                "parameters": {
                    "query": {"type": "string", "required": False},
                    "channel_id": {"type": "string", "required": False},
                    "guild_id": {"type": "string", "required": False},
                    "author_id": {"type": "string", "required": False},
                    "limit": {"type": "integer", "default": 100}
                }
            },
            {
                "name": "moderate_content",
                "description": "Perform moderation actions on Discord content",
                "parameters": {
                    "action": {"type": "string", "required": True},
                    "target_id": {"type": "string", "required": True},
                    "guild_id": {"type": "string", "required": True},
                    "reason": {"type": "string", "required": False}
                }
            }
        ]
    }


# Add MCP server to FastAPI app
mcp = get_mcp_server()


async def main():
    """Main function to run the server."""
    try:
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the server
        config = uvicorn.Config(
            app,
            host=settings.mcp_server_host,
            port=settings.mcp_server_port,
            log_level=settings.log_level.lower(),
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error("Failed to start server", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main()) 