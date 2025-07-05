"""Tests for authentication functionality."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.auth.security import (
    generate_api_key, hash_api_key, create_jwt_token, verify_token
)
from src.auth.auth_manager import AuthManager
from src.models.auth import APIKey, PermissionLevel


class TestSecurity:
    """Test security functions."""
    
    def test_generate_api_key(self):
        """Test API key generation."""
        key = generate_api_key()
        assert isinstance(key, str)
        assert len(key) == 64  # 32 bytes in hex
        
        # Test uniqueness
        key2 = generate_api_key()
        assert key != key2
    
    def test_hash_api_key(self):
        """Test API key hashing."""
        key = "test_key"
        hashed = hash_api_key(key)
        
        assert isinstance(hashed, str)
        assert hashed != key
        assert len(hashed) == 64  # SHA256 hex length
        
        # Test consistency
        hashed2 = hash_api_key(key)
        assert hashed == hashed2
    
    def test_create_jwt_token(self):
        """Test JWT token creation."""
        payload = {
            "user_id": "123",
            "key_id": "key_123",
            "permissions": ["READ_ONLY"],
            "guild_ids": ["guild_123"],
            "channel_ids": ["channel_123"]
        }
        
        token = create_jwt_token(payload)
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically longer
    
    def test_verify_token_valid(self):
        """Test JWT token verification with valid token."""
        payload = {
            "user_id": "123",
            "key_id": "key_123",
            "permissions": ["READ_ONLY"],
            "guild_ids": ["guild_123"],
            "channel_ids": ["channel_123"]
        }
        
        token = create_jwt_token(payload)
        result = verify_token(token)
        
        assert result is not None
        assert result["user_id"] == "123"
        assert result["key_id"] == "key_123"
        assert PermissionLevel.READ_ONLY in result["permissions"]
    
    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token."""
        invalid_token = "invalid.token.here"
        result = verify_token(invalid_token)
        assert result is None


class TestAuthManager:
    """Test authentication manager."""
    
    @pytest.fixture
    def auth_manager(self):
        """Create an auth manager instance for testing."""
        with patch('src.auth.auth_manager.redis_client'):
            return AuthManager()
    
    def test_api_key_creation(self, auth_manager):
        """Test API key creation."""
        key_data = APIKey(
            key_id="test_key",
            user_id="test_user",
            permissions=[PermissionLevel.READ_ONLY],
            guild_ids=["guild_123"],
            channel_ids=["channel_123"],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        # Mock the store method
        with patch.object(auth_manager, 'store_api_key', return_value=True):
            result = auth_manager.create_api_key(
                user_id="test_user",
                permissions=[PermissionLevel.READ_ONLY],
                guild_ids=["guild_123"],
                channel_ids=["channel_123"],
                expires_days=30
            )
            
            assert result is not None
            assert isinstance(result, str)  # Returns the raw key
    
    @pytest.mark.asyncio
    async def test_validate_api_key(self, auth_manager):
        """Test API key validation."""
        # Mock Redis get
        mock_key_data = {
            "user_id": "test_user",
            "permissions": ["READ_ONLY"],
            "guild_ids": ["guild_123"],
            "channel_ids": ["channel_123"],
            "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "active": True
        }
        
        with patch.object(auth_manager.redis_client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = str(mock_key_data).replace("'", '"')
            
            result = await auth_manager.validate_api_key("test_key")
            assert result is not None
            assert result["user_id"] == "test_user"


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiting functionality."""
    from src.auth.rate_limiter import RateLimiter
    
    with patch('src.auth.rate_limiter.redis.Redis'):
        rate_limiter = RateLimiter()
        
        # Mock Redis operations
        with patch.object(rate_limiter.redis, 'zcard', new_callable=AsyncMock) as mock_zcard, \
             patch.object(rate_limiter.redis, 'zadd', new_callable=AsyncMock) as mock_zadd, \
             patch.object(rate_limiter.redis, 'zremrangebyscore', new_callable=AsyncMock) as mock_zrem:
            
            mock_zcard.return_value = 0  # No existing requests
            
            # Test allowing request
            allowed = await rate_limiter.is_allowed("test_key", 100, 60)
            assert allowed is True
            
            # Verify Redis calls
            mock_zrem.assert_called_once()
            mock_zadd.assert_called_once()
            mock_zcard.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__]) 