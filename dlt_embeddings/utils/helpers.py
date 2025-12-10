"""Helper functions for data loading pipelines."""

import logging
import os
import sys
import types
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
    from loguru import logger as _loguru_logger_import
    from rich.console import Console as _Console_import
    from rich.logging import RichHandler as _RichHandler_import

    loguru_logger: Optional[Any] = _loguru_logger_import
    Console: Optional[Any] = _Console_import
    RichHandler: Any = _RichHandler_import

    LOGURU_AVAILABLE = True
    RICH_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False
    RICH_AVAILABLE = False
    loguru_logger = None
    RichHandler = logging.StreamHandler  # Fallback to standard handler
    Console = None


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and route them to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to loguru."""
        if not LOGURU_AVAILABLE:
            return

        # Get the corresponding Loguru level if it exists
        if loguru_logger is None:
            return
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            # Map standard logging levels to loguru levels
            level_map = {
                logging.CRITICAL: "CRITICAL",
                logging.ERROR: "ERROR",
                logging.WARNING: "WARNING",
                logging.INFO: "INFO",
                logging.DEBUG: "DEBUG",
            }
            level = level_map.get(record.levelno, "INFO")

        # Find the caller from where the logged message originated
        current_frame: Optional[types.FrameType] = sys._getframe(6)
        depth = 6
        while current_frame is not None and current_frame.f_code.co_filename == logging.__file__:
            current_frame = current_frame.f_back
            depth += 1

        if loguru_logger is not None:
            loguru_logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )


class DLTStderrInterceptor:
    """Intercept DLT's stderr output and route through loguru."""

    def __init__(self):
        self.original_stderr = sys.stderr
        self.buffer = ""

    def write(self, text):
        """Intercept writes to stderr and parse DLT's format."""
        if not LOGURU_AVAILABLE:
            self.original_stderr.write(text)
            return

        # DLT format: timestamp|[LEVEL]|PID|thread|module|file|function:line|message
        # Example: 2025-12-03 12:32:26,895|[WARNING]|60765|8581685760|dlt_project|config_loader.py|__init__:32|message
        # Check if this looks like a DLT log message
        if "|[" in text and "|" in text:
            try:
                # Split by | to parse
                parts = text.split("|")

                # Find the level part (starts with [)
                level_str = None
                level_idx = None
                for i, part in enumerate(parts):
                    if part.startswith("[") and part.endswith("]"):
                        level_str = part.strip("[]")
                        level_idx = i
                        break

                if level_str and level_idx is not None:
                    # Message is everything after the metadata (typically after 6-7 pipes)
                    # Format: timestamp|[LEVEL]|PID|thread|module|file|function:line|message
                    message_start = (
                        level_idx + 5
                    )  # Skip level, PID, thread, module, file, function:line
                    if len(parts) > message_start:
                        message = "|".join(parts[message_start:]).strip()
                    else:
                        # Fallback: take everything after level
                        message = "|".join(parts[level_idx + 1 :]).strip()

                    if message:
                        # Map DLT levels to loguru levels
                        level_map = {
                            "DEBUG": "DEBUG",
                            "INFO": "INFO",
                            "WARNING": "WARNING",
                            "ERROR": "ERROR",
                            "CRITICAL": "CRITICAL",
                        }
                        loguru_level = level_map.get(level_str.upper(), "INFO")

                        # Log through loguru (which uses RichHandler)
                        if loguru_logger is not None:
                            loguru_logger.log(loguru_level, message)
                        return
            except Exception:
                # If parsing fails, fall through to write original
                pass

        # Not a DLT log or parsing failed - write to original stderr
        self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()


_dlt_stderr_interceptor = None


def _configure_dlt_custom_logger():
    """Configure DLT's custom logger to route through our Rich formatting."""
    global _dlt_stderr_interceptor

    if not LOGURU_AVAILABLE:
        return

    try:
        # Intercept stderr to catch DLT's direct writes
        if _dlt_stderr_interceptor is None:
            _dlt_stderr_interceptor = DLTStderrInterceptor()
            sys.stderr = _dlt_stderr_interceptor
    except Exception:
        # If interception fails, continue without it
        pass


def load_env_vars(env_file: Optional[str] = None) -> None:
    """Load environment variables from .env file."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
        if not os.getenv("REDSHIFT_HOST"):
            parent_env = Path(__file__).parent.parent.parent / ".env"
            if parent_env.exists():
                load_dotenv(parent_env)


def get_redshift_credentials() -> Dict[str, Any]:
    """Get Redshift credentials from environment variables."""
    load_env_vars()

    return {
        "database": os.getenv("REDSHIFT_DB_NAME", "dev"),
        "username": os.getenv("REDSHIFT_USER_NAME"),
        "password": os.getenv("REDSHIFT_USER_PASS"),
        "host": os.getenv("REDSHIFT_HOST"),
        "port": int(os.getenv("REDSHIFT_PORT", "5439")),
    }


def get_aws_credentials() -> Dict[str, Any]:
    """Get AWS credentials from environment variables."""
    load_env_vars()

    return {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region_name": os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "eu-west-1")),
    }


def get_s3_config() -> Dict[str, Any]:
    """Get S3 configuration from environment variables."""
    load_env_vars()

    return {
        "bucket_name": os.getenv("S3_SAGEMAKER_BUCKET") or os.getenv("S3_BUCKET_NAME"),
        "prefix": os.getenv("S3_SAGEMAKER_PREFIX", "log/"),
        **get_aws_credentials(),
    }


def validate_credentials(credentials: Dict[str, Any]) -> bool:
    """Validate that all required credentials are present."""
    required_keys = ["database", "username", "password", "host", "port"]
    missing = [key for key in required_keys if not credentials.get(key)]

    if missing:
        raise ValueError(f"Missing required credentials: {', '.join(missing)}")

    return True


def setup_logger(level: str = "INFO", show_dlt_logs: bool = False, log_file: Optional[str] = None):
    """
    Set up logging with Rich formatting.

    Args:
        level: Log level (e.g., "INFO", "DEBUG", "WARNING")
        show_dlt_logs: If True, show DLT's internal logs (usually very verbose)
        log_file: Optional path to log file. If provided, logs will be written to file
                  in addition to console. Format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"

    Returns:
        Configured loguru logger instance
    """
    if not LOGURU_AVAILABLE or not RICH_AVAILABLE:
        # Fallback to basic logging if rich/loguru not available
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)s | %(message)s",
        )
        return None

    # Configure loguru with Rich
    if loguru_logger is not None and Console is not None and RichHandler is not None:
        loguru_logger.remove()  # Remove default handler
        loguru_logger.add(
            RichHandler(
                console=Console(
                    stderr=True, force_terminal=True, force_interactive=True, no_color=False
                ),
                show_time=True,
                show_level=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True,
            ),
            format="{message}",
            level=level,
        )

    # Add file handler if log_file is provided
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Add file handler with structured format for easy parsing
        if loguru_logger is not None:
            loguru_logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                level=level,
                rotation="10 MB",  # Rotate when file reaches 10MB
                retention="30 days",  # Keep logs for 30 days
                compression="zip",  # Compress old logs
                enqueue=True,  # Thread-safe logging
            )

    # Set up stderr interceptor BEFORE configuring DLT loggers
    # This must happen early to catch DLT's direct stderr writes
    _configure_dlt_custom_logger()

    # Configure DLT logging to route through loguru using InterceptHandler
    if show_dlt_logs:
        # Set DLT to INFO level
        dlt_level = getattr(logging, level.upper(), logging.INFO)
    else:
        # Set DLT to WARNING (only show warnings/errors)
        dlt_level = logging.WARNING

    # Try to configure DLT's custom logger first
    _configure_dlt_custom_logger()

    # Configure all DLT loggers to use InterceptHandler (routes through loguru)
    dlt_logger_names = [
        "dlt",
        "dlt.common",
        "dlt.pipeline",
        "dlt.normalize",
        "dlt.load",
        "dlt.extract",
        "dlt.destinations",
        "dlt.destinations.redshift",
    ]

    for logger_name in dlt_logger_names:
        dlt_logger = logging.getLogger(logger_name)
        dlt_logger.handlers.clear()
        dlt_logger.propagate = False
        dlt_logger.setLevel(dlt_level)
        # Use InterceptHandler to route through loguru (which uses RichHandler)
        dlt_logger.addHandler(InterceptHandler())

    # Ensure stderr interceptor is active (in case it wasn't set up earlier)
    _configure_dlt_custom_logger()

    return loguru_logger


def setup_minimal_dlt_logging(level: str = "ERROR"):
    """
    Minimal DLT logging - only show errors.
    Recommended for production use with progress bars.

    Args:
        level: Minimum log level to show (default: ERROR)

    Returns:
        Configured loguru logger instance or None
    """
    if not LOGURU_AVAILABLE or not RICH_AVAILABLE:
        return None

    # Configure loguru with Rich
    if loguru_logger is not None and Console is not None and RichHandler is not None:
        loguru_logger.remove()
        loguru_logger.add(
            RichHandler(
                console=Console(
                    stderr=True, force_terminal=True, force_interactive=True, no_color=False
                ),
                show_time=True,
                show_level=True,
                show_path=False,
                markup=True,
            ),
            format="{message}",
            level="INFO",  # Your logs at INFO
        )

    # Set DLT to only show errors
    error_level = getattr(logging, level.upper(), logging.ERROR)

    for logger_name in ["dlt", "dlt.common", "dlt.pipeline", "dlt.normalize", "dlt.load"]:
        dlt_logger = logging.getLogger(logger_name)
        dlt_logger.handlers.clear()
        dlt_logger.propagate = False
        dlt_logger.setLevel(error_level)
        # Use InterceptHandler to route through loguru
        dlt_logger.addHandler(InterceptHandler())

    return loguru_logger


def reconfigure_dlt_loggers(level: str = "WARNING"):
    """
    Reconfigure DLT loggers after DLT has initialized.
    Call this AFTER creating dlt.pipeline() if logs are still showing.

    Args:
        level: Log level for DLT (default: WARNING)
    """
    if not LOGURU_AVAILABLE:
        return

    dlt_level = getattr(logging, level.upper(), logging.WARNING)

    # Try to configure DLT's custom logger
    _configure_dlt_custom_logger()

    # Find all DLT loggers dynamically
    root = logging.root
    dlt_logger_names = ["dlt"]  # Start with main logger

    # Find all loggers that start with "dlt"
    for logger_name in root.manager.loggerDict.keys():
        if logger_name.startswith("dlt") and logger_name not in dlt_logger_names:
            dlt_logger_names.append(logger_name)

    # Also ensure common ones are included
    known_loggers = [
        "dlt.common",
        "dlt.pipeline",
        "dlt.normalize",
        "dlt.load",
        "dlt.extract",
        "dlt.destinations",
        "dlt.destinations.redshift",
    ]
    for logger_name in known_loggers:
        if logger_name not in dlt_logger_names:
            dlt_logger_names.append(logger_name)

    for logger_name in dlt_logger_names:
        dlt_logger = logging.getLogger(logger_name)
        # Clear ALL handlers (DLT might add multiple)
        dlt_logger.handlers.clear()
        dlt_logger.propagate = False
        dlt_logger.setLevel(dlt_level)
        # Use InterceptHandler to route through loguru (which uses RichHandler)
        dlt_logger.addHandler(InterceptHandler())
