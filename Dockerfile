# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WEATHERAPI_KEY=""

# Expose stdio for MCP communication
# MCP servers communicate via stdin/stdout, no port needed

# Run the MCP server
CMD ["python", "-m", "mcp_weather_server"]
