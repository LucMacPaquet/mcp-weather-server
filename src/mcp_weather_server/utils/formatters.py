"""Formatting utilities for weather data and responses.

This module provides functions to format weather data and responses
in a structured and readable format for MCP clients.
"""

from typing import Any, Dict
from datetime import datetime, date

from ..models import CurrentWeather, Forecast, DailyForecast, WeatherError
from .errors import WeatherServiceError, LocationNotFoundError, RateLimitError, APIError


def format_success_response(data: CurrentWeather | Forecast) -> Dict[str, Any]:
    """Format a successful weather data response.
    
    Args:
        data: Weather data (CurrentWeather or Forecast)
        
    Returns:
        A structured dictionary with formatted weather data
    """
    if isinstance(data, CurrentWeather):
        return _format_current_weather(data)
    elif isinstance(data, Forecast):
        return _format_forecast(data)
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")


def format_error_response(
    error_type: str,
    message: str,
    details: str | None = None
) -> Dict[str, Any]:
    """Format an error response.
    
    Args:
        error_type: Type of error (e.g., "invalid_location", "api_error")
        message: Error message
        details: Optional additional error details
        
    Returns:
        A structured dictionary with error information
    """
    error = WeatherError(
        error_type=error_type,
        message=message,
        details=details
    )
    
    return {
        "error": True,
        "error_type": error.error_type,
        "message": error.message,
        "details": error.details
    }


def format_exception_response(exception: Exception) -> Dict[str, Any]:
    """Format an exception into an error response.
    
    Args:
        exception: The exception to format
        
    Returns:
        A structured dictionary with error information
    """
    if isinstance(exception, LocationNotFoundError):
        return format_error_response(
            error_type="invalid_location",
            message=exception.message,
            details=exception.details
        )
    elif isinstance(exception, RateLimitError):
        return format_error_response(
            error_type="rate_limit",
            message=exception.message,
            details=exception.details
        )
    elif isinstance(exception, APIError):
        return format_error_response(
            error_type="api_error",
            message=exception.message,
            details=exception.details
        )
    elif isinstance(exception, WeatherServiceError):
        return format_error_response(
            error_type="service_error",
            message=exception.message,
            details=exception.details
        )
    else:
        return format_error_response(
            error_type="internal_error",
            message="An unexpected error occurred",
            details=str(exception)
        )


def _format_current_weather(weather: CurrentWeather) -> Dict[str, Any]:
    """Format current weather data into a readable structure.
    
    Args:
        weather: CurrentWeather model instance
        
    Returns:
        A formatted dictionary with current weather information
    """
    return {
        "location": weather.location,
        "coordinates": {
            "latitude": weather.coordinates.latitude,
            "longitude": weather.coordinates.longitude
        },
        "timestamp": _format_datetime(weather.timestamp),
        "current": {
            "temperature": _format_temperature(weather.temperature),
            "feels_like": _format_temperature(weather.feels_like),
            "conditions": weather.conditions,
            "description": weather.description,
            "humidity": f"{weather.humidity}%",
            "pressure": f"{weather.pressure} hPa",
            "wind": {
                "speed": _format_wind_speed(weather.wind_speed),
                "direction": _format_wind_direction(weather.wind_direction)
            },
            "visibility": _format_visibility(weather.visibility),
            "uv_index": _format_uv_index(weather.uv_index),
            "clouds": f"{weather.clouds}%"
        },
        "sun": {
            "sunrise": _format_time(weather.sunrise),
            "sunset": _format_time(weather.sunset)
        }
    }


def _format_forecast(forecast: Forecast) -> Dict[str, Any]:
    """Format forecast data into a readable structure.
    
    Args:
        forecast: Forecast model instance
        
    Returns:
        A formatted dictionary with forecast information
    """
    return {
        "location": forecast.location,
        "coordinates": {
            "latitude": forecast.coordinates.latitude,
            "longitude": forecast.coordinates.longitude
        },
        "forecast": [_format_daily_forecast(day) for day in forecast.daily]
    }


def _format_daily_forecast(day: DailyForecast) -> Dict[str, Any]:
    """Format a single day's forecast data.
    
    Args:
        day: DailyForecast model instance
        
    Returns:
        A formatted dictionary with daily forecast information
    """
    return {
        "date": _format_date(day.date),
        "temperature": {
            "min": _format_temperature(day.temp_min),
            "max": _format_temperature(day.temp_max),
            "day": _format_temperature(day.temp_day),
            "feels_like": _format_temperature(day.feels_like_day)
        },
        "conditions": day.conditions,
        "description": day.description,
        "precipitation_probability": f"{int(day.precipitation_probability * 100)}%",
        "humidity": f"{day.humidity}%",
        "wind_speed": _format_wind_speed(day.wind_speed),
        "uv_index": _format_uv_index(day.uv_index)
    }


def _format_temperature(temp: float) -> str:
    """Format temperature value.
    
    Args:
        temp: Temperature in degrees
        
    Returns:
        Formatted temperature string
    """
    return f"{temp:.1f}°C"


def _format_wind_speed(speed: float) -> str:
    """Format wind speed value.
    
    Args:
        speed: Wind speed in m/s
        
    Returns:
        Formatted wind speed string
    """
    # Convert m/s to km/h
    kmh = speed * 3.6
    return f"{kmh:.1f} km/h"


def _format_wind_direction(degrees: int) -> str:
    """Format wind direction from degrees to cardinal direction.
    
    Args:
        degrees: Wind direction in degrees (0-360)
        
    Returns:
        Cardinal direction (N, NE, E, SE, S, SW, W, NW)
    """
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int((degrees + 22.5) / 45) % 8
    return f"{degrees}° ({directions[index]})"


def _format_visibility(meters: int) -> str:
    """Format visibility value.
    
    Args:
        meters: Visibility in meters
        
    Returns:
        Formatted visibility string
    """
    if meters >= 1000:
        km = meters / 1000
        return f"{km:.1f} km"
    return f"{meters} m"


def _format_uv_index(uv: float) -> str:
    """Format UV index with risk level.
    
    Args:
        uv: UV index value
        
    Returns:
        Formatted UV index string with risk level
    """
    if uv < 3:
        level = "Low"
    elif uv < 6:
        level = "Moderate"
    elif uv < 8:
        level = "High"
    elif uv < 11:
        level = "Very High"
    else:
        level = "Extreme"
    
    return f"{uv:.1f} ({level})"


def _format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 string.
    
    Args:
        dt: Datetime object
        
    Returns:
        ISO 8601 formatted datetime string
    """
    return dt.isoformat()


def _format_date(d: date) -> str:
    """Format date to ISO 8601 string.
    
    Args:
        d: Date object
        
    Returns:
        ISO 8601 formatted date string
    """
    return d.isoformat()


def _format_time(dt: datetime) -> str:
    """Format datetime to time string (HH:MM).
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted time string
    """
    return dt.strftime("%H:%M")
