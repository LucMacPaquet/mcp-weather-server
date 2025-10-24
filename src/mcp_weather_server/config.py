"""Configuration module for MCP Weather Server.

This module handles loading and validating environment variables,
and provides configuration constants for the application.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# API configuration
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "13ced4f0f05a4a4f986223827252410")

# WeatherAPI.com endpoints
WEATHERAPI_BASE_URL = "https://api.weatherapi.com/v1"
CURRENT_ENDPOINT = f"{WEATHERAPI_BASE_URL}/current.json"
FORECAST_ENDPOINT = f"{WEATHERAPI_BASE_URL}/forecast.json"

# Default units
DEFAULT_UNITS = "metric"

# Forecast limits
MAX_FORECAST_DAYS = 8
MIN_FORECAST_DAYS = 1


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


def validate_api_key(api_key: Optional[str] = None) -> str:
    """Validate WeatherAPI.com API key.
    
    Args:
        api_key: Optional API key. If not provided, uses WEATHERAPI_KEY from environment.
        
    Returns:
        The validated API key.
        
    Raises:
        ConfigurationError: If the API key is missing.
    """
    key = api_key or WEATHERAPI_KEY
    
    if not key:
        raise ConfigurationError(
            "WEATHERAPI_KEY environment variable is not set. "
            "Using default key for testing."
        )
    
    logging.info("Using WeatherAPI.com")
    return key


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def validate_configuration() -> None:
    """Validate all required configuration at startup.
    
    Raises:
        ConfigurationError: If any required configuration is missing or invalid.
    """
    # Validate API key
    validate_api_key()
    
    # Validate timeout
    if API_TIMEOUT <= 0:
        raise ConfigurationError(
            f"API_TIMEOUT must be positive, got {API_TIMEOUT}"
        )
    
    logging.info("Configuration validated successfully")
