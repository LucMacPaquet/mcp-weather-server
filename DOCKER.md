# Docker Support for MCP Weather Server

This guide explains how to run the MCP Weather Server in a Docker container.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Quick Start

### Using the helper script (Recommended)

```bash
# Build and start the container
./docker-run.sh start

# View logs
./docker-run.sh logs

# Stop the container
./docker-run.sh stop

# Restart the container
./docker-run.sh restart
```

### Using Docker directly

```bash
# Build the image
docker build -t mcp-weather-server:latest .

# Run the container
docker run -d \
  --name mcp-weather-server \
  -e WEATHERAPI_KEY=your_api_key_here \
  -i \
  mcp-weather-server:latest

# View logs
docker logs -f mcp-weather-server

# Stop the container
docker stop mcp-weather-server
docker rm mcp-weather-server
```

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Configuration

### Environment Variables

- `WEATHERAPI_KEY`: Your WeatherAPI.com API key (default: included test key)
- `LOG_LEVEL`: Logging level (default: INFO)
- `API_TIMEOUT`: API request timeout in seconds (default: 10)

### Custom API Key

You can set your own API key in several ways:

**1. Environment variable:**
```bash
export WEATHERAPI_KEY=your_key_here
./docker-run.sh start
```

**2. Docker run command:**
```bash
docker run -d \
  --name mcp-weather-server \
  -e WEATHERAPI_KEY=your_key_here \
  -i \
  mcp-weather-server:latest
```

**3. Docker Compose (.env file):**
```bash
echo "WEATHERAPI_KEY=your_key_here" > .env
docker-compose up -d
```

## Using with MCP Clients

### Claude Desktop Configuration

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-weather-server",
        "python",
        "-m",
        "mcp_weather_server"
      ]
    }
  }
}
```

**Note:** The container must be running before starting Claude Desktop.

### Kiro IDE Configuration

Add this to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-weather-server",
        "python",
        "-m",
        "mcp_weather_server"
      ],
      "disabled": false,
      "autoApprove": [
        "get_current_weather",
        "get_weather_forecast"
      ]
    }
  }
}
```

## Testing

Test that the server is working:

```bash
# Using the helper script
./docker-run.sh test

# Or manually
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  docker exec -i mcp-weather-server python -m mcp_weather_server
```

## Troubleshooting

### Container won't start

Check the logs:
```bash
docker logs mcp-weather-server
```

### API key issues

Verify the environment variable is set:
```bash
docker exec mcp-weather-server env | grep WEATHERAPI_KEY
```

### Container not responding

Restart the container:
```bash
./docker-run.sh restart
```

Or with Docker directly:
```bash
docker restart mcp-weather-server
```

## Building for Production

### Multi-stage build (smaller image)

Create a `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/src /app/src

ENV PYTHONUNBUFFERED=1
ENV WEATHERAPI_KEY=""

CMD ["python", "-m", "mcp_weather_server"]
```

Build:
```bash
docker build -f Dockerfile.prod -t mcp-weather-server:prod .
```

## Docker Hub

To publish to Docker Hub:

```bash
# Tag the image
docker tag mcp-weather-server:latest yourusername/mcp-weather-server:latest

# Push to Docker Hub
docker push yourusername/mcp-weather-server:latest
```

## Advanced Usage

### Running with custom configuration

Mount a custom configuration file:

```bash
docker run -d \
  --name mcp-weather-server \
  -v $(pwd)/custom-config.py:/app/config.py \
  -e WEATHERAPI_KEY=your_key_here \
  -i \
  mcp-weather-server:latest
```

### Health checks

Add a health check to docker-compose.yml:

```yaml
services:
  mcp-weather-server:
    # ... other config ...
    healthcheck:
      test: ["CMD", "python", "-c", "import mcp_weather_server"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Security Notes

- Never commit your API key to version control
- Use Docker secrets for production deployments
- Run containers with minimal privileges
- Keep the base image updated

## Support

For issues related to Docker deployment, please open an issue on GitHub:
https://github.com/LucMacPaquet/mcp-weather-server/issues
