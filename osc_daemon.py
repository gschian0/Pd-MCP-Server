"""
Pure Data OSC Communication Module

This module provides the core functionality for communicating with Pure Data via the OSC
(Open Sound Control) protocol. It includes:

1. Client functionality for sending OSC messages to Pure Data
2. Server functionality for receiving feedback/responses from Pure Data
3. Port management with fallback mechanism
4. Callback registration for handling OSC messages

The main class, PureDataOSC, handles both directions of communication and ensures
that the server can continue functioning even if the primary port is unavailable.

Usage:
    pd_osc = PureDataOSC()
    pd_osc.send_message('/pd/create', ['osc~', 440])
    pd_osc.register_feedback_handler('/pd/feedback/*', my_handler_function)
    await pd_osc.start_server()
"""

import logging
import asyncio
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
from typing import Callable, Dict, List, Optional, Union, Any

class PureDataOSC:
    """A class for bidirectional OSC communication with Pure Data.
    
    This class handles both sending commands to Pure Data and receiving feedback
    from it. It includes port fallback mechanisms to handle cases where the 
    primary port is already in use.
    
    The OSC server binds to the feedback port to listen for messages from Pure Data,
    while the OSC client sends messages to Pure Data on the specified port.
    
    Attributes:
        host: The hostname for OSC communication
        port: The port for sending commands to Pure Data
        feedback_port: The port for receiving feedback from Pure Data
        retry_count: Number of alternative ports to try if primary is in use
        osc_client: The client for sending OSC messages
        dispatcher: The OSC message dispatcher for handling incoming messages
        feedback_handlers: Registered callback handlers for feedback messages
        object_indices: Dictionary mapping object IDs to their numeric indices
    """
    
    def __init__(
        self, 
        host: str = "127.0.0.1", 
        port: int = 5000, 
        feedback_port: int = 5001,
        retry_count: int = 5
    ):
        """Initialize the Pure Data OSC interface.
        
        Args:
            host: The Pure Data OSC host (default: 127.0.0.1)
            port: The port for sending commands to Pd (default: 5000)
            feedback_port: The port for receiving feedback from Pd (default: 5001)
            retry_count: Number of alternate ports to try if the specified one is in use (default: 5)
                         For example, if 5001 is in use, it will try 5002, 5003, etc.
        """
        self.host = host
        self.port = port
        self.feedback_port = feedback_port
        self.retry_count = retry_count
        self.osc_client = SimpleUDPClient(self.host, self.port)
        self.dispatcher = Dispatcher()
        self.feedback_handlers: Dict[str, List[Callable]] = {}
        
        # NEW: Add tracking for object indices to support our numeric indexing system
        self.object_indices: Dict[str, int] = {}
        self.next_index = 0
        
        # Configure default feedback handler to route incoming messages
        self.dispatcher.map("/pd/feedback/*", self._handle_feedback)
    
    def send_message(self, command: str, args: List[Any] = []) -> bool:
        """Sends an OSC command to Pure Data.
        
        This method handles sending commands to Pure Data and also takes care of
        automatically refreshing the GUI when needed for commands that modify the patch.
        
        Args:
            command: The OSC address to send to (e.g., "/pd/create")
            args: List of arguments for the OSC message
            
        Returns:
            True if successful, False otherwise
            
        Example:
            pd_osc.send_message("/pd/create", ["osc~", 100, 100, 440])
        """
        try:
            # NEW: Debug log to show exactly what we're sending
            args_str = ', '.join([str(arg) for arg in args])
            logging.debug(f"OSC Message Format: {command} [{args_str}]")
            
            # Send the original command
            self.osc_client.send_message(command, args)
            logging.info(f"➡️ Sent to Pd: {command} {args}")
            
            # Force GUI refresh after commands that modify the patch
            # Skip for commands that don't modify the visual patch
            if any(cmd in command for cmd in ['/pd/create', '/pd/delete', '/pd/connect', '/pd/disconnect']):
                # We use several different refresh methods because Pure Data's GUI refresh
                # behavior can be inconsistent. By sending multiple types of refresh commands,
                # we increase the likelihood that the GUI will update properly.
                
                # 1. Send direct GUI refresh command
                self.osc_client.send_message("/pd/gui_refresh", [1])
                
                # 2. Send a print message that will cause activity in the patch
                self.osc_client.send_message("/pd/print", ["GUI refresh triggered"])
                
                # 3. Use the 'pd' message system (built into Pd) 
                self.osc_client.send_message("/pd", ["refresh"])
                
                logging.debug("➡️ Sent GUI refresh commands to Pd")
            
            return True
        except Exception as e:
            logging.error(f"❌ Error sending OSC message: {e}")
            return False
    
    # NEW: Method for dynamic patch object creation with correct format for absolute_final_solution.pd
    def create_object(self, object_type: str, x: int, y: int, *args) -> int:
        """Creates an object in Pure Data with the absolute_final_solution.pd format.
        
        This method creates an object in the Pure Data patch and tracks its index
        for later use in connections.
        
        Args:
            object_type: Type of Pure Data object (e.g., "osc~", "dac~")
            x: X coordinate on the canvas
            y: Y coordinate on the canvas
            *args: Additional arguments for the object
            
        Returns:
            The index of the created object
            
        Example:
            index = pd_osc.create_object("osc~", 100, 100, 440)
        """
        # Create a unique ID for this object based on type and position
        object_id = f"{object_type}_{x}_{y}"
        
        # Assign a numeric index to this object
        object_index = self.next_index
        self.next_index += 1
        
        # Store the mapping for future reference
        self.object_indices[object_id] = object_index
        
        # Send the create message in the correct format
        # Format: [object_type, x, y, *args]
        self.send_message("/pd/create", [object_type, x, y] + list(args))
        
        return object_index
    
    # NEW: Method for connecting objects using numeric indices
    def connect_objects_by_index(self, source_index: int, source_outlet: int, 
                                 dest_index: int, dest_inlet: int) -> bool:
        """Connects two Pure Data objects using their numeric indices.
        
        This method is designed to work with the absolute_final_solution.pd format
        which uses numeric indices for connections.
        
        Args:
            source_index: Index of the source object
            source_outlet: Outlet number of the source object
            dest_index: Index of the destination object
            dest_inlet: Inlet number of the destination object
            
        Returns:
            True if successful, False otherwise
            
        Example:
            pd_osc.connect_objects_by_index(0, 0, 1, 0)
        """
        return self.send_message("/pd/connect", [source_index, source_outlet, dest_index, dest_inlet])
    
    # NEW: Method for connecting objects using their IDs
    def connect_objects_by_id(self, source_id: str, source_outlet: int,
                             dest_id: str, dest_inlet: int) -> bool:
        """Connects two Pure Data objects using their string IDs.
        
        This method looks up the numeric indices for the given object IDs
        and then connects them using the absolute_final_solution.pd format.
        
        Args:
            source_id: ID of the source object
            source_outlet: Outlet number of the source object
            dest_id: ID of the destination object
            dest_inlet: Inlet number of the destination object
            
        Returns:
            True if successful, False otherwise
            
        Example:
            pd_osc.connect_objects_by_id("osc~_100_100", 0, "dac~_200_100", 0)
        """
        # Check if we have indices for these objects
        if source_id not in self.object_indices:
            logging.error(f"Unknown source object ID: {source_id}")
            return False
        
        if dest_id not in self.object_indices:
            logging.error(f"Unknown destination object ID: {dest_id}")
            return False
        
        # Get the indices
        source_index = self.object_indices[source_id]
        dest_index = self.object_indices[dest_id]
        
        # Connect using indices
        return self.connect_objects_by_index(source_index, source_outlet, dest_index, dest_inlet)
    
    def register_feedback_handler(self, address: str, handler: Callable) -> None:
        """Register a handler for feedback messages from Pure Data.
        
        This method allows registering callback functions that will be called
        when messages matching the specified address pattern are received.
        
        Args:
            address: The OSC address pattern to listen for (e.g., "/pd/feedback/volume")
                    Can include wildcards like "*" and "?"
            handler: A function that takes (address, *args) as parameters
            
        Example:
            pd_osc.register_feedback_handler("/pd/feedback/volume", handle_volume_change)
        """
        if address not in self.feedback_handlers:
            self.feedback_handlers[address] = []
        self.feedback_handlers[address].append(handler)
    
    def _handle_feedback(self, address: str, *args: Any) -> None:
        """Internal handler for feedback messages from Pure Data.
        
        This method is called by the OSC dispatcher when a message is received.
        It routes the message to all registered handlers whose pattern matches
        the received address.
        
        Args:
            address: The OSC address received
            args: The arguments sent with the OSC message
        """
        logging.info(f"⬅️ Received from Pd: {address} {args}")
        
        # Call registered handlers for this address
        for pattern, handlers in self.feedback_handlers.items():
            import re
            # Convert OSC-style pattern to regex
            # * matches any sequence of characters except /
            # ? matches any single character
            pattern_regex = pattern.replace("*", "[^/]+").replace("?", ".")
            if re.match(pattern_regex, address):
                for handler in handlers:
                    try:
                        handler(address, *args)
                    except Exception as e:
                        logging.error(f"Error in feedback handler: {e}")
    
    async def start_server(self) -> None:
        """Start the OSC server to receive messages from Pure Data.
        
        This method sets up the UDP server to listen for OSC messages from Pure Data.
        It implements a port fallback mechanism to handle cases where the primary
        feedback port is already in use.
        
        The method will attempt to bind to the configured feedback port first.
        If that port is in use, it will try incremental ports (e.g., 5001, 5002, etc.)
        up to retry_count times before giving up.
        
        IMPORTANT: This method should only be called ONCE per application instance.
        Multiple calls can lead to binding multiple ports unnecessarily.
        
        Raises:
            OSError: If unable to bind to any port after retry_count attempts
        """
        original_port = self.feedback_port
        current_attempt = 0
        
        # Log the call stack to help diagnose multiple initialization issues
        logging.info(f"Starting OSC server... (called from {__import__('traceback').format_stack()[-2]})")
        
        while current_attempt <= self.retry_count:
            try:
                # Create the server with the current feedback port
                server = AsyncIOOSCUDPServer(
                    (self.host, self.feedback_port), 
                    self.dispatcher, 
                    asyncio.get_event_loop()
                )
                
                # This is where binding to the port happens
                # If the port is in use, this will raise an OSError
                await server.create_serve_endpoint()
                
                # Log a warning if we had to use an alternate port
                if self.feedback_port != original_port:
                    logging.warning(f"Using alternate feedback port: {self.feedback_port} (original port {original_port} was in use)")
                    logging.warning(f"Make sure Pure Data is configured to send to port {self.feedback_port}")
                    
                logging.info(f"OSC server listening for feedback on {self.host}:{self.feedback_port}")
                return
                
            except OSError as e:
                if "Address already in use" in str(e) and current_attempt < self.retry_count:
                    # Try the next port
                    self.feedback_port += 1
                    current_attempt += 1
                    logging.warning(f"Port {self.feedback_port-1} is in use, trying port {self.feedback_port}")
                else:
                    # Either we've exhausted our retry attempts or encountered a different error
                    if current_attempt >= self.retry_count:
                        logging.error(f"Failed to bind to any port after {self.retry_count} attempts. Please check for running processes.")
                    else:
                        logging.error(f"Error starting OSC server: {e}")
                    raise

# Default handler for feedback messages
async def default_osc_feedback_handler(address: str, *args: Any) -> None:
    """Default handler for feedback messages from Pure Data.
    
    This function demonstrates how to handle specific OSC messages from Pd.
    It can be registered as a handler for feedback messages.
    
    Args:
        address: The OSC address received
        args: The arguments sent with the OSC message
        
    Example:
        pd_osc.register_feedback_handler("/pd/feedback/*", default_osc_feedback_handler)
    """
    pd_osc = PureDataOSC()
    
    if address == "/pd/feedback/clipping_detected":
        logging.warning("🚨 Clipping detected! Lowering master volume.")
        pd_osc.send_message("/pd/set/master/volume", [0.8])
    elif address == "/pd/feedback/low_volume":
        logging.info("🔊 Low volume detected. Increasing volume.")
        pd_osc.send_message("/pd/set/master/volume", [1.0])

# For standalone usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting OSC Daemon for Pure Data...")
    
    async def run_osc_daemon():
        """Run the OSC daemon in standalone mode."""
        pd_osc = PureDataOSC()
        pd_osc.register_feedback_handler("/pd/feedback/*", default_osc_feedback_handler)
        await pd_osc.start_server()
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    
    asyncio.run(run_osc_daemon())