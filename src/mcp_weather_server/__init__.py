"""MCP Weather Server - A Model Context Protocol server for weather data.

This package provides a Model Context Protocol (MCP) server that exposes
weather data tools to MCP clients. It uses the OpenWeatherMap API to retrieve
current weather conditions and forecasts for any location worldwide.

Main Components:
    - WeatherMCPServer: The main MCP server implementation
    - WeatherService: Service for interacting with OpenWeatherMap API
    - Data Models: Pydantic models for weather data (CurrentWeather, Forecast, etc.)
    - Error Classes: Custom exceptions for error handling
    - Utilities: Formatting and helper functions

Example:
    >>> from mcp_weather_server import WeatherMCPServer
    >>> server = WeatherMCPServer(api_key="your_api_key")
    >>> await server.run()
"""

__version__ = "0.1.0"
__all__ = [
    # Main server
    "WeatherMCPServer",
    # Services
    "WeatherService",
    # Data models
    "CurrentWeather",
    "Forecast",
    "DailyForecast",
    "Coordinates",
    "WeatherError",
    # Error classes
    "WeatherServiceError",
    "LocationNotFoundError",
    "RateLimitError",
    "APIError",
    # Configuration
    "validate_api_key",
    "validate_configuration",
    "ConfigurationError",
]

# Main server and service
from mcp_weather_server.server import WeatherMCPServer
from mcp_weather_server.weather_service import WeatherService

# Data models
from mcp_weather_server.models import (
    CurrentWeather,
    Forecast,
    DailyForecast,
    Coordinates,
    WeatherError,
)

# Error classes
from mcp_weather_server.utils.errors import (
    WeatherServiceError,
    LocationNotFoundError,
    RateLimitError,
    APIError,
)

# Configuration
from mcp_weather_server.config import (
    validate_api_key,
    validate_configuration,
    ConfigurationError,
)
