#!/usr/bin/env python
"""
PD-MCP Server Installer for Claude Desktop

This script installs the Pure Data MCP server for Claude Desktop by:
1. Detecting the Claude Desktop configuration file location
2. Creating the proper configuration entry
3. Restarting Claude Desktop if necessary
"""

import json
import os
import platform
import subprocess
import sys
import socket
from pathlib import Path

def get_claude_config_path():
    """Get the path to the Claude Desktop configuration file."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        raise ValueError(f"Unsupported operating system: {system}")

def check_port_available(host, port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def create_mcp_server_config(project_path, osc_host="127.0.0.1", osc_port=5000, feedback_port=5001):
    """Create the MCP server configuration for Claude Desktop.
    
    Args:
        project_path: Path to the project directory
        osc_host: Host for Pure Data OSC communication
        osc_port: Port for sending commands to Pure Data
        feedback_port: Port for receiving feedback from Pure Data
    """
    absolute_path = Path(project_path).resolve()
    
    return {
        "Pure Data Controller": {
            "command": "/Users/nikmaniatis/.local/bin/uv",
            "args": [
                "--directory",
                str(absolute_path),
                "run",
                "main.py"
            ],
            "env": {
                "PD_OSC_HOST": osc_host,
                "PD_OSC_PORT": str(osc_port),
                "PD_FEEDBACK_PORT": str(feedback_port)
            }
        }
    }

def install_mcp_server():
    """Install the Pure Data MCP server for Claude Desktop."""
    print("🎵 Installing Pure Data MCP Server for Claude Desktop...")
    
    # Get the project path (current directory)
    project_path = os.getcwd()
    
    # Get OSC configuration settings
    osc_host = input("Enter OSC host (default: 127.0.0.1): ") or "127.0.0.1"
    
    while True:
        try:
            osc_port = int(input("Enter OSC port (default: 5000): ") or "5000")
            break
        except ValueError:
            print("❌ Port must be a number. Please try again.")
    
    while True:
        try:
            feedback_port = int(input("Enter feedback port (default: 5001): ") or "5001")
            
            # Check if port is available
            if not check_port_available(osc_host, feedback_port):
                print(f"⚠️ Warning: Port {feedback_port} is already in use.")
                use_anyway = input(f"Use port {feedback_port} anyway? (y/n): ")
                if use_anyway.lower() != "y":
                    continue
            
            break
        except ValueError:
            print("❌ Port must be a number. Please try again.")
    
    # Get the Claude Desktop config path
    try:
        config_path = get_claude_config_path()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Check if Claude Desktop configuration exists
    if not config_path.exists():
        print(f"❌ Claude Desktop configuration not found at {config_path}")
        print("Please make sure Claude Desktop is installed and has been run at least once.")
        return
    
    # Load existing configuration
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Error decoding Claude Desktop configuration.")
        print("The configuration file might be corrupted. Please reinstall Claude Desktop.")
        return
    except Exception as e:
        print(f"❌ Error reading Claude Desktop configuration: {e}")
        return
    
    # Create backup of existing configuration
    backup_path = config_path.with_suffix(".json.backup")
    try:
        with open(backup_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Created backup of existing configuration at {backup_path}")
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return
    
    # Update the configuration
    mcp_server_config = create_mcp_server_config(
        project_path,
        osc_host=osc_host,
        osc_port=osc_port,
        feedback_port=feedback_port
    )
    
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Check if the MCP server already exists
    if "Pure Data Controller" in config.get("mcpServers", {}):
        replace = input("Pure Data Controller is already configured. Replace it? (y/n): ")
        if replace.lower() != "y":
            print("Installation canceled.")
            return
    
    # Update or add the MCP server configuration
    config["mcpServers"].update(mcp_server_config)
    
    # Save the updated configuration
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Updated Claude Desktop configuration at {config_path}")
    except Exception as e:
        print(f"❌ Error updating Claude Desktop configuration: {e}")
        print(f"Restoring backup...")
        with open(backup_path, "r") as f:
            backup_config = json.load(f)
        with open(config_path, "w") as f:
            json.dump(backup_config, f, indent=2)
        return
    
    # Print usage instructions
    print("\n📋 Pure Data Setup Instructions:")
    print(f"1. Open Pure Data")
    print(f"2. Add [netreceive -u -b {osc_port}] for receiving OSC commands")
    print(f"3. Add [netsend -u -b {osc_host} {feedback_port}] for sending feedback")
    
    # Ask to restart Claude Desktop
    if platform.system() == "Darwin":  # macOS
        restart = input("Do you want to restart Claude Desktop now? (y/n): ")
        if restart.lower() == "y":
            try:
                subprocess.run(["killall", "Claude"])
                subprocess.run(["open", "-a", "Claude"])
                print("✅ Claude Desktop has been restarted.")
            except Exception as e:
                print(f"❌ Error restarting Claude Desktop: {e}")
                print("Please restart Claude Desktop manually.")
    else:
        print("Please restart Claude Desktop to apply the changes.")
    
    print("\n🎉 Pure Data MCP Server has been successfully installed!")
    print("You can now use it in Claude Desktop by typing '@Pure Data Controller'")

if __name__ == "__main__":
    install_mcp_server() 