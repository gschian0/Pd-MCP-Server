"""
Pure Data MCP Server Module

This module implements a Model Context Protocol (MCP) server for Pure Data integration.
It provides a bridge between Claude and Pure Data, allowing the LLM to control
and interact with Pure Data patches via OSC (Open Sound Control).

Key features:
1. OSC communication with Pure Data for sending commands and receiving feedback
2. MCP tools for creating, deleting, connecting, and controlling Pure Data objects
3. MCP resources for querying information about Pure Data
4. MCP prompts for common Pure Data operations

The server is designed to work with Claude Desktop through the MCP integration,
as well as directly via stdio or SSE transports.

Important implementation note:
The OSC server initialization is carefully managed to prevent duplicate starts.
The osc_server_started flag ensures that even if start_server() is called multiple
times (e.g., once during lifespan initialization and again during tool execution),
the server will only bind to a port once.
"""

import logging
import asyncio
import os
from osc_daemon import PureDataOSC
from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# Default OSC configuration - can be overridden at runtime
PD_OSC_HOST = os.environ.get("PD_OSC_HOST", "127.0.0.1")
PD_OSC_PORT = int(os.environ.get("PD_OSC_PORT", "5000"))
PD_FEEDBACK_PORT = int(os.environ.get("PD_FEEDBACK_PORT", "5001"))

# Initialize MCP Server
mcp_server = FastMCP("pd-mcp-server")

# Initialize OSC client - will be set in lifespan
pd_osc = None
osc_server_started = False  # Flag to track if OSC server has been started

# Global object tracking system
# Maps object_ids (in the format "{object_type}_{x}_{y}") to numeric indices
# This provides a stable way to identify objects for connections in Pure Data
object_indices = {}
next_index = 0

# Create application lifespan
@asynccontextmanager
async def pd_lifespan(server: FastMCP):
    """Manage application lifecycle with OSC connection.
    
    This context manager handles the initialization and cleanup of the OSC connection
    to Pure Data. It is called when the MCP server starts up and shuts down.
    
    The osc_server_started flag prevents multiple initializations of the OSC server,
    which could lead to binding to multiple ports unnecessarily.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        A dictionary containing the initialized OSC connection
    """
    global pd_osc, osc_server_started
    try:
        # Initialize OSC connection on startup
        logging.info(f"Initializing OSC connection to Pure Data:")
        logging.info(f"Host: {PD_OSC_HOST}, Port: {PD_OSC_PORT}, Feedback port: {PD_FEEDBACK_PORT}")
        
        pd_osc = PureDataOSC(PD_OSC_HOST, PD_OSC_PORT, PD_FEEDBACK_PORT)
        
        # Register default feedback handlers
        pd_osc.register_feedback_handler("/pd/feedback/*", handle_pd_feedback)
        
        try:
            # Only start the server if it hasn't been started yet
            # This prevents binding to multiple ports when the server
            # is initialized multiple times (e.g., in Claude Desktop)
            if not osc_server_started:
                # Start with port auto-selection if the configured port is unavailable
                await pd_osc.start_server()
                osc_server_started = True
                
                if pd_osc.feedback_port != PD_FEEDBACK_PORT:
                    logging.warning(f"Using alternate feedback port: {pd_osc.feedback_port}")
                    logging.warning(f"Make sure Pure Data is configured to send to port {pd_osc.feedback_port}")
                    
                logging.info(f"OSC server listening for feedback on {pd_osc.host}:{pd_osc.feedback_port}")
            else:
                logging.info(f"OSC server already running on {pd_osc.host}:{pd_osc.feedback_port}")
            
            # Yield the OSC connection to make it available in the lifespan context
            yield {"pd_osc": pd_osc}
        except Exception as e:
            logging.error(f"Error starting OSC server: {e}")
            raise
    finally:
        # Clean up on shutdown (nothing specific needed for OSC)
        logging.info("Shutting down OSC connection")

# Configure server with lifespan
mcp_server = FastMCP(
    "pd-mcp-server",
    description="Pure Data MCP Server for controlling Pd via OSC",
    lifespan=pd_lifespan
)

async def handle_pd_feedback(address: str, *args: Any) -> None:
    """Handle feedback messages from Pure Data.
    
    This function is registered as a handler for all feedback messages
    from Pure Data. It logs the received messages and could be expanded
    to notify MCP clients about events in Pure Data.
    
    Args:
        address: The OSC address received
        args: The arguments sent with the OSC message
    """
    logging.info(f"⬅️ Received feedback: {address} {args}")
    # This could be expanded to notify MCP clients about Pd events

# MCP Tool Definitions
@mcp_server.tool()
def create_object(object_type: str, args: List[str], position: Dict[str, int], ctx: Context) -> Dict[str, Any]:
    """Create a new Pd object.
    
    This tool creates a new object in the Pure Data patch at the specified position.
    The object can be any valid Pd object type (e.g., osc~, dac~) with optional arguments.
    
    The implementation handles:
    1. Creating the object in Pure Data via OSC
    2. Assigning a unique numeric index to the object for connection tracking
    3. Returning an object_id that can be used in subsequent API calls
    
    The object_id follows the format "{object_type}_{x}_{y}" to provide
    a predictable way to reference objects.
    
    Args:
        object_type: Type of Pd object (e.g., osc~, dac~)
        args: Arguments for the object (e.g., ["440"] for an oscillator)
        position: Position on the canvas (x, y coordinates)
        ctx: MCP context
        
    Returns:
        Response with object ID and status
        
    Example:
        create_object("osc~", ["440"], {"x": 100, "y": 100}, ctx)
    """
    global object_indices, next_index
    
    # Access the OSC client from the lifespan context
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    # Debug log for tracking
    logging.info(f"Creating object: {object_type} at position {position} with args {args}")
    
    # Send the create command to Pure Data: [object_type, x, y, *args]
    # Note: This format is specifically required by the absolute_final_solution.pd patch
    pd_osc.send_message("/pd/create", [object_type, position["x"], position["y"]] + args)
    
    # Assign and track the numeric index using global variables
    # This is critical for properly managing connections between objects
    object_index = next_index
    next_index += 1
    object_id = f"{object_type}_{position['x']}_{position['y']}"
    object_indices[object_id] = object_index
    
    logging.info(f"Created object with ID: {object_id}, index: {object_index}")
    
    return {"status": "success", "object_id": object_id, "object_index": object_index}

@mcp_server.tool()
def delete_object(object_id: str, ctx: Context) -> Dict[str, str]:
    """Delete a Pd object.
    
    This tool removes an existing object from the Pure Data patch.
    It also removes the object's entry from the index tracking system
    to maintain consistency.
    
    Args:
        object_id: ID of the object to delete
        ctx: MCP context
        
    Returns:
        Response with status
        
    Example:
        delete_object("osc~_100_100", ctx)
    """
    global object_indices
    
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message("/pd/delete", [object_id])
    
    # Remove the object from our tracking system if it exists
    # This ensures we don't keep references to deleted objects
    if object_id in object_indices:
        del object_indices[object_id]
        logging.info(f"Deleted object and removed from tracking: {object_id}")
    
    return {"status": "success"}

@mcp_server.tool()
def connect_objects(source: Dict[str, Any], destination: Dict[str, Any], ctx: Context) -> Dict[str, str]:
    """Create a connection between two Pd objects.
    
    This tool connects two objects in the Pure Data patch by creating a
    patch cord between the specified outlet and inlet.
    
    The connection system uses numeric indices rather than string IDs,
    as required by the Pure Data patch. The global object_indices
    dictionary maps from the user-friendly string IDs to these numeric indices.
    
    Args:
        source: Source object with id and port
               e.g., {"id": "osc~_100_100", "port": 0}
        destination: Destination object with id and port
                    e.g., {"id": "dac~_200_100", "port": 0}
        ctx: MCP context
        
    Returns:
        Response with status
        
    Example:
        connect_objects({"id": "osc~_100_100", "port": 0}, {"id": "dac~_200_100", "port": 0}, ctx)
    """
    global object_indices
    
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    # Get the source and destination IDs
    source_id = source["id"]
    dest_id = destination["id"]
    
    # Debug log
    logging.info(f"Connecting objects: {source_id} (port {source['port']}) -> {dest_id} (port {destination['port']})")
    
    # Try to get indices from our global tracking system
    # If an object ID isn't found, we assign a new index and log a warning
    # This helps with resilience in case object creation failed but connection is attempted
    if source_id not in object_indices:
        logging.warning(f"Source object ID not found: {source_id}, assigning new index")
        object_indices[source_id] = next_index
        next_index += 1
        
    if dest_id not in object_indices:
        logging.warning(f"Destination object ID not found: {dest_id}, assigning new index")
        object_indices[dest_id] = next_index
        next_index += 1
        
    source_index = object_indices[source_id]
    dest_index = object_indices[dest_id]
    
    logging.info(f"Connecting indexed objects: {source_index} -> {dest_index}")
    
    # Send connection message with numeric indices
    # Format: [source_index, source_port, dest_index, dest_port]
    pd_osc.send_message("/pd/connect", [source_index, source["port"], dest_index, destination["port"]])
    return {"status": "success"}

@mcp_server.tool()
def disconnect_objects(source_id: str, destination_id: str, ctx: Context) -> Dict[str, str]:
    """Remove an existing connection between two Pd objects.
    
    This tool disconnects two objects in the Pure Data patch.
    It handles the translation from string IDs to numeric indices
    required by the Pure Data patch.
    
    Args:
        source_id: ID of the source object
        destination_id: ID of the destination object
        ctx: MCP context
        
    Returns:
        Response with status
    """
    global object_indices
    
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    # Check if we have indices for these objects
    if source_id in object_indices and destination_id in object_indices:
        source_index = object_indices[source_id]
        dest_index = object_indices[destination_id]
        pd_osc.send_message("/pd/disconnect", [source_index, dest_index])
    else:
        # Fall back to using string IDs if indices not found
        pd_osc.send_message("/pd/disconnect", [source_id, destination_id])
    
    return {"status": "success"}

@mcp_server.tool()
def set_param(object_id: str, parameter: str, value: str, ctx: Context) -> Dict[str, str]:
    """Modify a parameter of an existing Pd object.
    
    Args:
        object_id: ID of the object
        parameter: Parameter name to modify
        value: New value for the parameter
        ctx: MCP context
        
    Returns:
        Response with status
    """
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message(f"/pd/set/{object_id}/{parameter}", [value])
    return {"status": "success"}

@mcp_server.tool()
def get_param(object_id: str, parameter: str, ctx: Context) -> Dict[str, str]:
    """Retrieve the current value of an object's parameter.
    
    Args:
        object_id: ID of the object
        parameter: Parameter name to retrieve
        ctx: MCP context
        
    Returns:
        Response with status and value
    """
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message(f"/pd/get/{object_id}/{parameter}")
    # In a real implementation, we would wait for a response from Pd
    # For now, we return a placeholder
    return {"status": "success", "value": "unknown"}

@mcp_server.tool()
def start_dsp(ctx: Context) -> Dict[str, str]:
    """Enable DSP processing in Pure Data.
    
    This turns on audio processing in Pure Data so that
    sound can be generated or processed.
    
    Args:
        ctx: MCP context
        
    Returns:
        Response with status
    """
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message("/pd/dsp", [1])
    return {"status": "success"}

@mcp_server.tool()
def stop_dsp(ctx: Context) -> Dict[str, str]:
    """Disable DSP processing in Pure Data.
    
    This turns off audio processing in Pure Data to
    conserve CPU when audio is not needed.
    
    Args:
        ctx: MCP context
        
    Returns:
        Response with status
    """
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message("/pd/dsp", [0])
    return {"status": "success"}

@mcp_server.tool()
def refresh_gui(ctx: Context) -> Dict[str, str]:
    """Force Pure Data to refresh its GUI.
    
    This can be useful after making multiple changes to ensure
    the visual state of Pure Data matches the internal state.
    
    Args:
        ctx: MCP context
        
    Returns:
        Response with status
    """
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message("/pd/gui_refresh", [1])
    return {"status": "success"}

@mcp_server.tool()
def save_patch(file_path: str, ctx: Context) -> Dict[str, str]:
    """Save the current Pd patch.
    
    This tool saves the current state of the Pure Data patch
    to a file at the specified path.
    
    Args:
        file_path: Path to save the patch file
        ctx: MCP context
        
    Returns:
        Response with status
    """
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message("/pd/save", [file_path])
    return {"status": "success"}

@mcp_server.tool()
def load_patch(file_path: str, ctx: Context) -> Dict[str, str]:
    """Load a Pd patch from a file.
    
    This tool loads a Pure Data patch from the specified file path.
    It will replace the current patch state.
    
    Args:
        file_path: Path to the patch file to load
        ctx: MCP context
        
    Returns:
        Response with status
    """
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    pd_osc.send_message("/pd/load", [file_path])
    return {"status": "success"}

# Add a resource for getting available Pd objects
@mcp_server.resource("pd://objects")
def get_pd_objects() -> str:
    """Get a list of available Pd objects.
    
    This resource provides a catalog of common Pure Data objects
    with their names and descriptions. This can be used by MCP clients
    to present a list of available objects to the user or to provide
    information about specific objects.
    
    Returns:
        JSON string with Pd object types and descriptions
        
    Example:
        A Claude client can access this using: @pd://objects
    """
    return """
    {
        "objects": [
            {"name": "osc~", "description": "Sine wave oscillator"},
            {"name": "dac~", "description": "Digital to analog converter (audio output)"},
            {"name": "adc~", "description": "Analog to digital converter (audio input)"},
            {"name": "phasor~", "description": "Sawtooth oscillator"},
            {"name": "noise~", "description": "White noise generator"},
            {"name": "lop~", "description": "Lowpass filter"},
            {"name": "hip~", "description": "Highpass filter"},
            {"name": "bp~", "description": "Bandpass filter"},
            {"name": "vcf~", "description": "Voltage controlled filter"},
            {"name": "env~", "description": "Envelope follower"},
            {"name": "delwrite~", "description": "Delay writer"},
            {"name": "delread~", "description": "Delay reader"},
            {"name": "loadbang", "description": "Outputs a bang when the patch loads"},
            {"name": "metro", "description": "Metronome"},
            {"name": "random", "description": "Random number generator"},
            {"name": "counter", "description": "Counter"},
            {"name": "select", "description": "Route data based on matches"},
            {"name": "trigger", "description": "Trigger outputs in right-to-left order"},
            {"name": "pack", "description": "Pack data together"},
            {"name": "unpack", "description": "Unpack data"},
            {"name": "send", "description": "Send data through a named connection"},
            {"name": "receive", "description": "Receive data from a named connection"}
        ]
    }
    """

@mcp_server.resource("pd://port-info")
def get_port_info() -> str:
    """Get current port configuration.
    
    This resource provides information about the current OSC connection,
    including the host, port, and feedback port. This can be used to
    diagnose connection issues or to configure Pure Data to connect
    to the correct ports.
    
    Returns:
        JSON string with current port settings
        
    Example:
        A Claude client can access this using: @pd://port-info
    """
    global pd_osc
    if not pd_osc:
        return """
        {
            "status": "not_connected",
            "message": "OSC connection not initialized"
        }
        """
    
    return f"""
    {{
        "status": "connected",
        "host": "{pd_osc.host}",
        "port": {pd_osc.port},
        "feedback_port": {pd_osc.feedback_port}
    }}
    """

# Add a prompt for creating a simple oscillator patch
@mcp_server.prompt()
def create_oscillator_patch() -> str:
    """Prompt to create a simple oscillator patch.
    
    This prompt guides the user through creating a basic
    oscillator patch in Pure Data using the available tools.
    
    Returns:
        Prompt text
    """
    return """Please create a simple oscillator patch in Pure Data with the following components:
    
1. An oscillator (osc~) with a frequency of 440 Hz
2. A volume control (multiply by a value between 0 and 1)
3. Connect it to the audio output (dac~)
4. Enable DSP processing
    
You can use the create_object, connect_objects, and start_dsp tools to do this."""

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting MCP Server...")
    try:
        # Run the server directly when this module is executed
        asyncio.run(mcp_server.run(transport='stdio'))
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Error running server: {e}", exc_info=True)
