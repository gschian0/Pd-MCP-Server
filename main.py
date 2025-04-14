#!/usr/bin/env python
"""
Pd-MCP Server Main Entry Point

This script serves as the main entry point for the Pure Data MCP server.
It initializes the OSC daemon and MCP server with the appropriate configuration
and starts the server with the requested transport protocol.

The server has two main components:
1. OSC Communication Layer: Handles bidirectional communication with Pure Data
2. MCP Server: Implements the Model Context Protocol for Claude integration

Key features:
- Command-line argument parsing for configuration
- OSC connection management with port auto-selection
- Support for multiple MCP transports (stdio, SSE)
- Integration with Pure Data via OSC messages

Important implementation note:
The OSC server initialization is carefully managed through the shared
osc_server_started flag to prevent binding to multiple ports. This is
particularly important when the server is used with Claude Desktop,
which might trigger multiple initialization paths.

Usage:
    python main.py                   # Run with default settings
    python main.py --debug           # Run with debug logging
    python main.py --transport sse   # Use SSE transport instead of stdio
"""

import logging
import argparse
import asyncio
import os

from osc_daemon import PureDataOSC
# Import the mcp_server instance from the mcp_server module
# Also import the osc_server_started flag to track OSC server initialization state
from mcp_server import mcp_server as pd_mcp_server, pd_lifespan, osc_server_started
import mcp_server as mcp_server_module
from mcp.server.fastmcp import FastMCP, Context

def parse_arguments():
    """Parse command line arguments.
    
    This function parses command line arguments for configuring the server.
    It looks for default values in environment variables before falling back
    to hardcoded defaults.
    
    Returns:
        An argparse.Namespace object containing the parsed arguments
        
    Command-line options:
        --host: Pure Data OSC host (default: 127.0.0.1)
        --port: Pure Data OSC port (default: 5000)
        --feedback-port: Port for receiving feedback from Pure Data (default: 5001)
        --debug: Enable debug logging
        --transport: MCP transport protocol (stdio, http, sse)
        --http-port: HTTP port if using HTTP transport
    """
    # Get defaults from environment variables, if present
    default_host = os.environ.get("PD_OSC_HOST", "127.0.0.1")
    default_port = int(os.environ.get("PD_OSC_PORT", "5000"))
    default_feedback_port = int(os.environ.get("PD_FEEDBACK_PORT", "5001"))
    
    parser = argparse.ArgumentParser(description="Pure Data MCP Server")
    parser.add_argument("--host", default=default_host, help=f"Pure Data OSC host (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Pure Data OSC port (default: {default_port})")
    parser.add_argument("--feedback-port", type=int, default=default_feedback_port, 
                       help=f"Port for receiving feedback from Pure Data (default: {default_feedback_port})")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "sse"],
                       help="MCP transport protocol")
    parser.add_argument("--http-port", type=int, default=8000, 
                       help="HTTP port (if using HTTP transport)")
    return parser.parse_args()

async def main():
    """Main entry point for the Pd-MCP server.
    
    This function initializes the server with the specified configuration,
    sets up logging, and starts the MCP server with the requested transport.
    
    The function:
    1. Parses command line arguments
    2. Configures logging
    3. Updates global OSC settings in the mcp_server module
    4. Starts the MCP server with the appropriate transport
    """
    args = parse_arguments()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Update global settings in mcp_server module
    # These settings will be used by the lifespan context manager
    # to initialize the OSC connection
    mcp_server_module.PD_OSC_HOST = args.host
    mcp_server_module.PD_OSC_PORT = args.port
    mcp_server_module.PD_FEEDBACK_PORT = args.feedback_port
    
    logging.info(f"Starting Pure Data MCP server with OSC configuration:")
    logging.info(f"Host: {args.host}, Port: {args.port}, Feedback Port: {args.feedback_port}")
    
    # We use the mcp_server instance created in the mcp_server module
    # The OSC server will be initialized in the lifespan context manager
    # and the osc_server_started flag will prevent double initialization
    
    # Start the MCP server with the specified transport
    logging.info(f"Starting MCP Server with {args.transport} transport...")
    if args.transport == "http":
        # HTTP transport requires additional setup that's not implemented here
        logging.error("HTTP transport not directly supported in this script")
        return
    elif args.transport == "stdio":
        # Use stdio transport for terminal or Claude Desktop integration
        await pd_mcp_server.run_stdio_async()
    else:  # args.transport == "sse"
        # SSE transport for web integration
        await pd_mcp_server.run_sse_async()

if __name__ == "__main__":
    try:
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle clean shutdown on Ctrl+C
        logging.info("Server stopped by user")
    except Exception as e:
        # Log any unexpected errors
        logging.error(f"Error running server: {e}", exc_info=True) 