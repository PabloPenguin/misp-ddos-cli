"""
Configuration Module

Secure configuration loading from environment variables.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Config:
    """
    Application configuration loaded from environment variables.
    
    Security:
        - API keys are never logged
        - Environment variables are validated
        - Secure defaults are used where appropriate
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file (defaults to .env in current dir)
        
        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        # Load .env file if it exists
        if env_file:
            env_path = Path(env_file)
            if not env_path.exists():
                raise ConfigurationError(f".env file not found: {env_file}")
            load_dotenv(env_path)
        else:
            # Try to load .env from current directory
            load_dotenv()
        
        # Required configuration
        self.misp_url = self._get_required("MISP_URL")
        self.misp_api_key = self._get_required("MISP_API_KEY")
        
        # Optional configuration with defaults
        self.misp_verify_ssl = self._get_bool("MISP_VERIFY_SSL", default=True)
        self.misp_timeout = self._get_int("MISP_TIMEOUT", default=30)
        self.misp_max_retries = self._get_int("MISP_MAX_RETRIES", default=3)
        
        # Logging configuration
        self.log_level = self._get_optional("LOG_LEVEL", default="INFO")
        self.log_file = self._get_optional("LOG_FILE", default=None)
        
        # Validate configuration
        self._validate()
        
        logger.info(
            "Configuration loaded",
            extra={
                "misp_url": self.misp_url,
                "verify_ssl": self.misp_verify_ssl,
                "timeout": self.misp_timeout,
                "max_retries": self.misp_max_retries,
                "log_level": self.log_level
            }
        )
    
    def _get_required(self, key: str) -> str:
        """
        Get required environment variable.
        
        Args:
            key: Environment variable name
        
        Returns:
            Environment variable value
        
        Raises:
            ConfigurationError: If variable is not set
        """
        value = os.environ.get(key)
        if not value:
            raise ConfigurationError(
                f"Required environment variable '{key}' is not set. "
                f"Please set it in your .env file or environment."
            )
        return value.strip()
    
    def _get_optional(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get optional environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
        
        Returns:
            Environment variable value or default
        """
        value = os.environ.get(key)
        return value.strip() if value else default
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
        
        Returns:
            Boolean value
        """
        value = os.environ.get(key)
        if not value:
            return default
        
        value_lower = value.strip().lower()
        if value_lower in ("true", "1", "yes", "on"):
            return True
        elif value_lower in ("false", "0", "no", "off"):
            return False
        else:
            logger.warning(
                f"Invalid boolean value for {key}: {value}. Using default: {default}"
            )
            return default
    
    def _get_int(self, key: str, default: int = 0) -> int:
        """
        Get integer environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not set
        
        Returns:
            Integer value
        """
        value = os.environ.get(key)
        if not value:
            return default
        
        try:
            return int(value.strip())
        except ValueError:
            logger.warning(
                f"Invalid integer value for {key}: {value}. Using default: {default}"
            )
            return default
    
    def _validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ConfigurationError: If validation fails
        """
        # Validate MISP URL
        if not self.misp_url.startswith(("http://", "https://")):
            raise ConfigurationError(
                f"MISP_URL must start with http:// or https://, got: {self.misp_url}"
            )
        
        # Validate API key (basic check)
        if len(self.misp_api_key) < 10:
            raise ConfigurationError(
                "MISP_API_KEY appears to be invalid (too short)"
            )
        
        # Validate timeout
        if self.misp_timeout <= 0:
            raise ConfigurationError(
                f"MISP_TIMEOUT must be positive, got: {self.misp_timeout}"
            )
        
        # Validate max retries
        if self.misp_max_retries < 0:
            raise ConfigurationError(
                f"MISP_MAX_RETRIES must be non-negative, got: {self.misp_max_retries}"
            )
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            logger.warning(
                f"Invalid LOG_LEVEL: {self.log_level}. Using INFO. "
                f"Valid levels: {valid_log_levels}"
            )
            self.log_level = "INFO"


def setup_logging(config: Config) -> None:
    """
    Configure logging based on configuration.
    
    Args:
        config: Application configuration
    """
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(message)s [%(filename)s:%(lineno)d]"
    )
    
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    handlers.append(console_handler)
    
    # File handler if specified
    if config.log_file:
        try:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)
        except Exception as e:
            logger.warning(f"Failed to create log file {config.log_file}: {e}")
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        handlers=handlers,
        force=True
    )
    
    # Suppress verbose third-party logging
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
