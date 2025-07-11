#!/usr/bin/env python3
"""Script to help set up the environment for Discord MCP Server."""

import os
import secrets
import string
from pathlib import Path
from typing import Dict, Any
import sys


def generate_jwt_secret() -> str:
    """Generate a secure JWT secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(64))


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_hex(32)


def get_user_input(prompt: str, default: str = None, required: bool = True) -> str:
    """Get input from user with optional default."""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        value = input(full_prompt).strip()
        
        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please provide a value.")


def collect_configuration() -> Dict[str, Any]:
    """Collect configuration from user."""
    print("🔧 Discord MCP Server Configuration Setup")
    print("=" * 50)
    print()
    
    config = {}
    
    # Discord Bot Configuration
    print("📱 Discord Bot Configuration")
    print("-" * 30)
    
    config['DISCORD_BOT_TOKEN'] = get_user_input(
        "Discord Bot Token (from Discord Developer Portal)"
    )
    
    print()
    
    # Server Configuration
    print("🖥️  Server Configuration")
    print("-" * 25)
    
    config['MCP_SERVER_NAME'] = get_user_input(
        "MCP Server Name",
        default="discord-mcp-server"
    )
    
    config['MCP_SERVER_HOST'] = get_user_input(
        "Server Host",
        default="127.0.0.1"
    )
    
    config['MCP_SERVER_PORT'] = get_user_input(
        "Server Port",
        default="8000"
    )
    
    print()
    
    # Security Configuration
    print("🔐 Security Configuration")
    print("-" * 25)
    
    config['JWT_SECRET_KEY'] = generate_jwt_secret()
    print(f"Generated JWT Secret Key: {config['JWT_SECRET_KEY'][:20]}...")
    
    config['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = get_user_input(
        "JWT Token Expiration (minutes)",
        default="1440"  # 24 hours
    )
    
    print()
    
    # Redis Configuration
    print("📊 Redis Configuration")
    print("-" * 22)
    
    config['REDIS_URL'] = get_user_input(
        "Redis URL",
        default="redis://localhost:6379/0"
    )
    
    print()
    
    # Logging Configuration
    print("📝 Logging Configuration")
    print("-" * 25)
    
    config['LOG_LEVEL'] = get_user_input(
        "Log Level (DEBUG, INFO, WARNING, ERROR)",
        default="INFO"
    )
    
    config['LOG_FORMAT'] = get_user_input(
        "Log Format (json, console)",
        default="console"
    )
    
    print()
    
    # CORS Configuration
    print("🌐 CORS Configuration")
    print("-" * 20)
    
    cors_enabled = get_user_input(
        "Enable CORS? (y/n)",
        default="n"
    ).lower() in ['y', 'yes', 'true', '1']
    
    config['CORS_ENABLED'] = str(cors_enabled).lower()
    
    if cors_enabled:
        config['ALLOWED_ORIGINS'] = get_user_input(
            "Allowed Origins (comma-separated)",
            default="http://localhost:3000,http://127.0.0.1:3000"
        )
    else:
        config['ALLOWED_ORIGINS'] = ""
    
    print()
    
    # Rate Limiting
    print("⚡ Rate Limiting Configuration")
    print("-" * 30)
    
    config['RATE_LIMIT_REQUESTS'] = get_user_input(
        "Rate limit requests per minute",
        default="100"
    )
    
    config['RATE_LIMIT_WINDOW'] = get_user_input(
        "Rate limit window (seconds)",
        default="60"
    )
    
    return config


def write_env_file(config: Dict[str, Any], filepath: Path) -> None:
    """Write configuration to .env file."""
    with open(filepath, 'w') as f:
        f.write("# Discord MCP Server Configuration\n")
        f.write("# Generated by setup_env.py\n\n")
        
        # Discord Bot
        f.write("# Discord Bot Configuration\n")
        f.write(f"DISCORD_BOT_TOKEN={config['DISCORD_BOT_TOKEN']}\n\n")
        
        # Server
        f.write("# Server Configuration\n")
        f.write(f"MCP_SERVER_NAME={config['MCP_SERVER_NAME']}\n")
        f.write(f"MCP_SERVER_HOST={config['MCP_SERVER_HOST']}\n")
        f.write(f"MCP_SERVER_PORT={config['MCP_SERVER_PORT']}\n")
        f.write("MCP_SERVER_VERSION=1.0.0\n\n")
        
        # Security
        f.write("# Security Configuration\n")
        f.write(f"JWT_SECRET_KEY={config['JWT_SECRET_KEY']}\n")
        f.write(f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES={config['JWT_ACCESS_TOKEN_EXPIRE_MINUTES']}\n\n")
        
        # Redis
        f.write("# Redis Configuration\n")
        f.write(f"REDIS_URL={config['REDIS_URL']}\n\n")
        
        # Logging
        f.write("# Logging Configuration\n")
        f.write(f"LOG_LEVEL={config['LOG_LEVEL']}\n")
        f.write(f"LOG_FORMAT={config['LOG_FORMAT']}\n\n")
        
        # CORS
        f.write("# CORS Configuration\n")
        f.write(f"CORS_ENABLED={config['CORS_ENABLED']}\n")
        f.write(f"ALLOWED_ORIGINS={config['ALLOWED_ORIGINS']}\n\n")
        
        # Rate Limiting
        f.write("# Rate Limiting Configuration\n")
        f.write(f"RATE_LIMIT_REQUESTS={config['RATE_LIMIT_REQUESTS']}\n")
        f.write(f"RATE_LIMIT_WINDOW={config['RATE_LIMIT_WINDOW']}\n\n")
        
        # Optional: Development settings
        f.write("# Development Settings (uncomment as needed)\n")
        f.write("# DEBUG=true\n")
        f.write("# DEVELOPMENT_MODE=true\n")


def main():
    """Main function."""
    print("Welcome to the Discord MCP Server setup utility!")
    print()
    
    # Check if .env already exists
    env_file = Path(".env")
    if env_file.exists():
        overwrite = get_user_input(
            ".env file already exists. Overwrite? (y/n)",
            default="n"
        ).lower() in ['y', 'yes', 'true', '1']
        
        if not overwrite:
            print("Setup cancelled.")
            return
    
    try:
        # Collect configuration
        config = collect_configuration()
        
        # Write .env file
        write_env_file(config, env_file)
        
        print("✅ Configuration saved to .env file!")
        print()
        print("📋 Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start Redis server (if not already running)")
        print("3. Run the server: python scripts/run_server.py")
        print()
        print("🔗 Useful links:")
        print("- Discord Developer Portal: https://discord.com/developers/applications")
        print("- Redis installation: https://redis.io/download")
        print()
        print("💡 To regenerate this configuration, run this script again.")
        
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 