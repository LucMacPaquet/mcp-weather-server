"""Handler for current weather tool.

This module implements the MCP tool handler for retrieving current weather
data for a specified location.
"""

import logging
from typing import Dict, Any

from ..weather_service import WeatherService
from ..utils.formatters import format_success_response, format_exception_response
from ..utils.errors import WeatherServiceError
from ..config import DEFAULT_UNITS

logger = logging.getLogger(__name__)


async def handle_current_weather(
    weather_service: WeatherService,
    location: str,
    units: str = DEFAULT_UNITS
) -> Dict[str, Any]:
    """Handle a request for current weather data.
    
    This function processes a current weather request by:
    1. Parsing and validating the location parameter (city name or "lat,lon")
    2. Converting city names to coordinates if needed
    3. Fetching current weather data from the weather service
    4. Formatting and returning the response
    
    Args:
        weather_service: WeatherService instance for API calls
        location: Location as city name (e.g., "Paris") or coordinates (e.g., "48.8566,2.3522")
        units: Unit system ("metric" or "imperial"), defaults to metric
        
    Returns:
        A formatted dictionary with current weather data or error information
        
    Examples:
        >>> await handle_current_weather(service, "Paris")
        >>> await handle_current_weather(service, "48.8566,2.3522")
        >>> await handle_current_weather(service, "London", units="imperial")
    """
    logger.info(f"Handling current weather request for location: {location}, units: {units}")
    
    try:
        # Validate units parameter
        units = units.lower().strip()
        if units not in ["metric", "imperial"]:
            return {
                "error": True,
                "error_type": "invalid_parameter",
                "message": f"Invalid units parameter: '{units}'",
                "details": "Units must be either 'metric' or 'imperial'"
            }
        
        # Parse location parameter
        lat, lon, location_name = await _parse_location(weather_service, location)
        
        # Fetch current weather data
        current_weather = await weather_service.get_current_weather(lat, lon, units)
        
        # Update location name in the response
        current_weather.location = location_name
        
        # Format and return success response
        response = format_success_response(current_weather)
        logger.info(f"Successfully retrieved current weather for {location_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error handling current weather request: {e}")
        return format_exception_response(e)


async def _parse_location(
    weather_service: WeatherService,
    location: str
) -> tuple[float, float, str]:
    """Parse location parameter and return coordinates and location name.
    
    Handles two formats:
    1. City name: "Paris", "London,UK", "New York,NY,US"
    2. Coordinates: "48.8566,2.3522" (lat,lon)
    
    Args:
        weather_service: WeatherService instance for geocoding
        location: Location string to parse
        
    Returns:
        A tuple of (latitude, longitude, location_name)
        
    Raises:
        ValueError: If the location format is invalid
        LocationNotFoundError: If the city name cannot be geocoded
    """
    location = location.strip()
    
    if not location:
        raise ValueError("Location parameter cannot be empty")
    
    # Check if location is in coordinate format (lat,lon)
    if _is_coordinate_format(location):
        lat, lon = _parse_coordinates(location)
        location_name = f"{lat}, {lon}"
        logger.debug(f"Parsed coordinates: lat={lat}, lon={lon}")
        return lat, lon, location_name
    
    # Otherwise, treat as city name and geocode
    logger.debug(f"Geocoding city name: {location}")
    coordinates = await weather_service.geocode_location(location)
    return coordinates.latitude, coordinates.longitude, location


def _is_coordinate_format(location: str) -> bool:
    """Check if location string is in coordinate format (lat,lon).
    
    Args:
        location: Location string to check
        
    Returns:
        True if the location appears to be coordinates, False otherwise
    """
    # Simple heuristic: if it contains a comma and both parts are numeric
    if "," not in location:
        return False
    
    parts = location.split(",")
    if len(parts) != 2:
        return False
    
    try:
        float(parts[0].strip())
        float(parts[1].strip())
        return True
    except ValueError:
        return False


def _parse_coordinates(location: str) -> tuple[float, float]:
    """Parse coordinate string into latitude and longitude.
    
    Args:
        location: Coordinate string in format "lat,lon"
        
    Returns:
        A tuple of (latitude, longitude)
        
    Raises:
        ValueError: If the coordinate format is invalid or values are out of range
    """
    parts = location.split(",")
    
    if len(parts) != 2:
        raise ValueError(
            f"Invalid coordinate format: '{location}'. "
            "Expected format: 'latitude,longitude' (e.g., '48.8566,2.3522')"
        )
    
    try:
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
    except ValueError as e:
        raise ValueError(
            f"Invalid coordinate values: '{location}'. "
            "Latitude and longitude must be numeric values."
        ) from e
    
    # Validate coordinate ranges
    if not -90 <= lat <= 90:
        raise ValueError(
            f"Invalid latitude: {lat}. Latitude must be between -90 and 90 degrees."
        )
    
    if not -180 <= lon <= 180:
        raise ValueError(
            f"Invalid longitude: {lon}. Longitude must be between -180 and 180 degrees."
        )
    
    return lat, lon
