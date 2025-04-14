# Implementing MCP Extensions for Pure Data

This document provides detailed instructions for implementing MCP (Model Context Protocol) extensions for Pure Data integration. It serves as a guide for future developers to ensure consistent implementation patterns across the codebase.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Implementing MCP Tools](#implementing-mcp-tools)
3. [Implementing MCP Resources](#implementing-mcp-resources)
4. [Implementing MCP Prompts](#implementing-mcp-prompts)
5. [Message Format Standards](#message-format-standards)
6. [Object Tracking System](#object-tracking-system)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Testing and Validation](#testing-and-validation)
9. [Documentation Standards](#documentation-standards)
10. [Integration with the Schema](#integration-with-the-schema)

## Architecture Overview

The MCP-Pure Data integration follows a layered architecture:

1. **MCP Layer**: Implements the Model Context Protocol interface for Claude AI
   - Defines tools, resources, and prompts
   - Handles context management
   - Provides an API for Claude to control Pure Data

2. **OSC Layer**: Manages communication with Pure Data
   - Formats and sends OSC messages
   - Receives feedback from Pure Data
   - Provides abstractions over the raw OSC protocol

3. **Pure Data Layer**: A dynamic patching solution that receives OSC messages
   - Processes incoming OSC commands
   - Creates and manipulates Pure Data objects
   - Provides feedback on operations

When implementing new features, you need to ensure that all three layers are properly addressed.

## Implementing MCP Tools

MCP tools are the primary way for Claude to interact with Pure Data. Follow these steps to implement a new tool:

### Step 1: Define the Tool Function

Tools are implemented as Python functions decorated with `@mcp_server.tool()`. Follow this pattern:

```python
@mcp_server.tool()
def tool_name(param1: type1, param2: type2, ctx: Context) -> Dict[str, Any]:
    """Tool docstring with detailed description.
    
    Explain what the tool does, its parameters, and any side effects.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        ctx: MCP context
        
    Returns:
        Response dictionary with status and any relevant data
        
    Example:
        Example usage of the tool
    """
    # Get the OSC client from context
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    # Log the operation
    logging.info(f"Operation description: {param1}, {param2}")
    
    # Format and send OSC message
    pd_osc.send_message("/pd/command", [param1, param2])
    
    # Return response
    return {"status": "success", "data": some_data}
```

### Step 2: Handle Object Tracking (if needed)

If your tool creates or manipulates objects, update the object tracking system:

```python
# For object creation:
object_id = f"{object_type}_{position['x']}_{position['y']}"
object_indices[object_id] = next_index
next_index += 1

# For object deletion:
if object_id in object_indices:
    del object_indices[object_id]
```

### Step 3: Implement Input Validation

Always validate inputs before sending them to Pure Data:

```python
# Validate position coordinates
if position["x"] < 0 or position["y"] < 0:
    return {"status": "error", "message": "Invalid position coordinates"}

# Validate parameter values
if not isinstance(value, (int, float)) or value < min_value or value > max_value:
    return {"status": "error", "message": f"Value must be between {min_value} and {max_value}"}
```

### Step 4: Format OSC Messages

Follow these message format standards:

- Object Creation: `/pd/create [object_type, x, y, *args]`
- Object Connection: `/pd/connect [source_index, source_port, dest_index, dest_port]`
- Object Deletion: `/pd/delete [object_id]`
- Parameter Setting: `/pd/set/{object_id}/{parameter} [value]`
- DSP Control: `/pd/dsp [state]`

### Example: Implementing a new tool

Here's a complete example for a tool that creates a slider GUI object:

```python
@mcp_server.tool()
def create_slider(position: Dict[str, int], min_value: float, max_value: float, 
                 default: float, orientation: str, ctx: Context) -> Dict[str, Any]:
    """Create a slider GUI object in Pure Data.
    
    This tool creates a slider (horizontal or vertical) with the specified range
    and default value.
    
    Args:
        position: Position on the canvas (x, y coordinates)
        min_value: Minimum value of the slider
        max_value: Maximum value of the slider
        default: Default value of the slider
        orientation: Either "horizontal" or "vertical"
        ctx: MCP context
        
    Returns:
        Response with object ID and status
        
    Example:
        create_slider({"x": 100, "y": 100}, 0, 127, 64, "horizontal", ctx)
    """
    global object_indices, next_index
    
    # Get OSC client from context
    pd_osc = ctx.request_context.lifespan_context.get("pd_osc")
    if not pd_osc:
        return {"status": "error", "message": "OSC connection not initialized"}
    
    # Validate inputs
    if position["x"] < 0 or position["y"] < 0:
        return {"status": "error", "message": "Invalid position coordinates"}
    
    if min_value >= max_value:
        return {"status": "error", "message": "Minimum value must be less than maximum value"}
    
    if default < min_value or default > max_value:
        return {"status": "error", "message": "Default value must be between min and max"}
    
    if orientation not in ["horizontal", "vertical"]:
        return {"status": "error", "message": "Orientation must be 'horizontal' or 'vertical'"}
    
    # Determine the object type based on orientation
    object_type = "hsl" if orientation == "horizontal" else "vsl"
    
    # Log the operation
    logging.info(f"Creating {orientation} slider at position {position} with range [{min_value}, {max_value}]")
    
    # Send the create command to Pure Data
    pd_osc.send_message("/pd/create", [object_type, position["x"], position["y"], 
                                       min_value, max_value, default])
    
    # Track the object
    object_index = next_index
    next_index += 1
    object_id = f"{object_type}_{position['x']}_{position['y']}"
    object_indices[object_id] = object_index
    
    return {"status": "success", "object_id": object_id, "object_index": object_index}
```

## Implementing MCP Resources

MCP resources provide information to Claude about Pure Data's capabilities. Follow these steps to implement a new resource:

### Step 1: Define the Resource Function

Resources are implemented as Python functions decorated with `@mcp_server.resource()`. Follow this pattern:

```python
@mcp_server.resource("pd://resource-name")
def get_resource_name() -> str:
    """Resource docstring with detailed description.
    
    Explain what information the resource provides and how it can be used.
    
    Returns:
        JSON string with resource data
        
    Example:
        A Claude client can access this using: @pd://resource-name
    """
    # Generate or retrieve the resource data
    data = {
        "key1": "value1",
        "key2": "value2",
        # ...
    }
    
    # Return as a formatted JSON string
    return json.dumps(data, indent=2)
```

### Step 2: Ensure JSON Formatting

Resources must return valid JSON strings. Use the `json` module to ensure proper formatting:

```python
import json

# For static data:
return json.dumps(data, indent=2)

# For dynamic data:
return json.dumps({
    "status": "connected",
    "host": pd_osc.host,
    "port": pd_osc.port,
    "feedback_port": pd_osc.feedback_port
}, indent=2)
```

### Example: Implementing a new resource

Here's a complete example for a resource that lists available audio effects:

```python
@mcp_server.resource("pd://audio-effects")
def get_audio_effects() -> str:
    """Get a list of available audio effect objects in Pure Data.
    
    This resource provides information about the audio effect objects
    available in Pure Data, including their names, descriptions,
    and typical parameter ranges.
    
    Returns:
        JSON string with audio effect information
        
    Example:
        A Claude client can access this using: @pd://audio-effects
    """
    effects = [
        {
            "name": "freeverb~",
            "description": "Reverb effect based on Freeverb",
            "parameters": [
                {"name": "room_size", "min": 0, "max": 1, "default": 0.5},
                {"name": "damping", "min": 0, "max": 1, "default": 0.5},
                {"name": "width", "min": 0, "max": 1, "default": 1.0},
                {"name": "wet", "min": 0, "max": 1, "default": 0.33}
            ]
        },
        {
            "name": "delay~",
            "description": "Simple delay effect",
            "parameters": [
                {"name": "delay_time", "min": 0, "max": 5000, "default": 500},
                {"name": "feedback", "min": 0, "max": 1, "default": 0.5}
            ]
        },
        # Add more effects here...
    ]
    
    return json.dumps({"effects": effects}, indent=2)
```

## Implementing MCP Prompts

MCP prompts provide guidance to Claude on how to accomplish common tasks. Follow these steps to implement a new prompt:

### Step 1: Define the Prompt Function

Prompts are implemented as Python functions decorated with `@mcp_server.prompt()`. Follow this pattern:

```python
@mcp_server.prompt()
def prompt_name() -> str:
    """Prompt docstring with detailed description.
    
    Explain what the prompt helps Claude accomplish and any key concepts it introduces.
    
    Returns:
        Prompt text
    """
    return """
    Detailed instructions for Claude on how to accomplish a specific task.
    
    1. Step one details
    2. Step two details
    3. Step three details
    
    Additional guidance, tips, or explanations can be included here.
    """
```

### Step 2: Structure the Prompt Content

Effective prompts should:
- Start with a clear goal statement
- Provide step-by-step instructions
- Reference specific tools to use
- Include examples of expected output or behavior
- Anticipate common errors and provide solutions

### Example: Implementing a new prompt

Here's a complete example for a prompt that guides creating a drum machine:

```python
@mcp_server.prompt()
def create_drum_machine() -> str:
    """Prompt to create a drum machine patch in Pure Data.
    
    This prompt guides the user through creating a basic drum machine
    with multiple sample players triggered by a sequencer.
    
    Returns:
        Prompt text
    """
    return """Please create a basic drum machine in Pure Data with the following components:
    
1. A central metro object running at 120 BPM (500ms)
2. A counter to track beat position (0-15 for a 16-step pattern)
3. Four sample players for different drum sounds:
   - Kick drum sample
   - Snare drum sample
   - Hi-hat closed sample
   - Hi-hat open sample
4. Select objects to trigger each sample at specific beat positions
5. Volume controls for each sample
6. A master output with volume control
7. Enable DSP processing
    
For each sample player, you'll need:
- A table to hold the sample data (you can use dummy data for now)
- A tabplay~ object to play the sample
- A trigger mechanism using the select object
- A multiplication for volume control
- A connection to the master output
    
You can use the following tools:
- create_object: For creating all the Pure Data objects
- connect_objects: For connecting them together
- set_param: For setting the BPM and pattern values
- start_dsp: To enable audio processing
    
When you're done, the patch should be able to play a 16-step drum pattern automatically.
"""
```

## Message Format Standards

When implementing new tools, adhere to these message format standards:

### Object Creation
```
/pd/create [object_type, x, y, *args]
```

- `object_type`: String (e.g., "osc~", "dac~")
- `x`, `y`: Integer coordinates
- `*args`: Optional arguments for the object

### Object Connection
```
/pd/connect [source_index, source_port, dest_index, dest_port]
```

- `source_index`, `dest_index`: Integer indices from the object tracking system
- `source_port`, `dest_port`: Integer outlet/inlet numbers (0-based)

### Parameter Setting
```
/pd/set/{object_id}/{parameter} [value]
```

- `object_id`: String ID from object creation
- `parameter`: String parameter name
- `value`: The new parameter value (type depends on parameter)

### DSP Control
```
/pd/dsp [state]
```

- `state`: 1 for on, 0 for off

## Object Tracking System

The object tracking system is crucial for maintaining connections between objects. When implementing new tools that create or manipulate objects, ensure you:

1. **Assign unique indices**: Use the global `next_index` counter
2. **Generate consistent object IDs**: Use the format `{object_type}_{x}_{y}`
3. **Update the tracking dictionary**: Add new objects to `object_indices`
4. **Clean up on deletion**: Remove deleted objects from the tracking system

Example:
```python
# Creating an object
object_index = next_index
next_index += 1
object_id = f"{object_type}_{position['x']}_{position['y']}"
object_indices[object_id] = object_index

# Deleting an object
if object_id in object_indices:
    del object_indices[object_id]
```

## Error Handling Patterns

Follow these error handling patterns for consistent user experience:

1. **Input validation**: Validate all inputs before sending to Pure Data
2. **Comprehensive error messages**: Provide clear, actionable error messages
3. **Graceful fallbacks**: When possible, provide fallback behavior
4. **Detailed logging**: Log all operations and errors for debugging

Example:
```python
# Input validation with clear error message
if position["x"] < 0 or position["y"] < 0:
    logging.error(f"Invalid position coordinates: {position}")
    return {"status": "error", "message": "Position coordinates must be non-negative"}

# Fallback behavior
if source_id not in object_indices:
    logging.warning(f"Source object ID not found: {source_id}, assigning new index")
    object_indices[source_id] = next_index
    next_index += 1
```

## Testing and Validation

Before submitting a new extension, implement these testing procedures:

1. **Unit testing**: Write tests for edge cases and parameter validation
2. **Integration testing**: Test the OSC message flow with Pure Data
3. **Validation against schema**: Ensure conformance with `pd-schema.json`
4. **Documentation verification**: Check that docstrings and examples are accurate

Example unit test for a new tool:
```python
def test_create_slider():
    # Test normal operation
    result = create_slider({"x": 100, "y": 100}, 0, 127, 64, "horizontal", mock_context)
    assert result["status"] == "success"
    assert "object_id" in result
    
    # Test invalid position
    result = create_slider({"x": -10, "y": 100}, 0, 127, 64, "horizontal", mock_context)
    assert result["status"] == "error"
    assert "position" in result["message"]
    
    # Test invalid range
    result = create_slider({"x": 100, "y": 100}, 100, 0, 50, "horizontal", mock_context)
    assert result["status"] == "error"
    assert "minimum" in result["message"]
```

## Documentation Standards

Follow these documentation standards:

1. **Comprehensive docstrings**: Include purpose, parameters, return values, and examples
2. **Consistent formatting**: Use Google-style docstring format
3. **Include examples**: Provide usage examples in docstrings
4. **Update README**: Add new tools, resources, and prompts to the README
5. **Update commands.md**: Add new entries to the commands list

Example docstring:
```python
"""Create a new Pd object.
    
This tool creates a new object in the Pure Data patch at the specified position.
The object can be any valid Pd object type (e.g., osc~, dac~) with optional arguments.
    
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
```

## Integration with the Schema

The `pd-schema.json` file provides a comprehensive data model for Pure Data patches. When implementing new extensions:

1. **Review the schema**: Understand how your extension fits into the data model
2. **Validate against schema**: Ensure your tools produce valid data
3. **Update schema if needed**: If your extension introduces new concepts, update the schema
4. **Consider serialization**: Think about how your extension affects patch serialization

Example schema validation:
```python
def validate_object_creation(object_type, args, position):
    # Load the schema
    with open('pd-schema.json', 'r') as f:
        schema = json.load(f)
    
    # Create a representation of the object
    object_data = {
        "type": object_type,
        "args": args,
        "position": position
    }
    
    # Validate against the schema
    try:
        jsonschema.validate(object_data, schema["definitions"]["PdObject"])
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)
```

## Advanced Implementation Patterns

### Working with Audio Files and Samples

```python
@mcp_server.tool()
def load_sample(file_path: str, position: Dict[str, int], ctx: Context) -> Dict[str, Any]:
    """Load an audio sample into a table.
    
    This tool creates a table object and loads an audio sample from the specified path.
    It then returns the table's object ID for further manipulation.
    
    Args:
        file_path: Path to the audio file
        position: Position on the canvas (x, y coordinates)
        ctx: MCP context
        
    Returns:
        Response with table object ID and status
    """
    global object_indices, next_index
    
    # Implementation details...
    # 1. Create a table object
    # 2. Send a message to load the sample
    # 3. Track the object
    # 4. Return the object ID
```

### Working with MIDI

```python
@mcp_server.tool()
def send_midi_note(note: int, velocity: int, channel: int, ctx: Context) -> Dict[str, str]:
    """Send a MIDI note message.
    
    This tool sends a MIDI note message through Pure Data's MIDI output.
    
    Args:
        note: MIDI note number (0-127)
        velocity: Note velocity (0-127)
        channel: MIDI channel (0-15)
        ctx: MCP context
        
    Returns:
        Response with status
    """
    # Implementation details...
    # 1. Validate MIDI parameters
    # 2. Format the MIDI message
    # 3. Send the message to Pure Data
    # 4. Return status
```

### Creating Complex Patch Structures

```python
@mcp_server.tool()
def create_subpatch(name: str, position: Dict[str, int], ctx: Context) -> Dict[str, Any]:
    """Create a subpatch object.
    
    This tool creates a subpatch (pd object) in the main patch.
    
    Args:
        name: Name of the subpatch
        position: Position on the canvas (x, y coordinates)
        ctx: MCP context
        
    Returns:
        Response with subpatch object ID and status
    """
    # Implementation details...
    # 1. Create a pd object
    # 2. Set up the subpatch environment
    # 3. Track the object
    # 4. Return the object ID
```

## Conclusion

By following these implementation guidelines, you'll ensure that all MCP extensions for Pure Data maintain a consistent design pattern, are well-documented, and integrate seamlessly with the existing codebase. Remember to:

1. Follow the established patterns for tools, resources, and prompts
2. Maintain the object tracking system
3. Use consistent message formats
4. Implement proper error handling
5. Document your extensions thoroughly
6. Test and validate your implementation

For further assistance, refer to the existing implementation in `mcp_server.py` and the comprehensive command list in `commands.md`. 