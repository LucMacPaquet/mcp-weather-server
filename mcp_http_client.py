#!/usr/bin/env python3
"""
MCP HTTP Client - Wrapper to connect to remote MCP Weather Server via HTTP
This allows Kiro/Claude to communicate with the Docker server on another machine
"""

import sys
import json
import requests

# Configuration
SERVER_URL = "http://192.168.2.23:8081"

def handle_mcp_request(request_data):
    """Forward MCP request to HTTP server and return response"""
    try:
        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")
        
        if method == "tools/list":
            # Get tools list from HTTP endpoint
            response = requests.get(f"{SERVER_URL}/tools", timeout=10)
            response.raise_for_status()
            tools_data = response.json()
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": tools_data.get("tools", [])
            }
        
        elif method == "tools/call":
            # Call tool via HTTP endpoint
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "get_current_weather":
                location = tool_args.get("location")
                units = tool_args.get("units", "metric")
                
                response = requests.get(
                    f"{SERVER_URL}/weather/current",
                    params={"location": location, "units": units},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
                
            elif tool_name == "get_weather_forecast":
                location = tool_args.get("location")
                days = tool_args.get("days", 7)
                units = tool_args.get("units", "metric")
                
                response = requests.get(
                    f"{SERVER_URL}/weather/forecast",
                    params={"location": location, "days": days, "units": units},
                    timeout=10
                )
                response.raise_for_status()
                result = response.json()
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
                "result": result
            }
        
        elif method == "initialize":
            # Handle initialization
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "mcp-weather-server-http",
                        "version": "1.0.0"
                    }
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
    
    except requests.RequestException as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"HTTP request failed: {str(e)}"
            }
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

def main():
    """Main loop - read JSON-RPC from stdin, forward to HTTP server, write response to stdout"""
    import sys
    
    # Ensure unbuffered I/O
    sys.stdin.reconfigure(line_buffering=True)
    sys.stdout.reconfigure(line_buffering=True)
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            request = json.loads(line)
            response = handle_mcp_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()
