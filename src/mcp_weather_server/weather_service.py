"""Weather service for interacting with OpenWeatherMap API.

This module provides the WeatherService class that handles all interactions
with the OpenWeatherMap API, including geocoding, current weather retrieval,
and forecast data.
"""

import logging
from datetime import datetime, date, timezone
from typing import List, Tuple
import httpx

from .models import Coordinates, CurrentWeather, DailyForecast, Forecast
from .config import (
    CURRENT_ENDPOINT,
    FORECAST_ENDPOINT,
    API_TIMEOUT,
    DEFAULT_UNITS,
)
from .utils.errors import (
    LocationNotFoundError,
    RateLimitError,
    APIError,
    WeatherServiceError,
)

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for retrieving weather data from OpenWeatherMap API.
    
    This class encapsulates all interactions with the OpenWeatherMap API,
    including geocoding location names to coordinates, fetching current
    weather data, and retrieving weather forecasts.
    """
    
    def __init__(self, api_key: str, http_client: httpx.AsyncClient | None = None):
        """Initialize the weather service.
        
        Args:
            api_key: WeatherAPI.com API key for authentication
            http_client: Optional httpx AsyncClient. If not provided, a new one will be created.
        """
        self.api_key = api_key
        
        if http_client is None:
            self.http_client = httpx.AsyncClient(
                timeout=API_TIMEOUT,
                headers={
                    "User-Agent": "MCP-Weather-Server/0.1.0",
                    "Accept": "application/json",
                }
            )
            self._owns_client = True
        else:
            self.http_client = http_client
            self._owns_client = False
    
    async def close(self) -> None:
        """Close the HTTP client if owned by this service."""
        if self._owns_client and self.http_client:
            await self.http_client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def geocode_location(self, location_name: str) -> Coordinates:
        """Convert a location name to geographic coordinates.
        
        WeatherAPI.com handles geocoding automatically, so this method
        fetches current weather to get the coordinates.
        
        Args:
            location_name: Name of the location (e.g., "Paris", "London", "New York")
            
        Returns:
            Coordinates object with latitude and longitude
            
        Raises:
            LocationNotFoundError: If the location cannot be found
            APIError: If the API request fails
        """
        logger.info(f"Geocoding location: {location_name}")
        
        try:
            response = await self.http_client.get(
                CURRENT_ENDPOINT,
                params={
                    "key": self.api_key,
                    "q": location_name,
                    "aqi": "no"
                }
            )
            
            self._handle_http_errors(response)
            
            data = response.json()
            location_data = data.get("location", {})
            
            if not location_data:
                raise LocationNotFoundError(
                    location_name,
                    "No results found. Please check the location name and try again."
                )
            
            coordinates = Coordinates(
                latitude=location_data["lat"],
                longitude=location_data["lon"]
            )
            
            logger.info(
                f"Geocoded '{location_name}' to coordinates: "
                f"({coordinates.latitude}, {coordinates.longitude})"
            )
            
            return coordinates
            
        except (LocationNotFoundError, APIError, RateLimitError):
            raise
        except httpx.TimeoutException:
            raise APIError(
                "Request timed out while geocoding location",
                details=f"The geocoding service did not respond within {API_TIMEOUT} seconds"
            )
        except httpx.RequestError as e:
            raise APIError(
                "Network error while geocoding location",
                details=str(e)
            )
        except Exception as e:
            logger.exception(f"Unexpected error geocoding location: {e}")
            raise WeatherServiceError(
                "Failed to geocode location",
                details=str(e)
            )

    async def get_current_weather(
        self,
        lat: float,
        lon: float,
        units: str = DEFAULT_UNITS
    ) -> CurrentWeather:
        """Get current weather data for specific coordinates.
        
        Retrieves current weather conditions from WeatherAPI.com.
        
        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            units: Unit system ("metric" or "imperial"), defaults to metric
            
        Returns:
            CurrentWeather object with all current weather data
            
        Raises:
            APIError: If the API request fails
            ValueError: If coordinates are invalid
        """
        logger.info(f"Fetching current weather for coordinates: ({lat}, {lon})")
        
        # Validate coordinates
        coordinates = Coordinates(latitude=lat, longitude=lon)
        
        try:
            response = await self.http_client.get(
                FORECAST_ENDPOINT,
                params={
                    "key": self.api_key,
                    "q": f"{lat},{lon}",
                    "days": 1,
                    "aqi": "no",
                    "alerts": "no"
                }
            )
            
            self._handle_http_errors(response)
            
            data = response.json()
            current = data.get("current", {})
            location = data.get("location", {})
            forecast = data.get("forecast", {})
            forecastday = forecast.get("forecastday", [{}])[0] if forecast.get("forecastday") else {}
            astro = forecastday.get("astro", {})
            
            # Extract condition
            condition = current.get("condition", {})
            
            # Parse sunrise/sunset
            sunrise_str = astro.get("sunrise", "06:00 AM")
            sunset_str = astro.get("sunset", "06:00 PM")
            
            # Convert to datetime (using today's date)
            from datetime import datetime as dt
            today = dt.now(timezone.utc).date()
            sunrise = dt.strptime(f"{today} {sunrise_str}", "%Y-%m-%d %I:%M %p").replace(tzinfo=timezone.utc)
            sunset = dt.strptime(f"{today} {sunset_str}", "%Y-%m-%d %I:%M %p").replace(tzinfo=timezone.utc)
            
            # Use metric or imperial based on units parameter
            temp = current.get("temp_c" if units == "metric" else "temp_f", 0.0)
            feels_like = current.get("feelslike_c" if units == "metric" else "feelslike_f", 0.0)
            wind_speed = current.get("wind_kph" if units == "metric" else "wind_mph", 0.0)
            visibility = current.get("vis_km" if units == "metric" else "vis_miles", 10.0) * 1000  # Convert to meters
            pressure = current.get("pressure_mb" if units == "metric" else "pressure_in", 0)
            
            # Create CurrentWeather object
            current_weather = CurrentWeather(
                location=location.get("name", f"{lat}, {lon}"),
                coordinates=coordinates,
                timestamp=datetime.fromisoformat(current.get("last_updated", datetime.now(timezone.utc).isoformat()).replace(" ", "T")),
                temperature=temp,
                feels_like=feels_like,
                conditions=condition.get("text", "Unknown"),
                description=condition.get("text", "No description available"),
                humidity=current.get("humidity", 0),
                pressure=int(pressure),
                wind_speed=wind_speed,
                wind_direction=current.get("wind_degree", 0),
                visibility=int(visibility),
                uv_index=current.get("uv", 0.0),
                clouds=current.get("cloud", 0),
                sunrise=sunrise,
                sunset=sunset,
            )
            
            logger.info(f"Successfully retrieved current weather: {current_weather.conditions}")
            return current_weather
            
        except (APIError, RateLimitError):
            raise
        except httpx.TimeoutException:
            raise APIError(
                "Request timed out while fetching current weather",
                details=f"The weather service did not respond within {API_TIMEOUT} seconds"
            )
        except httpx.RequestError as e:
            raise APIError(
                "Network error while fetching current weather",
                details=str(e)
            )
        except ValueError as e:
            # Re-raise validation errors from Coordinates or CurrentWeather
            raise
        except Exception as e:
            logger.exception(f"Unexpected error fetching current weather: {e}")
            raise WeatherServiceError(
                "Failed to fetch current weather",
                details=str(e)
            )

    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 7,
        units: str = DEFAULT_UNITS
    ) -> Forecast:
        """Get weather forecast for specific coordinates.
        
        Retrieves daily weather forecasts from WeatherAPI.com.
        
        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            days: Number of days to forecast (1-8), defaults to 7
            units: Unit system ("metric" or "imperial"), defaults to metric
            
        Returns:
            Forecast object with daily forecast data
            
        Raises:
            APIError: If the API request fails
            ValueError: If coordinates or days parameter is invalid
        """
        logger.info(f"Fetching {days}-day forecast for coordinates: ({lat}, {lon})")
        
        # Validate coordinates
        coordinates = Coordinates(latitude=lat, longitude=lon)
        
        # Validate days parameter (WeatherAPI supports up to 14 days, but we limit to 8)
        if days < 1 or days > 8:
            raise ValueError(f"Days must be between 1 and 8, got {days}")
        
        try:
            response = await self.http_client.get(
                FORECAST_ENDPOINT,
                params={
                    "key": self.api_key,
                    "q": f"{lat},{lon}",
                    "days": days,
                    "aqi": "no",
                    "alerts": "no"
                }
            )
            
            self._handle_http_errors(response)
            
            data = response.json()
            location = data.get("location", {})
            forecast_data = data.get("forecast", {})
            forecastday_list = forecast_data.get("forecastday", [])
            
            if not forecastday_list:
                raise APIError(
                    "No forecast data available",
                    details="The API response did not contain daily forecast data"
                )
            
            # Parse daily forecasts
            daily_forecasts: List[DailyForecast] = []
            for day_data in forecastday_list[:days]:
                day = day_data.get("day", {})
                condition = day.get("condition", {})
                
                # Use metric or imperial based on units parameter
                temp_max = day.get("maxtemp_c" if units == "metric" else "maxtemp_f", 0.0)
                temp_min = day.get("mintemp_c" if units == "metric" else "mintemp_f", 0.0)
                temp_avg = day.get("avgtemp_c" if units == "metric" else "avgtemp_f", 0.0)
                wind_speed = day.get("maxwind_kph" if units == "metric" else "maxwind_mph", 0.0)
                
                daily_forecast = DailyForecast(
                    date=datetime.fromisoformat(day_data.get("date", datetime.now(timezone.utc).isoformat())).date(),
                    temp_min=temp_min,
                    temp_max=temp_max,
                    temp_day=temp_avg,
                    feels_like_day=temp_avg,  # WeatherAPI doesn't provide feels_like for daily
                    conditions=condition.get("text", "Unknown"),
                    description=condition.get("text", "No description available"),
                    precipitation_probability=day.get("daily_chance_of_rain", 0) / 100.0,
                    humidity=day.get("avghumidity", 0),
                    wind_speed=wind_speed,
                    uv_index=day.get("uv", 0.0),
                )
                daily_forecasts.append(daily_forecast)
            
            forecast = Forecast(
                location=location.get("name", f"{lat}, {lon}"),
                coordinates=coordinates,
                daily=daily_forecasts
            )
            
            logger.info(f"Successfully retrieved {len(daily_forecasts)}-day forecast")
            return forecast
            
        except (APIError, RateLimitError):
            raise
        except httpx.TimeoutException:
            raise APIError(
                "Request timed out while fetching forecast",
                details=f"The weather service did not respond within {API_TIMEOUT} seconds"
            )
        except httpx.RequestError as e:
            raise APIError(
                "Network error while fetching forecast",
                details=str(e)
            )
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Unexpected error fetching forecast: {e}")
            raise WeatherServiceError(
                "Failed to fetch forecast",
                details=str(e)
            )

    def _handle_http_errors(self, response: httpx.Response) -> None:
        """Handle HTTP errors from WeatherAPI.com responses.
        
        Converts HTTP error status codes into appropriate custom exceptions
        with descriptive error messages.
        
        Args:
            response: The HTTP response from the API
            
        Raises:
            APIError: For authentication errors and server errors
            LocationNotFoundError: For location not found errors
            RateLimitError: For rate limit errors
        """
        if response.status_code == 200:
            return
        
        # Try to extract error message from response
        try:
            error_data = response.json()
            error_info = error_data.get("error", {})
            error_code = error_info.get("code", 0)
            api_message = error_info.get("message", "")
        except Exception:
            api_message = response.text or "No error message provided"
            error_code = 0
        
        # Handle WeatherAPI specific error codes
        if error_code == 1002 or error_code == 2006:
            raise APIError(
                "Invalid API key",
                status_code=response.status_code,
                details="Please check that your WEATHERAPI_KEY is correct and active"
            )
        
        elif error_code == 1006:
            raise LocationNotFoundError(
                "Location",
                details=f"No matching location found. {api_message}"
            )
        
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
            
            raise RateLimitError(
                retry_after=retry_seconds,
                details=f"API rate limit exceeded. {api_message}"
            )
        
        elif 400 <= response.status_code < 500:
            raise APIError(
                f"Bad request to weather API",
                status_code=response.status_code,
                details=api_message
            )
        
        elif 500 <= response.status_code < 600:
            raise APIError(
                "Weather service temporarily unavailable",
                status_code=response.status_code,
                details=f"WeatherAPI.com is experiencing issues. {api_message}"
            )
        
        else:
            raise APIError(
                f"Unexpected HTTP status code: {response.status_code}",
                status_code=response.status_code,
                details=api_message
            )
