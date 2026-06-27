"""
Centralized logging configuration for the application.
Provides structured logging with different levels for different environments.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return formatted


def setup_logging(
    app_name: str = "resume-optimizer",
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
):
    """
    Configure application logging with both console and file handlers.
    
    Args:
        app_name: Name of the application (used in log messages)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (None = no file logging)
    """
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()  # Remove any existing handlers
    
    # Console Handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(
        '%(levelname)s | %(asctime)s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler (if log_dir specified)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main log file (rotating)
        main_log = log_dir / f"{app_name}.log"
        file_handler = RotatingFileHandler(
            main_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(levelname)s | %(asctime)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Error log file (only errors and above)
        error_log = log_dir / f"{app_name}-errors.log"
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"resume-optimizer.{name}")


# Request logging middleware helper
def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    error: Optional[str] = None,
):
    """Log an HTTP request with relevant details."""
    extra_info = []
    
    if user_id:
        extra_info.append(f"user={user_id[:8]}")
    
    if error:
        extra_info.append(f"error={error}")
    
    extra_str = f" | {' | '.join(extra_info)}" if extra_info else ""
    
    if status_code >= 500:
        logger.error(f"{method} {path} → {status_code} ({duration_ms:.0f}ms){extra_str}")
    elif status_code >= 400:
        logger.warning(f"{method} {path} → {status_code} ({duration_ms:.0f}ms){extra_str}")
    else:
        logger.info(f"{method} {path} → {status_code} ({duration_ms:.0f}ms){extra_str}")


# Function timing decorator
def log_timing(logger: logging.Logger):
    """Decorator to log function execution time."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.debug(f"{func.__name__} completed in {duration:.0f}ms")
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(f"{func.__name__} failed after {duration:.0f}ms: {type(e).__name__}: {e}")
                raise
        
        def sync_wrapper(*args, **kwargs):
            import time
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.debug(f"{func.__name__} completed in {duration:.0f}ms")
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(f"{func.__name__} failed after {duration:.0f}ms: {type(e).__name__}: {e}")
                raise
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
