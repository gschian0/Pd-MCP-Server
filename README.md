# Pure Data MCP Server

This project provides integration between Claude AI and Pure Data through the Model Context Protocol (MCP). With this integration, Claude can dynamically create, modify, and control Pure Data patches through natural language.

## Known Issues
**The example patch (`example patch.pd`) is not working correctly.**

## Overview

The system consists of three core components:

1. **MCP Server** (`mcp_server.py`): Implements the Model Context Protocol interface for Claude
2. **OSC Daemon** (`osc_daemon.py`): Handles OSC communication with Pure Data
3. **Pure Data Patch** (`absolute_final_solution.pd`): A dynamic patching solution that receives OSC messages

## Features

- **Dynamic Object Creation**: Create any Pure Data object on demand through Claude
- **Connection Management**: Connect objects together to build complex signal flows
- **DSP Control**: Start and stop audio processing remotely
- **Parameter Control**: Modify parameters of objects in real-time
- **Global Object Tracking**: Reliable index-based connection system
- **Error Handling**: Robust error detection and reporting
- **Debugging Tools**: Comprehensive logging system

## Recent Updates


## Installation

### Prerequisites

- Python 3.7+ 
- Pure Data (vanilla) 0.51+ 
- Required Python packages:
  - `python-osc`
  - `fastmcp`
  - `jsonschema`
- [`uv` package manager](https://github.com/astral-sh/uv)

### **Install `uv`**

#### On macOS and Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### On Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Learn more: [astral-sh/uv](https://github.com/astral-sh/uv)

---
## 🛠️ Usage

### **Clone the repository**
```bash
git clone https://github.com/nikmaniatis/Pd-MCP-Server.git
```

### **Integration with Claude Desktop**

1. Open:
 
`Claude > Settings > Developer > Edit Config > claude_desktop_config.json`

2. Add the following block:
```json
{
    "mcpServers": {
      "Pure Data MCP Server": {
        "command": "uv",
        "args": [
          "--directory",
          "PATH_TO_PD_MCP_SERVER",
          "run",
          "main.py"
        ],
        "env": {
          "PD_OSC_HOST": "127.0.0.1",
          "PD_OSC_PORT": "5000",
          "PD_FEEDBACK_PORT": "5001"
        }
      }
    }
  }
```

> **Note:** If the `uv` command is not found, run `which uv` (Unix) or `Get-Command uv` (PowerShell) and use the full path in the `"command"` field.

---

## Architecture

### Message Flow

1. Claude executes MCP tools based on user requests
2. MCP Server processes the tool calls
3. OSC messages are formatted and sent to Pure Data
4. Pure Data executes the commands via the dynamic patch
5. Feedback (if any) is returned via OSC callbacks


## Troubleshooting

### Common Issues

1. **Object Creation Fails**: Ensure Pure Data is running and the patch is open
2. **Connection Issues**: Verify that object IDs match exactly what was returned from `create_object`
3. **Port Conflicts**: Check if port 5000 is already in use
4. **Message Format Errors**: Ensure message formats match the expected format in the Pure Data patch
5. **Lost Objects**: If object tracking gets confused, try restarting both the MCP server and Pure Data

## JSON Schema

The `pd-schema.json` provides a comprehensive data model for Pure Data patches, supporting validation and serialization of patches. While not directly used in the current MCP tools, it serves as a reference for future development and potential integration with patch serialization/deserialization features.

## Next Steps

1. **Enhanced Error Reporting**: Improve feedback from Pure Data for better error messages
2. **Visualization Tools**: Add tools to visualize the current patch state
3. **Object Library Integration**: Support loading external libraries and abstractions
4. **Patch Persistence**: Implement better state management for patches
5. **Audio File Support**: Add tools for working with audio files and samples
6. **MIDI Integration**: Add MIDI input/output capabilities
7. **GUI Object Support**: Add support for GUI objects like sliders and number boxes
8. **Collaborative Features**: Support multiple simultaneous connections
9. **Documentation Generator**: Create automatic documentation from the JSON schema


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Pure Data](https://puredata.info/) - The open source visual programming language
- [Model Context Protocol](https://modelcontextprotocol.io) - The protocol enabling AI tools
- [Python-OSC](https://github.com/attwad/python-osc) - Python implementation of OSC