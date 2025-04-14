#!/usr/bin/env python
"""
Port Checker for Pure Data MCP Server

This script checks if the ports needed for the Pd-MCP server are available.
"""

import socket
import sys

def check_port(port, host='127.0.0.1'):
    """Check if a port is available on the specified host."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def main():
    """Main function to check the default Pure Data MCP ports."""
    ports_to_check = [
        (5000, "Pure Data OSC port (for sending commands)"),
        (5001, "Pure Data feedback port (for receiving feedback)"),
        (5002, "Alternative feedback port")
    ]
    
    print("🔍 Checking port availability for Pure Data MCP Server...")
    print("---------------------------------------------------")
    
    all_available = True
    
    for port, description in ports_to_check:
        available = check_port(port)
        status = "✅ Available" if available else "❌ In Use"
        print(f"Port {port} ({description}): {status}")
        
        if not available:
            all_available = False
    
    print("---------------------------------------------------")
    
    if all_available:
        print("🎉 All default ports are available! You can use the default settings.")
    else:
        print("⚠️ Some ports are in use. Consider the following options:")
        print("1. Use different ports in your configuration")
        print("2. Stop the processes using these ports")
        print("3. Use the automatic port selection feature in the updated OSC daemon")
        print("\nTo identify processes using these ports, run:")
        print("  On macOS/Linux: sudo lsof -i :<port>")
        print("  On Windows: netstat -ano | findstr :<port>")

if __name__ == "__main__":
    main() 