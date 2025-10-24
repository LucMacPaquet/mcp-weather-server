#!/usr/bin/env python3
"""Network-accessible MCP Weather Server using HTTP/SSE.

This server wraps the MCP Weather Server to make it accessible over the network
via HTTP and Server-Sent Events (SSE).
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_weather_server.weather_service import WeatherService
from mcp_weather_server.tools.current_weather import handle_current_weather
from mcp_weather_server.tools.forecast import handle_forecast
from mcp_weather_server.config import validate_api_key, setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Weather Server",
    description="Network-accessible weather data via WeatherAPI.com",
    version="1.0.0"
)

# Enable CORS for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global weather service instance
weather_service = None


@app.on_event("startup")
async def startup_event():
    """Initialize the weather service on startup."""
    global weather_service
    api_key = validate_api_key()
    weather_service = WeatherService(api_key)
    logger.info("MCP Weather Server started and ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global weather_service
    if weather_service:
        await weather_service.close()
    logger.info("MCP Weather Server shutdown")


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "MCP Weather Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "current_weather": "/weather/current",
            "forecast": "/weather/forecast",
            "tools": "/tools"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mcp-weather-server"
    }


@app.get("/tools")
async def list_tools():
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "get_current_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "location": "City name or coordinates (lat,lon)",
                    "units": "metric or imperial (optional, default: metric)"
                }
            },
            {
                "name": "get_weather_forecast",
                "description": "Get weather forecast for multiple days",
                "parameters": {
                    "location": "City name or coordinates (lat,lon)",
                    "days": "Number of days (1-8, optional, default: 7)",
                    "units": "metric or imperial (optional, default: metric)"
                }
            }
        ]
    }


@app.get("/weather/current")
async def get_current_weather_endpoint(
    location: str,
    units: str = "metric"
):
    """Get current weather for a location.
    
    Args:
        location: City name or coordinates (lat,lon)
        units: metric or imperial (default: metric)
    """
    try:
        result = await handle_current_weather(
            weather_service=weather_service,
            location=location,
            units=units
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error getting current weather: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/weather/forecast")
async def get_forecast_endpoint(
    location: str,
    days: int = 7,
    units: str = "metric"
):
    """Get weather forecast for a location.
    
    Args:
        location: City name or coordinates (lat,lon)
        days: Number of days (1-8, default: 7)
        units: metric or imperial (default: metric)
    """
    try:
        result = await handle_forecast(
            weather_service=weather_service,
            location=location,
            days=days,
            units=units
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP protocol endpoint for JSON-RPC requests."""
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        if method == "tools/list":
            tools_list = await list_tools()
            result = tools_list["tools"]
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "get_current_weather":
                result = await handle_current_weather(
                    weather_service=weather_service,
                    location=tool_args.get("location"),
                    units=tool_args.get("units", "metric")
                )
            elif tool_name == "get_weather_forecast":
                result = await handle_forecast(
                    weather_service=weather_service,
                    location=tool_args.get("location"),
                    days=tool_args.get("days", 7),
                    units=tool_args.get("units", "metric")
                )
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                )
        else:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                }
            )
        
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        )
    
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": request_id if 'request_id' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
        )


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"Starting MCP Weather Server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
