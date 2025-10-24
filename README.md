# MCP Weather Server

A Model Context Protocol (MCP) server that provides weather data through OpenWeatherMap API. This server enables MCP clients like Kiro and Claude to access current weather conditions and forecasts for any location.

## Features

- **Current Weather**: Get real-time weather data including temperature, conditions, humidity, wind speed, and more
- **Weather Forecasts**: Retrieve weather forecasts for up to 8 days
- **Flexible Location Input**: Support for both city names and latitude/longitude coordinates
- **Comprehensive Data**: Includes UV index, sunrise/sunset times, atmospheric pressure, and visibility
- **Error Handling**: Robust error management with descriptive messages
- **MCP Protocol**: Full compliance with Model Context Protocol specification

## Prerequisites

- Python 3.10 or higher
- OpenWeatherMap API key (free tier available at [openweathermap.org](https://openweathermap.org/api))
- `uv` and `uvx` installed (see [installation guide](https://docs.astral.sh/uv/getting-started/installation/))

## Installation

### For Use with Kiro or Other MCP Clients

No manual installation required! The server will be automatically downloaded and run via `uvx`.

### For Development

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp-weather-server
```

2. Install dependencies:
```bash
uv pip install -e ".[dev]"
```

3. Copy the example environment file and add your API key:
```bash
cp .env.example .env
# Edit .env and add your OPENWEATHER_API_KEY
```

## Configuration

### Get an OpenWeatherMap API Key

1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Navigate to your API keys section
3. Generate a new API key (free tier includes 1,000 calls/day)

### Configure in Kiro

Add the following to your `.kiro/settings/mcp.json` file:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uvx",
      "args": ["mcp-weather-server"],
      "env": {
        "OPENWEATHER_API_KEY": "your_api_key_here"
      },
      "disabled": false,
      "autoApprove": ["get_current_weather", "get_weather_forecast"]
    }
  }
}
```

Replace `your_api_key_here` with your actual OpenWeatherMap API key.

### Environment Variables

- `OPENWEATHER_API_KEY` (required): Your OpenWeatherMap API key
- `LOG_LEVEL` (optional): Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO
- `API_TIMEOUT` (optional): Timeout for API requests in seconds. Default: 10

## Usage

### Available Tools

#### `get_current_weather`

Get current weather conditions for a location.

**Parameters:**
- `location` (string, required): City name (e.g., "Paris") or coordinates (e.g., "48.8566,2.3522")
- `units` (string, optional): "metric" (default) or "imperial"

**Example:**
```
Get the current weather in Tokyo
```

#### `get_weather_forecast`

Get weather forecast for upcoming days.

**Parameters:**
- `location` (string, required): City name or coordinates
- `days` (integer, optional): Number of days (1-8). Default: 7
- `units` (string, optional): "metric" (default) or "imperial"

**Example:**
```
Show me the 5-day forecast for London
```

### Using with Kiro

Once configured, simply ask Kiro natural language questions:

- "What's the weather like in Paris?"
- "Give me a 3-day forecast for New York"
- "What's the temperature in Tokyo right now?"
- "Show me the weather forecast for coordinates 51.5074,-0.1278"

## Testing

For detailed testing instructions, see [TESTING.md](TESTING.md).

### Quick Structure Validation

```bash
python3 test_structure.py
```

### Integration Tests (requires valid API key)

```bash
OPENWEATHER_API_KEY=your_key python3 test_integration.py
```

## Development

### Running the Server Locally

```bash
python -m mcp_weather_server
```

### Project Structure

```
mcp-weather-server/
├── src/
│   └── mcp_weather_server/
│       ├── __init__.py
│       ├── __main__.py          # Entry point
│       ├── server.py            # MCP server implementation
│       ├── weather_service.py   # OpenWeatherMap API client
│       ├── config.py            # Configuration management
│       ├── models.py            # Data models
│       ├── tools/               # MCP tool handlers
│       │   ├── current_weather.py
│       │   └── forecast.py
│       └── utils/               # Utilities
│           ├── errors.py
│           └── formatters.py
├── tests/                       # Test suite
├── pyproject.toml              # Project configuration
├── README.md                   # This file
└── .env.example                # Example environment configuration
```

## API Rate Limits

The free tier of OpenWeatherMap includes:
- 1,000 API calls per day
- 60 calls per minute

The server handles rate limit errors gracefully and will inform you if limits are exceeded.

## Troubleshooting

### "API key is invalid"
- Verify your API key is correct in the configuration
- Ensure the API key is activated (can take a few hours after creation)

### "Location not found"
- Check the spelling of the city name
- Try using coordinates instead: "latitude,longitude"

### "Service temporarily unavailable"
- OpenWeatherMap API may be experiencing issues
- Check [OpenWeatherMap status](https://openweathermap.statuspage.io/)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Check the [OpenWeatherMap API documentation](https://openweathermap.org/api/one-call-3)
- Review the [MCP specification](https://modelcontextprotocol.io/)
- Open an issue in this repository
