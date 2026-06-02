# Pure Data MCP Server

This project provides integration between Claude AI and Pure Data through the Model Context Protocol (MCP). With this integration, Claude can dynamically create, modify, and control Pure Data patches through natural language.

## Overview

The system consists of three core components:

1. **MCP Server** (`mcp_server.py`): Implements the Model Context Protocol interface for Claude
2. **OSC Daemon** (`osc_daemon.py`): Handles OSC communication with Pure Data
3. **Pure Data Patch** (`example_patch.pd`): A dynamic patching solution that receives OSC messages

## Features

- **Dynamic Object Creation**: Create any Pure Data object on demand through Claude
- **Connection Management**: Connect objects together to build complex signal flows
- **Workspace Management**: Clear all objects and reset state with `clear_workspace`
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

## Quick Example

Once the MCP server is connected and the Pd patch is listening, you can ask Claude to build patches using natural language:

> "Create an osc~ at 440 Hz, connect it to a dac~, and start DSP."

Claude will call the MCP tools to produce something like:

```
create_object("osc~", ["440"], {"x": 100, "y": 50})   → index 0
create_object("*~",   ["0.25"], {"x": 100, "y": 110})  → index 1
create_object("dac~", [],       {"x": 100, "y": 170})  → index 2

connect_objects({"id": "osc~_100_50",  "port": 0}, {"id": "*~_100_110",  "port": 0})
connect_objects({"id": "*~_100_110",   "port": 0}, {"id": "dac~_100_170", "port": 0})
connect_objects({"id": "*~_100_110",   "port": 0}, {"id": "dac~_100_170", "port": 1})

start_dsp()
```

This creates the following patch in the workspace subpatch:

```
  osc~ 440
     |
  *~ 0.25 (volume)
    / \
  dac~ L+R
```

You can then ask Claude to modify the patch, add effects, change frequencies, or build more complex signal chains — all through conversation.

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



## Known Limitations

- **No delete or disconnect support**: The Pd patch (`example_patch.pd`) only handles `/pd/create`, `/pd/connect`, `/pd/dsp`, and `/pd/clear`. Objects and connections cannot be individually removed — use `clear_workspace` to reset the entire workspace instead.
- **Signal objects with zero arguments**: When signal objects like `+~` or `*~` are created with a `0` argument via dynamic patching (e.g., `obj 100 100 +~ 0`), Pd 0.55+ treats the second inlet as a float inlet instead of a signal inlet, breaking signal connections. The MCP server automatically strips trailing zero arguments from signal objects to avoid this issue.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Pure Data](https://puredata.info/) - The open source visual programming language
- [Model Context Protocol](https://modelcontextprotocol.io) - The protocol enabling AI tools
- [Python-OSC](https://github.com/attwad/python-osc) - Python implementation of OSC