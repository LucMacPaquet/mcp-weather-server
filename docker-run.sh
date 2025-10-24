#!/bin/bash
# Helper script to run MCP Weather Server in Docker

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
WEATHERAPI_KEY="${WEATHERAPI_KEY:-13ced4f0f05a4a4f986223827252410}"
IMAGE_NAME="mcp-weather-server"
CONTAINER_NAME="mcp-weather-server"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to build the Docker image
build_image() {
    print_info "Building Docker image..."
    docker build -t ${IMAGE_NAME}:latest .
    print_success "Docker image built successfully"
}

# Function to run the container
run_container() {
    print_info "Starting MCP Weather Server container..."
    
    # Stop and remove existing container if it exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_info "Removing existing container..."
        docker rm -f ${CONTAINER_NAME} > /dev/null 2>&1
    fi
    
    # Run the container
    docker run -d \
        --name ${CONTAINER_NAME} \
        -e WEATHERAPI_KEY="${WEATHERAPI_KEY}" \
        -i \
        ${IMAGE_NAME}:latest
    
    print_success "Container started: ${CONTAINER_NAME}"
}

# Function to stop the container
stop_container() {
    print_info "Stopping container..."
    docker stop ${CONTAINER_NAME} > /dev/null 2>&1 || true
    docker rm ${CONTAINER_NAME} > /dev/null 2>&1 || true
    print_success "Container stopped"
}

# Function to view logs
view_logs() {
    print_info "Viewing container logs (Ctrl+C to exit)..."
    docker logs -f ${CONTAINER_NAME}
}

# Function to execute commands in the container
exec_container() {
    docker exec -it ${CONTAINER_NAME} "$@"
}

# Function to test the server
test_server() {
    print_info "Testing MCP Weather Server..."
    
    # Test with a simple weather query
    echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
        docker exec -i ${CONTAINER_NAME} python -m mcp_weather_server
    
    print_success "Server is responding"
}

# Main script
case "${1:-}" in
    build)
        build_image
        ;;
    start)
        build_image
        run_container
        print_success "MCP Weather Server is running!"
        print_info "Use 'docker logs -f ${CONTAINER_NAME}' to view logs"
        ;;
    stop)
        stop_container
        ;;
    restart)
        stop_container
        build_image
        run_container
        ;;
    logs)
        view_logs
        ;;
    test)
        test_server
        ;;
    exec)
        shift
        exec_container "$@"
        ;;
    *)
        echo "Usage: $0 {build|start|stop|restart|logs|test|exec}"
        echo ""
        echo "Commands:"
        echo "  build    - Build the Docker image"
        echo "  start    - Build and start the container"
        echo "  stop     - Stop and remove the container"
        echo "  restart  - Restart the container"
        echo "  logs     - View container logs"
        echo "  test     - Test the server"
        echo "  exec     - Execute command in container"
        echo ""
        echo "Environment variables:"
        echo "  WEATHERAPI_KEY - WeatherAPI.com API key (default: 13ced4f0f05a4a4f986223827252410)"
        exit 1
        ;;
esac
