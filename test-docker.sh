#!/bin/bash
# Test script to validate Docker configuration

echo "🐳 Testing Docker configuration for MCP Weather Server"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "   Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

echo "✓ Docker is installed"
docker --version

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose is installed"
    docker-compose --version
else
    echo "⚠ Docker Compose not found (optional)"
fi

echo ""
echo "📋 Validating Dockerfile..."
if [ -f "Dockerfile" ]; then
    echo "✓ Dockerfile exists"
else
    echo "❌ Dockerfile not found"
    exit 1
fi

echo ""
echo "📋 Validating docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    echo "✓ docker-compose.yml exists"
else
    echo "⚠ docker-compose.yml not found (optional)"
fi

echo ""
echo "🔨 Building Docker image..."
docker build -t mcp-weather-server:test . || {
    echo "❌ Docker build failed"
    exit 1
}

echo ""
echo "✓ Docker image built successfully"

echo ""
echo "🧪 Testing container startup..."
CONTAINER_ID=$(docker run -d --name mcp-weather-test -e WEATHERAPI_KEY=13ced4f0f05a4a4f986223827252410 -i mcp-weather-server:test)

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Failed to start container"
    exit 1
fi

echo "✓ Container started: $CONTAINER_ID"

# Wait a bit for the container to initialize
sleep 2

# Check if container is still running
if docker ps | grep -q mcp-weather-test; then
    echo "✓ Container is running"
else
    echo "❌ Container stopped unexpectedly"
    docker logs mcp-weather-test
    docker rm mcp-weather-test
    exit 1
fi

echo ""
echo "📝 Container logs:"
docker logs mcp-weather-test | head -20

echo ""
echo "🧹 Cleaning up..."
docker stop mcp-weather-test > /dev/null 2>&1
docker rm mcp-weather-test > /dev/null 2>&1
docker rmi mcp-weather-server:test > /dev/null 2>&1

echo ""
echo "✅ All tests passed!"
echo ""
echo "To use the Docker container:"
echo "  ./docker-run.sh start    # Start the server"
echo "  ./docker-run.sh logs     # View logs"
echo "  ./docker-run.sh stop     # Stop the server"
