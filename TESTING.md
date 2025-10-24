# Testing Guide for MCP Weather Server

This document describes how to test the MCP Weather Server integration.

## Prerequisites

1. Python 3.10 or higher
2. A valid OpenWeatherMap API key (get one at https://openweathermap.org/api)
3. Kiro IDE with MCP support

## Structure Validation (No API Key Required)

To verify the server structure is correct without making API calls:

```bash
python3 test_structure.py
```

This validates:
- All modules can be imported
- Data models work correctly
- Server can be initialized
- Configuration is valid
- Error classes function properly

## Integration Testing (Requires Valid API Key)

To test with real API calls:

```bash
OPENWEATHER_API_KEY=your_api_key_here python3 test_integration.py
```

This tests:
- WeatherService geocoding
- Current weather retrieval
- Forecast retrieval
- Error handling with invalid locations
- Tool handlers with various inputs

**Note:** The provided API key in the configuration may be invalid or expired. You need to use your own valid API key for integration testing.

## Testing in Kiro

### 1. Configure the MCP Server

The MCP configuration file has been created at `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uvx",
      "args": ["--from", ".", "mcp-weather-server"],
      "env": {
        "OPENWEATHER_API_KEY": "your_api_key_here"
      },
      "disabled": false,
      "autoApprove": ["get_current_weather", "get_weather_forecast"]
    }
  }
}
```

**Important:** Replace `your_api_key_here` with your actual OpenWeatherMap API key.

### 2. Restart Kiro

After updating the configuration, restart Kiro or reconnect the MCP server from the MCP Server view in the Kiro feature panel.

### 3. Verify Tools are Exposed

Check that the following tools are available in Kiro:
- `get_current_weather`
- `get_weather_forecast`

### 4. Test Scenarios

#### Test 1: Current Weather with City Name

Ask Kiro: "What's the current weather in Paris?"

Expected: Weather data including temperature, conditions, humidity, wind speed, etc.

#### Test 2: Current Weather with Coordinates

Ask Kiro: "What's the weather at coordinates 40.7128,-74.0060?"

Expected: Weather data for New York City.

#### Test 3: Weather Forecast

Ask Kiro: "Give me a 5-day weather forecast for London"

Expected: Forecast data for 5 days with min/max temperatures and conditions.

#### Test 4: Invalid Location Error Handling

Ask Kiro: "What's the weather in InvalidCityXYZ123?"

Expected: Error message indicating the location was not found.

#### Test 5: Different Units

Ask Kiro: "What's the weather in Tokyo in imperial units?"

Expected: Weather data with Fahrenheit temperatures and mph wind speeds.

## Manual Testing Checklist

- [ ] MCP configuration file created at `.kiro/settings/mcp.json`
- [ ] Server starts successfully via uvx
- [ ] Tools are correctly exposed to the MCP client
- [ ] `get_current_weather` works with city name
- [ ] `get_current_weather` works with coordinates
- [ ] `get_weather_forecast` works with different day counts (1-8)
- [ ] Error handling works with invalid location
- [ ] Logs show appropriate information
- [ ] Error messages are clear and helpful

## Troubleshooting

### Server Won't Start

1. Check that all dependencies are installed:
   ```bash
   pip install mcp httpx pydantic python-dotenv
   ```

2. Verify the API key is set in the configuration

3. Check the logs for error messages

### API Key Errors (HTTP 401)

- Verify your API key is valid and active
- Check that you haven't exceeded the API rate limits
- Ensure the API key is correctly set in the environment variable

### Location Not Found Errors

- Check the spelling of the city name
- Try using coordinates instead: "latitude,longitude"
- Some small cities may not be in the OpenWeatherMap database

### Import Errors

If you see `ModuleNotFoundError: No module named 'mcp'`:

```bash
pip install mcp
```

## Test Results

### Structure Validation: ✓ PASSED

All modules import correctly, data models validate properly, and the server initializes successfully.

### Integration Testing: ⚠️ REQUIRES VALID API KEY

The integration tests require a valid OpenWeatherMap API key. The key provided in the initial configuration appears to be invalid or expired (HTTP 401 error).

To complete integration testing:
1. Obtain a valid API key from https://openweathermap.org/api
2. Update `.kiro/settings/mcp.json` with your key
3. Run the integration tests again

## Logs and Debugging

The server logs important information at different levels:

- **INFO**: Successful operations, server startup/shutdown
- **WARNING**: Rate limits, timeouts, recoverable errors
- **ERROR**: API errors, critical failures
- **DEBUG**: Detailed request/response information

To enable debug logging, set the `LOG_LEVEL` environment variable:

```json
{
  "mcpServers": {
    "weather": {
      "env": {
        "OPENWEATHER_API_KEY": "your_key",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```
