# Discord MCP Server

A comprehensive Model Context Protocol (MCP) server for Discord integration, providing secure access to Discord functionality through a standardized API interface.

## 🚀 Features

- **FastMCP Integration**: Built on top of FastMCP for efficient MCP server implementation
- **Discord Bot**: Full-featured Discord bot with message handling and moderation capabilities
- **Authentication & Authorization**: JWT-based authentication with API key management
- **Rate Limiting**: Redis-based rate limiting with configurable limits
- **Multi-tenancy**: Support for multiple users with permission-based access control
- **Audit Logging**: Comprehensive logging of all actions and API calls
- **Moderation Tools**: Built-in content moderation and user management
- **Secure**: Hash-based API key storage and encrypted JWT tokens

## 📋 Requirements

- Python 3.9+
- Redis server
- Discord Bot Token (from Discord Developer Portal)
- Virtual environment (recommended)

## 🛠️ Installation

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd Discord-MCP-Server

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Run the interactive setup script:

```bash
python3 scripts/setup_env.py
```

Or manually create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Start Redis Server

Make sure Redis is running on your system:

```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS with Homebrew
brew services start redis

# Or run directly
redis-server
```

### 5. Run the Server

```bash
python3 scripts/run_server.py
```

For development with debug mode:

```bash
python3 scripts/run_server.py --debug
```

## ⚙️ Configuration

### Environment Variables

| Variable              | Description                             | Default                    |
| --------------------- | --------------------------------------- | -------------------------- |
| `DISCORD_BOT_TOKEN`   | Discord bot token from Developer Portal | **Required**               |
| `JWT_SECRET_KEY`      | Secret key for JWT token signing        | **Required**               |
| `REDIS_URL`           | Redis connection URL                    | `redis://localhost:6379/0` |
| `MCP_SERVER_NAME`     | Name of the MCP server                  | `discord-mcp-server`       |
| `MCP_SERVER_HOST`     | Server host address                     | `127.0.0.1`                |
| `MCP_SERVER_PORT`     | Server port                             | `8000`                     |
| `LOG_LEVEL`           | Logging level                           | `INFO`                     |
| `LOG_FORMAT`          | Log format (json/console)               | `console`                  |
| `CORS_ENABLED`        | Enable CORS                             | `false`                    |
| `ALLOWED_ORIGINS`     | Comma-separated allowed origins         | ``                         |
| `RATE_LIMIT_REQUESTS` | Requests per window                     | `100`                      |
| `RATE_LIMIT_WINDOW`   | Rate limit window in seconds            | `60`                       |

### Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable necessary intents:
   - Message Content Intent
   - Server Members Intent
   - Guilds Intent
6. Invite the bot to your server with appropriate permissions

## 🔧 API Usage

### MCP Tools

The server provides the following MCP tools:

#### `send_message`

Send a message to a Discord channel.

```json
{
  "tool": "send_message",
  "arguments": {
    "channel_id": "123456789",
    "content": "Hello, world!",
    "embed": {
      "title": "Optional Embed",
      "description": "Embed content"
    }
  }
}
```

#### `get_messages`

Retrieve message history from a channel.

```json
{
  "tool": "get_messages",
  "arguments": {
    "channel_id": "123456789",
    "limit": 50,
    "before": "2023-12-01T00:00:00Z",
    "after": "2023-11-01T00:00:00Z"
  }
}
```

#### `get_channel_info`

Get information about a Discord channel.

```json
{
  "tool": "get_channel_info",
  "arguments": {
    "channel_id": "123456789"
  }
}
```

#### `search_messages`

Search for messages with various filters.

```json
{
  "tool": "search_messages",
  "arguments": {
    "query": "search term",
    "channel_id": "123456789",
    "author_id": "987654321",
    "limit": 100
  }
}
```

#### `moderate_content`

Perform moderation actions.

```json
{
  "tool": "moderate_content",
  "arguments": {
    "action": "delete_message",
    "target_id": "message_id",
    "guild_id": "guild_id",
    "reason": "Spam content"
  }
}
```

### REST API Endpoints

- `GET /` - Server status and information
- `GET /health` - Health check endpoint
- `GET /mcp/tools` - List available MCP tools
- `GET /mcp/resources/discord://status` - Discord bot status

## 🔐 Authentication

The server uses JWT-based authentication with API keys. Each API key has:

- **User ID**: Unique identifier for the user
- **Permissions**: Read-only, Read-write, or Moderation access
- **Guild/Channel Restrictions**: Optional access limitations
- **Expiration Date**: Automatic key expiration
- **Rate Limiting**: Per-key rate limits

### Permission Levels

1. **READ_ONLY**: Can retrieve messages and channel information
2. **READ_WRITE**: Can send messages and retrieve data
3. **MODERATE**: Can perform moderation actions (delete, ban, etc.)

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/test_auth.py -v

# Run with coverage
python3 -m pytest --cov=src tests/
```

## 📊 Monitoring and Logging

The server provides structured logging with configurable formats:

- **Console Format**: Human-readable colored output
- **JSON Format**: Machine-readable for log aggregation

Key log events include:

- Authentication attempts
- API calls and responses
- Discord actions (messages, moderation)
- Rate limiting events
- Errors and exceptions

## 🚨 Security Considerations

- **API Keys**: Stored as SHA-256 hashes in Redis
- **JWT Tokens**: Signed with strong secret keys
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Input Validation**: All inputs are validated and sanitized
- **Permission Checks**: Fine-grained access control
- **Audit Logging**: Complete audit trail of all actions

## 🔧 Development

### Project Structure

```
Discord-MCP-Server/
├── src/
│   ├── auth/               # Authentication and authorization
│   ├── bot/                # Discord bot implementation
│   ├── mcp/                # MCP server and tools
│   ├── models/             # Data models and schemas
│   ├── utils/              # Utility functions
│   └── main.py             # Application entry point
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
└── README.md              # This file
```

### Adding New MCP Tools

1. Define the tool function in `src/mcp/server.py`
2. Use the `@mcp_server.tool()` decorator
3. Add appropriate error handling and logging
4. Update the API documentation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the documentation and examples
2. Review the test cases for usage patterns
3. Open an issue on GitHub
4. Join our Discord community

## 🔗 Related Projects

- [FastMCP](https://github.com/jlowin/fastmcp) - Fast MCP server implementation
- [Discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [Model Context Protocol](https://github.com/modelcontextprotocol) - MCP specification

---

Made with ❤️ for the Discord and MCP communities
