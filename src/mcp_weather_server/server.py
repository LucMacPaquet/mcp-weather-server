"""MCP Weather Server implementation.

This module implements the main MCP server that exposes weather tools
to MCP clients using the official Python MCP SDK.
"""

import logging
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .weather_service import WeatherService
from .tools.current_weather import handle_current_weather
from .tools.forecast import handle_forecast
from .config import setup_logging, DEFAULT_UNITS

logger = logging.getLogger(__name__)


class WeatherMCPServer:
    """MCP server for weather data tools.
    
    This server exposes two main tools:
    1. get_current_weather - Get current weather for a location
    2. get_weather_forecast - Get weather forecast for a location
    
    The server uses stdio transport for communication with MCP clients.
    """
    
    def __init__(self, api_key: str):
        """Initialize the Weather MCP Server.
        
        Args:
            api_key: OpenWeatherMap API key for authentication
        """
        self.api_key = api_key
        self.weather_service: WeatherService | None = None
        self.server = Server("mcp-weather-server")
        
        # Configure logging
        setup_logging()
        logger.info("Initializing Weather MCP Server")
        
        # Register tools
        self.register_tools()
    
    def register_tools(self) -> None:
        """Register weather tools with the MCP server.
        
        This method configures the tool definitions and handlers for:
        - get_current_weather: Retrieve current weather data
        - get_weather_forecast: Retrieve weather forecast data
        """
        logger.info("Registering weather tools")
        
        # Register list_tools handler
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available weather tools."""
            return [
                Tool(
                    name="get_current_weather",
                    description=(
                        "Get current weather conditions for a specific location. "
                        "Provides temperature, conditions, humidity, wind speed, UV index, "
                        "and other meteorological data. "
                        "Location can be specified as a city name (e.g., 'Paris', 'London,UK') "
                        "or coordinates (e.g., '48.8566,2.3522')."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": (
                                    "Location to get weather for. Can be a city name "
                                    "(e.g., 'Paris', 'New York,NY,US') or coordinates "
                                    "in 'latitude,longitude' format (e.g., '48.8566,2.3522')"
                                ),
                            },
                            "units": {
                                "type": "string",
                                "description": (
                                    "Unit system for temperature and other measurements. "
                                    "'metric' for Celsius, km/h, etc. (default), "
                                    "'imperial' for Fahrenheit, mph, etc."
                                ),
                                "enum": ["metric", "imperial"],
                                "default": DEFAULT_UNITS,
                            },
                        },
                        "required": ["location"],
                    },
                ),
                Tool(
                    name="get_weather_forecast",
                    description=(
                        "Get weather forecast for a specific location. "
                        "Provides daily forecasts including temperature range, conditions, "
                        "precipitation probability, humidity, wind speed, and UV index. "
                        "Location can be specified as a city name (e.g., 'Paris', 'London,UK') "
                        "or coordinates (e.g., '48.8566,2.3522'). "
                        "Forecasts are available for up to 8 days."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": (
                                    "Location to get forecast for. Can be a city name "
                                    "(e.g., 'Paris', 'New York,NY,US') or coordinates "
                                    "in 'latitude,longitude' format (e.g., '48.8566,2.3522')"
                                ),
                            },
                            "days": {
                                "type": "integer",
                                "description": (
                                    "Number of days to forecast (1-8). Defaults to 7 days."
                                ),
                                "minimum": 1,
                                "maximum": 8,
                                "default": 7,
                            },
                            "units": {
                                "type": "string",
                                "description": (
                                    "Unit system for temperature and other measurements. "
                                    "'metric' for Celsius, km/h, etc. (default), "
                                    "'imperial' for Fahrenheit, mph, etc."
                                ),
                                "enum": ["metric", "imperial"],
                                "default": DEFAULT_UNITS,
                            },
                        },
                        "required": ["location"],
                    },
                ),
            ]
        
        # Register call_tool handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool execution requests."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            # Ensure weather service is initialized
            if self.weather_service is None:
                self.weather_service = WeatherService(self.api_key)
            
            try:
                if name == "get_current_weather":
                    location = arguments.get("location")
                    units = arguments.get("units", DEFAULT_UNITS)
                    
                    if not location:
                        return [
                            TextContent(
                                type="text",
                                text="Error: 'location' parameter is required"
                            )
                        ]
                    
                    result = await handle_current_weather(
                        self.weather_service,
                        location,
                        units
                    )
                    
                    # Format result as text
                    return [TextContent(type="text", text=self._format_result(result))]
                
                elif name == "get_weather_forecast":
                    location = arguments.get("location")
                    days = arguments.get("days", 7)
                    units = arguments.get("units", DEFAULT_UNITS)
                    
                    if not location:
                        return [
                            TextContent(
                                type="text",
                                text="Error: 'location' parameter is required"
                            )
                        ]
                    
                    result = await handle_forecast(
                        self.weather_service,
                        location,
                        days,
                        units
                    )
                    
                    # Format result as text
                    return [TextContent(type="text", text=self._format_result(result))]
                
                else:
                    error_msg = f"Unknown tool: {name}"
                    logger.error(error_msg)
                    return [TextContent(type="text", text=f"Error: {error_msg}")]
            
            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.exception(error_msg)
                return [TextContent(type="text", text=f"Error: {error_msg}")]
        
        logger.info("Weather tools registered successfully")
    
    def _format_result(self, result: dict[str, Any]) -> str:
        """Format tool result as human-readable text.
        
        Args:
            result: Result dictionary from tool handler
            
        Returns:
            Formatted text representation of the result
        """
        import json
        
        # Check if result contains an error
        if result.get("error"):
            error_type = result.get("error_type", "unknown")
            message = result.get("message", "An error occurred")
            details = result.get("details")
            
            error_text = f"Error ({error_type}): {message}"
            if details:
                error_text += f"\nDetails: {details}"
            
            return error_text
        
        # Format success result as pretty JSON
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    async def run(self) -> None:
        """Start the MCP server with stdio transport.
        
        This method starts the server and handles communication with MCP clients
        via standard input/output. The server will run until interrupted.
        """
        logger.info("Starting Weather MCP Server with stdio transport")
        
        try:
            # Initialize weather service
            self.weather_service = WeatherService(self.api_key)
            
            # Run server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Server is ready and listening for requests")
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.exception(f"Server error: {e}")
            raise
        finally:
            # Clean up weather service
            if self.weather_service:
                await self.weather_service.close()
                logger.info("Weather service closed")
            
            logger.info("Weather MCP Server stopped")
