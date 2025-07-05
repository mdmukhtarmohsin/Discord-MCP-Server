#!/usr/bin/env python3
"""Script to run the Discord MCP Server."""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import main
from src.models.settings import settings
from src.utils.logging import setup_logging, get_logger


def check_requirements():
    """Check if all required environment variables are set."""
    required_vars = [
        'DISCORD_BOT_TOKEN',
        'JWT_SECRET_KEY',
        'REDIS_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or environment configuration.")
        return False
    
    return True


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Discord MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_server.py                    # Run with default settings
  python scripts/run_server.py --host 0.0.0.0    # Run on all interfaces
  python scripts/run_server.py --port 8001        # Run on custom port
  python scripts/run_server.py --debug            # Run in debug mode
        """
    )
    
    parser.add_argument(
        '--host',
        default=settings.mcp_server_host,
        help=f'Host to bind to (default: {settings.mcp_server_host})'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=settings.mcp_server_port,
        help=f'Port to bind to (default: {settings.mcp_server_port})'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--no-check',
        action='store_true',
        help='Skip environment variable checks'
    )
    
    return parser.parse_args()


async def run_server(host: str, port: int, debug: bool = False):
    """Run the server with the specified configuration."""
    # Override settings if provided
    if host != settings.mcp_server_host:
        settings.mcp_server_host = host
    
    if port != settings.mcp_server_port:
        settings.mcp_server_port = port
    
    if debug:
        settings.log_level = "DEBUG"
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Setup logging with updated settings
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info(
        "Starting Discord MCP Server",
        host=host,
        port=port,
        debug=debug,
        server_name=settings.mcp_server_name
    )
    
    try:
        await main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error("Server failed to start", error=str(e))
        raise


def main_cli():
    """Main CLI entry point."""
    args = parse_args()
    
    print("🚀 Discord MCP Server")
    print("=" * 50)
    
    # Check requirements unless skipped
    if not args.no_check and not check_requirements():
        sys.exit(1)
    
    print(f"📡 Server will start on {args.host}:{args.port}")
    print(f"🔧 Debug mode: {'enabled' if args.debug else 'disabled'}")
    print(f"📝 Log level: {settings.log_level}")
    print()
    
    try:
        asyncio.run(run_server(args.host, args.port, args.debug))
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_cli() 