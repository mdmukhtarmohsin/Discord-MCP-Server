#!/usr/bin/env python3
"""Setup script for Discord MCP Server."""

import os
import secrets
import shutil
from pathlib import Path

def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)

def setup_environment():
    """Set up the environment file."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping environment setup.")
        return
    
    if not env_example.exists():
        print("❌ .env.example file not found.")
        return
    
    # Copy example file
    shutil.copy(env_example, env_file)
    
    # Generate secure keys
    jwt_secret = generate_secret_key()
    api_secret = generate_secret_key()
    
    # Read and update the file
    content = env_file.read_text()
    content = content.replace("your_super_secret_jwt_key_here_at_least_32_chars", jwt_secret)
    content = content.replace("your_api_key_secret_here_at_least_32_chars", api_secret)
    
    env_file.write_text(content)
    print("✅ Created .env file with secure keys")

def check_requirements():
    """Check if requirements are installed."""
    try:
        import discord
        import fastapi
        import redis
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Discord MCP Server")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Setup environment
    setup_environment()
    
    print("\n✨ Setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your Discord bot token")
    print("2. Start Redis server: redis-server")
    print("3. Run the server: python3 run.py")
    print("\n🔗 Useful links:")
    print("- Discord Developer Portal: https://discord.com/developers/applications")
    print("- Redis installation: https://redis.io/download")

if __name__ == "__main__":
    main() 