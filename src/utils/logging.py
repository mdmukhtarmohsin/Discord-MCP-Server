"""Logging configuration for the MCP Discord Server."""

import sys
import logging
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory

try:
    # Try relative import first
    from ..models.settings import settings
except ImportError:
    # Fall back to absolute import for standalone testing
    try:
        from models.settings import settings
    except ImportError:
        # Create a mock settings object for testing
        class MockSettings:
            log_level = "INFO"
            log_format = "console"
        settings = MockSettings()


def setup_logging():
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    
    # Configure processors based on format
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    if settings.log_format.lower() == "json":
        processors.extend([
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.JSONRenderer()
        ])
    else:
        processors.extend([
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_api_access(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        **kwargs
    ):
        """Log API access events."""
        self.logger.info(
            "API access",
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            **kwargs
        )
    
    def log_discord_action(
        self,
        action: str,
        user_id: str,
        guild_id: str = None,
        channel_id: str = None,
        target_id: str = None,
        success: bool = True,
        **kwargs
    ):
        """Log Discord actions."""
        self.logger.info(
            "Discord action",
            action=action,
            user_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id,
            target_id=target_id,
            success=success,
            **kwargs
        )
    
    def log_authentication(
        self,
        user_id: str,
        success: bool,
        reason: str = None,
        **kwargs
    ):
        """Log authentication events."""
        level = "info" if success else "warning"
        getattr(self.logger, level)(
            "Authentication attempt",
            user_id=user_id,
            success=success,
            reason=reason,
            **kwargs
        )


# Global audit logger instance
audit_logger = AuditLogger() 