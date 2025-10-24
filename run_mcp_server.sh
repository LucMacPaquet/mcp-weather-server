#!/bin/bash
# Wrapper script to run MCP Weather Server with proper environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include src directory
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Check if mcp package is installed, if not install dependencies
if ! python3 -c "import mcp" 2>/dev/null; then
    echo "Installing dependencies..." >&2
    python3 -m pip install -q mcp httpx pydantic python-dotenv
fi

# Run the server
exec python3 -m mcp_weather_server
