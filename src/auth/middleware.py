"""Authentication middleware for FastAPI."""

from typing import Optional, Callable, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from .security import verify_token
from .rate_limiter import rate_limiter
from ..models.auth import TokenData, PermissionLevel

logger = structlog.get_logger(__name__)

# Security scheme for FastAPI
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token."""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        
        return token_data
        
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise credentials_exception


def require_permission(required_permission: PermissionLevel):
    """Dependency factory for permission-based access control."""
    
    def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        
        from .security import check_permission
        
        if not check_permission(current_user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission.value}"
            )
        
        return current_user
    
    return permission_checker


def require_guild_access(guild_id: str):
    """Dependency factory for guild-specific access control."""
    
    def guild_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        
        if current_user.guild_ids and guild_id not in current_user.guild_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for guild: {guild_id}"
            )
        
        return current_user
    
    return guild_checker


def require_channel_access(channel_id: str):
    """Dependency factory for channel-specific access control."""
    
    def channel_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        
        if current_user.channel_ids and channel_id not in current_user.channel_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for channel: {channel_id}"
            )
        
        return current_user
    
    return channel_checker


async def rate_limit_middleware(request: Request, call_next):
    """Middleware for rate limiting requests."""
    
    # Extract user identifier from request
    user_id = "anonymous"
    auth_header = request.headers.get("authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        token_data = verify_token(token)
        if token_data:
            user_id = token_data.key_id or token_data.user_id or "anonymous"
    
    # Create rate limit key
    rate_limit_key = rate_limiter.create_rate_limit_key(
        "api",
        user_id,
        str(request.url.path)
    )
    
    # Check rate limit
    is_allowed = await rate_limiter.is_allowed(rate_limit_key)
    
    if not is_allowed:
        # Get rate limit info for headers
        rate_info = await rate_limiter.get_rate_limit_info(rate_limit_key)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": str(rate_info["reset"]) if rate_info["reset"] else "",
                "Retry-After": str(rate_info["window"])
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    rate_info = await rate_limiter.get_rate_limit_info(rate_limit_key)
    response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
    if rate_info["reset"]:
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
    
    return response


class AuthenticationManager:
    """Centralized authentication management."""
    
    def __init__(self):
        self.active_tokens: Dict[str, TokenData] = {}
    
    async def authenticate_request(self, request: Request) -> Optional[TokenData]:
        """Authenticate a request and return token data."""
        
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        return verify_token(token)
    
    async def log_authentication_event(
        self,
        token_data: Optional[TokenData],
        request: Request,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Log authentication events for auditing."""
        
        log_data = {
            "event": "authentication",
            "success": success,
            "endpoint": str(request.url.path),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
        }
        
        if token_data:
            log_data.update({
                "user_id": token_data.user_id,
                "key_id": token_data.key_id,
                "permissions": [p.value for p in token_data.permissions]
            })
        
        if error_message:
            log_data["error"] = error_message
        
        if success:
            logger.info("Authentication successful", **log_data)
        else:
            logger.warning("Authentication failed", **log_data)


# Global authentication manager
auth_manager = AuthenticationManager() 