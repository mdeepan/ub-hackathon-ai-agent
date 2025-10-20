"""
Application configuration management for the Personal Learning Agent.

This module provides centralized configuration management with environment
variable loading, validation, and default value handling.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with environment variable support and validation.
    """
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    openai_temperature: float = Field(default=0.7, description="OpenAI temperature setting")
    openai_max_tokens: int = Field(default=2000, description="Maximum tokens for OpenAI responses")
    openai_timeout: int = Field(default=30, description="OpenAI API timeout in seconds")
    
    # Database Configuration
    database_path: str = Field(default="data/sqlite/pla.db", description="SQLite database path")
    chroma_path: str = Field(default="data/chroma", description="ChromaDB storage path")
    data_dir: str = Field(default="data", description="Base data directory")
    
    # Application Configuration
    app_name: str = Field(default="Personal Learning Agent", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    # LangChain Configuration
    langchain_verbose: bool = Field(default=False, description="LangChain verbose mode")
    langchain_tracing: bool = Field(default=False, description="LangChain tracing enabled")
    
    @field_validator('openai_temperature')
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    @field_validator('openai_max_tokens')
    @classmethod
    def validate_max_tokens(cls, v):
        """Validate max tokens is positive."""
        if v <= 0:
            raise ValueError('Max tokens must be positive')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @field_validator('api_port')
    @classmethod
    def validate_api_port(cls, v):
        """Validate API port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError('API port must be between 1 and 65535')
        return v
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


class ConfigManager:
    """
    Configuration manager with singleton pattern and environment loading.
    """
    
    _instance: Optional['ConfigManager'] = None
    _settings: Optional[Settings] = None
    
    def __new__(cls) -> 'ConfigManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager."""
        if self._settings is None:
            self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from environment and .env file."""
        try:
            # Ensure .env file exists in project root
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
            
            if not env_file.exists():
                logger.warning(f".env file not found at {env_file}. Using environment variables only.")
            
            self._settings = Settings(_env_file=str(env_file) if env_file.exists() else None)
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def get_settings(self) -> Settings:
        """
        Get the current settings instance.
        
        Returns:
            Settings: Current settings instance
        """
        if self._settings is None:
            self._load_settings()
        return self._settings
    
    def reload_settings(self) -> None:
        """Reload settings from environment and .env file."""
        self._settings = None
        self._load_settings()
        logger.info("Configuration reloaded")
    
    def get_openai_config(self) -> Dict[str, Any]:
        """
        Get OpenAI-specific configuration.
        
        Returns:
            dict: OpenAI configuration parameters
        """
        settings = self.get_settings()
        return {
            'api_key': settings.openai_api_key,
            'model': settings.openai_model,
            'temperature': settings.openai_temperature,
            'max_tokens': settings.openai_max_tokens,
            'timeout': settings.openai_timeout
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database-specific configuration.
        
        Returns:
            dict: Database configuration parameters
        """
        settings = self.get_settings()
        return {
            'database_path': settings.database_path,
            'chroma_path': settings.chroma_path
        }
    
    def get_langchain_config(self) -> Dict[str, Any]:
        """
        Get LangChain-specific configuration.
        
        Returns:
            dict: LangChain configuration parameters
        """
        settings = self.get_settings()
        return {
            'verbose': settings.langchain_verbose,
            'tracing': settings.langchain_tracing
        }
    
    def is_debug_mode(self) -> bool:
        """
        Check if debug mode is enabled.
        
        Returns:
            bool: True if debug mode is enabled
        """
        return self.get_settings().debug
    
    def get_log_level(self) -> str:
        """
        Get the current log level.
        
        Returns:
            str: Current log level
        """
        return self.get_settings().log_level


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager: Global configuration instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_settings() -> Settings:
    """
    Get the current settings instance.
    
    Returns:
        Settings: Current settings instance
    """
    return get_config().get_settings()


def reload_config() -> None:
    """Reload configuration from environment and .env file."""
    get_config().reload_settings()


def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.
    
    Returns:
        bool: True if all required variables are set, False otherwise
    """
    try:
        settings = get_settings()
        required_vars = ['openai_api_key']
        
        missing_vars = []
        for var in required_vars:
            if not getattr(settings, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        logger.info("Environment validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Environment validation failed: {e}")
        return False


def setup_logging() -> None:
    """Setup logging configuration based on settings."""
    config = get_config()
    log_level = getattr(logging, config.get_log_level())
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific logger levels
    if config.is_debug_mode():
        logging.getLogger('langchain').setLevel(logging.DEBUG)
        logging.getLogger('openai').setLevel(logging.DEBUG)
    else:
        logging.getLogger('langchain').setLevel(logging.INFO)
        logging.getLogger('openai').setLevel(logging.WARNING)
    
    logger.info(f"Logging configured with level: {config.get_log_level()}")


# Initialize logging when module is imported
setup_logging()
