"""Rate limiting functionality for API endpoints."""

import time
from typing import Optional, Dict, Any
import redis
import structlog

from ..models.settings import settings

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Redis-based rate limiter for API endpoints."""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.redis_url,
            db=settings.redis_db,
            decode_responses=True
        )
    
    async def is_allowed(
        self,
        key: str,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> bool:
        """Check if request is allowed based on rate limits."""
        
        limit = limit or settings.rate_limit_requests
        window = window or settings.rate_limit_window
        
        try:
            # Use Redis sliding window log algorithm
            now = time.time()
            pipeline = self.redis_client.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(now): now})
            
            # Set expiration
            pipeline.expire(key, window)
            
            results = pipeline.execute()
            request_count = results[1]
            
            allowed = request_count < limit
            
            if not allowed:
                logger.warning(
                    "Rate limit exceeded",
                    key=key,
                    count=request_count,
                    limit=limit,
                    window=window
                )
            
            return allowed
            
        except Exception as e:
            logger.error("Rate limiting error", error=str(e))
            # On error, allow the request to proceed
            return True
    
    async def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get current rate limit information for a key."""
        try:
            window = settings.rate_limit_window
            now = time.time()
            
            # Get current request count
            count = self.redis_client.zcount(key, now - window, now)
            
            # Get oldest request in window
            oldest_requests = self.redis_client.zrange(key, 0, 0, withscores=True)
            
            reset_time = None
            if oldest_requests:
                oldest_time = oldest_requests[0][1]
                reset_time = int(oldest_time + window)
            
            return {
                "limit": settings.rate_limit_requests,
                "remaining": max(0, settings.rate_limit_requests - count),
                "reset": reset_time,
                "window": window
            }
            
        except Exception as e:
            logger.error("Failed to get rate limit info", error=str(e))
            return {
                "limit": settings.rate_limit_requests,
                "remaining": settings.rate_limit_requests,
                "reset": None,
                "window": settings.rate_limit_window
            }
    
    async def reset_rate_limit(self, key: str) -> bool:
        """Reset rate limit for a specific key."""
        try:
            self.redis_client.delete(key)
            logger.info("Rate limit reset", key=key)
            return True
        except Exception as e:
            logger.error("Failed to reset rate limit", key=key, error=str(e))
            return False
    
    def create_rate_limit_key(
        self,
        prefix: str,
        identifier: str,
        endpoint: Optional[str] = None
    ) -> str:
        """Create a consistent rate limit key."""
        parts = [prefix, identifier]
        if endpoint:
            parts.append(endpoint)
        return ":".join(parts)


# Global rate limiter instance
rate_limiter = RateLimiter() 