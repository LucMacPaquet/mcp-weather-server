"""Data models for weather information using Pydantic."""

from datetime import datetime
from datetime import date as date_type
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Coordinates(BaseModel):
    """Geographic coordinates with validation."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    
    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude is within valid range."""
        if not -90 <= v <= 90:
            raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        return v
    
    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude is within valid range."""
        if not -180 <= v <= 180:
            raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v


class CurrentWeather(BaseModel):
    """Current weather data for a location."""
    
    location: str = Field(..., description="Location name")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    timestamp: datetime = Field(..., description="Time of data observation")
    temperature: float = Field(..., description="Temperature in degrees")
    feels_like: float = Field(..., description="Perceived temperature in degrees")
    conditions: str = Field(..., description="Weather condition category")
    description: str = Field(..., description="Detailed weather description")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    pressure: int = Field(..., description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., ge=0, description="Wind speed")
    wind_direction: int = Field(..., ge=0, le=360, description="Wind direction in degrees")
    visibility: int = Field(..., ge=0, description="Visibility in meters")
    uv_index: float = Field(..., ge=0, description="UV index")
    clouds: int = Field(..., ge=0, le=100, description="Cloud coverage percentage")
    sunrise: datetime = Field(..., description="Sunrise time")
    sunset: datetime = Field(..., description="Sunset time")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DailyForecast(BaseModel):
    """Daily weather forecast data."""
    
    date: date_type = Field(..., description="Forecast date")
    temp_min: float = Field(..., description="Minimum temperature")
    temp_max: float = Field(..., description="Maximum temperature")
    temp_day: float = Field(..., description="Day temperature")
    feels_like_day: float = Field(..., description="Perceived day temperature")
    conditions: str = Field(..., description="Weather condition category")
    description: str = Field(..., description="Detailed weather description")
    precipitation_probability: float = Field(..., ge=0, le=1, description="Probability of precipitation (0-1)")
    humidity: int = Field(..., ge=0, le=100, description="Humidity percentage")
    wind_speed: float = Field(..., ge=0, description="Wind speed")
    uv_index: float = Field(..., ge=0, description="UV index")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            date_type: lambda v: v.isoformat()
        }


class Forecast(BaseModel):
    """Weather forecast for multiple days."""
    
    location: str = Field(..., description="Location name")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    daily: List[DailyForecast] = Field(..., description="Daily forecasts")
    
    @field_validator('daily')
    @classmethod
    def validate_daily_forecasts(cls, v: List[DailyForecast]) -> List[DailyForecast]:
        """Validate that daily forecasts list is not empty."""
        if not v:
            raise ValueError("Daily forecasts list cannot be empty")
        return v


class WeatherError(BaseModel):
    """Error response model."""
    
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
