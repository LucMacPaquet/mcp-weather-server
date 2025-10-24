"""Entry point for MCP Weather Server.

This module provides the main entry point for running the server via uvx.
It handles configuration loading, validation, server initialization, and
graceful shutdown on signals.
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from .config import validate_api_key, validate_configuration, setup_logging, ConfigurationError
from .server import WeatherMCPServer

logger = logging.getLogger(__name__)


class ServerShutdown(Exception):
    """Exception raised to trigger graceful server shutdown."""
    pass


async def main() -> int:
    """Main entry point for the MCP Weather Server.
    
    This function:
    1. Sets up logging
    2. Loads and validates configuration
    3. Initializes the WeatherMCPServer
    4. Handles graceful shutdown on SIGINT/SIGTERM
    5. Manages startup errors
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Setup logging first
    setup_logging()
    logger.info("Starting MCP Weather Server")
    
    # Track server instance for cleanup
    server: Optional[WeatherMCPServer] = None
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name} signal, initiating graceful shutdown...")
        shutdown_event.set()
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        validate_configuration()
        
        # Get and validate API key
        api_key = validate_api_key()
        logger.info("API key validated successfully")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Signal handlers registered (SIGINT, SIGTERM)")
        
        # Initialize the MCP server
        logger.info("Initializing Weather MCP Server...")
        server = WeatherMCPServer(api_key)
        
        # Run the server
        logger.info("Server initialized, starting main loop...")
        
        # Create a task for the server
        server_task = asyncio.create_task(server.run())
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        
        # Wait for either server completion or shutdown signal
        done, pending = await asyncio.wait(
            [server_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Check if server task raised an exception
        if server_task in done:
            try:
                await server_task
            except Exception as e:
                logger.exception(f"Server task failed: {e}")
                return 1
        
        logger.info("Server shutdown completed successfully")
        return 0
    
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        logger.error(
            "Please ensure OPENWEATHER_API_KEY is set in your environment variables "
            "or .env file. See .env.example for reference."
        )
        return 1
    
    except Exception as e:
        logger.exception(f"Unexpected error during server startup: {e}")
        return 1
    
    finally:
        logger.info("Cleanup complete, exiting")


def run() -> None:
    """Synchronous wrapper for the async main function.
    
    This is the actual entry point called by uvx.
    """
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
