"""Custom error classes for the MCP Weather Server.

This module defines the exception hierarchy for handling various error
conditions that can occur when interacting with the OpenWeatherMap API
and processing weather data.
"""


class WeatherServiceError(Exception):
    """Base exception class for all weather service errors.
    
    This serves as the parent class for all custom exceptions in the
    weather service, allowing for broad exception handling when needed.
    """
    
    def __init__(self, message: str, details: str | None = None):
        """Initialize the weather service error.
        
        Args:
            message: The main error message
            details: Optional additional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format the error message with optional details.
        
        Returns:
            A formatted error message string
        """
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class LocationNotFoundError(WeatherServiceError):
    """Exception raised when a location cannot be found or geocoded.
    
    This error occurs when:
    - A city name cannot be resolved to coordinates
    - Invalid coordinates are provided
    - The location is not recognized by the geocoding service
    """
    
    def __init__(self, location: str, details: str | None = None):
        """Initialize the location not found error.
        
        Args:
            location: The location that could not be found
            details: Optional additional details about why the location wasn't found
        """
        self.location = location
        message = f"Location not found: '{location}'"
        super().__init__(message, details)


class RateLimitError(WeatherServiceError):
    """Exception raised when API rate limits are exceeded.
    
    This error occurs when the OpenWeatherMap API returns a 429 status code,
    indicating that too many requests have been made in a given time period.
    """
    
    def __init__(self, retry_after: int | None = None, details: str | None = None):
        """Initialize the rate limit error.
        
        Args:
            retry_after: Optional number of seconds to wait before retrying
            details: Optional additional details about the rate limit
        """
        self.retry_after = retry_after
        
        if retry_after:
            message = f"API rate limit exceeded. Retry after {retry_after} seconds"
        else:
            message = "API rate limit exceeded. Please try again later"
        
        super().__init__(message, details)


class APIError(WeatherServiceError):
    """Exception raised when the OpenWeatherMap API returns an error.
    
    This error covers various API-related issues including:
    - Authentication failures (401)
    - Server errors (5xx)
    - Invalid requests (400)
    - Network connectivity issues
    """
    
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: str | None = None
    ):
        """Initialize the API error.
        
        Args:
            message: The main error message
            status_code: Optional HTTP status code from the API response
            details: Optional additional details about the error
        """
        self.status_code = status_code
        
        if status_code:
            formatted_message = f"API error (HTTP {status_code}): {message}"
        else:
            formatted_message = f"API error: {message}"
        
        super().__init__(formatted_message, details)
