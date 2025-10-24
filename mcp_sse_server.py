#!/usr/bin/env python3
"""
MCP Weather Server with SSE (Server-Sent Events) transport.

This implements the official MCP protocol over HTTP using SSE for server-to-client
communication and POST for client-to-server communication.

MCP SSE Transport Specification:
- Client sends requests via POST to /sse
- Server sends responses via SSE (text/event-stream)
- Each SSE message is a JSON-RPC response
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from typing import Dict, Optional
from collections import defaultdict

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
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
    title="MCP Weather Server (SSE)",
    description="MCP-compliant weather server using SSE transport",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
weather_service: Optional[WeatherService] = None
sessions: Dict[str, asyncio.Queue] = {}  # session_id -> response queue


@app.on_event("startup")
async def startup_event():
    """Initialize the weather service on startup."""
    global weather_service
    api_key = validate_api_key()
    weather_service = WeatherService(api_key)
    logger.info("MCP Weather Server (SSE) started and ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global weather_service
    if weather_service:
        await weather_service.close()
    logger.info("MCP Weather Server (SSE) shutdown")


async def handle_mcp_request(request_data: dict) -> dict:
    """Handle MCP JSON-RPC request and return response."""
    method = request_data.get("method")
    params = request_data.get("params", {})
    request_id = request_data.get("id")
    
    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mcp-weather-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_current_weather",
                            "description": "Get current weather for a location",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "City name or coordinates (lat,lon)"
                                    },
                                    "units": {
                                        "type": "string",
                                        "enum": ["metric", "imperial"],
                                        "default": "metric",
                                        "description": "Unit system"
                                    }
                                },
                                "required": ["location"]
                            }
                        },
                        {
                            "name": "get_weather_forecast",
                            "description": "Get weather forecast for multiple days",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "City name or coordinates (lat,lon)"
                                    },
                                    "days": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 8,
                                        "default": 7,
                                        "description": "Number of days"
                                    },
                                    "units": {
                                        "type": "string",
                                        "enum": ["metric", "imperial"],
                                        "default": "metric",
                                        "description": "Unit system"
                                    }
                                },
                                "required": ["location"]
                            }
                        }
                    ]
                }
            }
        
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
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


async def sse_generator(session_id: str):
    """Generate SSE events for a session."""
    queue = sessions[session_id]
    
    try:
        while True:
            # Wait for a response to send
            response = await queue.get()
            
            if response is None:  # Shutdown signal
                break
            
            # Format as SSE event
            yield f"data: {json.dumps(response)}\n\n"
    
    except asyncio.CancelledError:
        logger.info(f"SSE stream cancelled for session {session_id}")
    finally:
        # Cleanup session
        if session_id in sessions:
            del sessions[session_id]
        logger.info(f"Session {session_id} closed")


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP communication.
    
    This endpoint establishes an SSE connection for server-to-client communication.
    The client should send requests via POST to /messages.
    """
    # Create a new session
    session_id = str(uuid.uuid4())
    sessions[session_id] = asyncio.Queue()
    
    logger.info(f"New SSE connection established: {session_id}")
    
    # Set session ID in response header
    headers = {
        "X-Session-ID": session_id,
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    
    return StreamingResponse(
        sse_generator(session_id),
        media_type="text/event-stream",
        headers=headers
    )


@app.post("/message")
async def message_endpoint(request: Request):
    """Receive MCP requests from client and send responses via SSE.
    
    The client sends JSON-RPC requests here, and responses are sent
    back via the SSE connection.
    """
    # Get session ID from header
    session_id = request.headers.get("X-Session-ID")
    
    if not session_id or session_id not in sessions:
        return Response(
            content=json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32000,
                    "message": "Invalid or missing session ID"
                }
            }),
            status_code=400,
            media_type="application/json"
        )
    
    try:
        # Parse request
        request_data = await request.json()
        logger.info(f"Received request: {request_data.get('method')}")
        
        # Handle request
        response = await handle_mcp_request(request_data)
        
        # Send response via SSE
        await sessions[session_id].put(response)
        
        # Return acknowledgment
        return Response(status_code=202)  # Accepted
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return Response(
            content=json.dumps({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }),
            status_code=500,
            media_type="application/json"
        )


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "MCP Weather Server (SSE)",
        "version": "1.0.0",
        "protocol": "MCP over SSE",
        "transport": "Server-Sent Events",
        "endpoints": {
            "sse": "/sse (GET) - Establish SSE connection",
            "message": "/message (POST) - Send MCP requests"
        },
        "documentation": "https://modelcontextprotocol.io/docs/concepts/transports#server-sent-events-sse"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mcp-weather-server-sse",
        "active_sessions": len(sessions)
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"Starting MCP Weather Server (SSE) on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
