import json
import jsonschema
import unittest
from jsonschema import validate, ValidationError
from osc_daemon import handle_mcp_request

# Load MCP tool definitions
with open("mcp_tools.json", "r") as schema_file:
    MCP_SCHEMA = json.load(schema_file)

# Define explicit validators for messages going to absolute_final_solution.pd
def validate_create_message(data):
    """Validates a create object message format for Pure Data dynamic patching."""
    required_keys = ['object_type', 'position', 'args']
    
    # Check required keys
    for key in required_keys:
        if key not in data:
            return {"status": "invalid", "error": f"Missing required field: {key}"}
    
    # Validate object type (must be a string)
    if not isinstance(data['object_type'], str):
        return {"status": "invalid", "error": "object_type must be a string"}
    
    # Validate position (must have x and y as integers)
    if not isinstance(data['position'], dict):
        return {"status": "invalid", "error": "position must be a dictionary"}
    
    if 'x' not in data['position'] or 'y' not in data['position']:
        return {"status": "invalid", "error": "position must have x and y coordinates"}
    
    if not (isinstance(data['position']['x'], int) and isinstance(data['position']['y'], int)):
        return {"status": "invalid", "error": "position coordinates must be integers"}
    
    # Validate args (must be a list of strings or numbers)
    if not isinstance(data['args'], list):
        return {"status": "invalid", "error": "args must be a list"}
    
    # All valid!
    return {"status": "valid"}

def validate_connect_message(data):
    """Validates a connect objects message format for Pure Data dynamic patching."""
    # Must have source and destination keys
    if 'source' not in data or 'destination' not in data:
        return {"status": "invalid", "error": "Message must have source and destination"}
    
    # Source and destination must have id and port
    for endpoint in ['source', 'destination']:
        if not isinstance(data[endpoint], dict):
            return {"status": "invalid", "error": f"{endpoint} must be a dictionary"}
        
        if 'id' not in data[endpoint] or 'port' not in data[endpoint]:
            return {"status": "invalid", "error": f"{endpoint} must have id and port"}
        
        # id must be a string, port must be an integer
        if not isinstance(data[endpoint]['id'], str):
            return {"status": "invalid", "error": f"{endpoint} id must be a string"}
        
        if not isinstance(data[endpoint]['port'], int):
            return {"status": "invalid", "error": f"{endpoint} port must be an integer"}
    
    # All valid!
    return {"status": "valid"}

def validate_dsp_message(data):
    """Validates a DSP control message."""
    # DSP state must be a boolean or 0/1
    if 'state' not in data:
        return {"status": "invalid", "error": "Missing required field: state"}
    
    if not isinstance(data['state'], (bool, int)) or (isinstance(data['state'], int) and data['state'] not in [0, 1]):
        return {"status": "invalid", "error": "state must be a boolean or 0/1"}
    
    return {"status": "valid"}

def validate_mcp_request(tool_name, request_data):
    """Validates an MCP request against the defined schema."""
    # First check if this is one of our dynamic patching tools
    if tool_name == "create_object":
        return validate_create_message(request_data)
    elif tool_name == "connect_objects":
        return validate_connect_message(request_data)
    elif tool_name in ["start_dsp", "stop_dsp"]:
        # For start/stop DSP, we don't need any data
        return {"status": "valid"}
    elif tool_name == "set_dsp":
        return validate_dsp_message(request_data)
    
    # If not our custom tools, fall back to schema validation
    for tool in MCP_SCHEMA["mcp_tools"]:
        if tool["name"] == tool_name:
            try:
                validate(instance=request_data, schema={"type": "object", "properties": tool["parameters"], "required": list(tool["parameters"].keys())})
                return {"status": "valid"}
            except ValidationError as e:
                return {"status": "invalid", "error": e.message}
    
    return {"status": "unknown_tool"}

class TestMCPServer(unittest.TestCase):
    
    def test_create_object(self):
        """Test creating an object in Pure Data."""
        request = {
            "object_type": "osc~",
            "args": ["440"],
            "position": {"x": 100, "y": 200}
        }
        self.assertEqual(validate_mcp_request("create_object", request)["status"], "valid")
        response = handle_mcp_request("create_object", request)
        self.assertEqual(response["status"], "success")
    
    def test_delete_object(self):
        """Test deleting an object in Pure Data."""
        request = {"object_id": "osc1"}
        self.assertEqual(validate_mcp_request("delete_object", request)["status"], "valid")
        response = handle_mcp_request("delete_object", request)
        self.assertEqual(response["status"], "success")
    
    def test_connect_objects(self):
        """Test connecting two objects."""
        request = {
            "source": {"id": "osc1", "port": 0},
            "destination": {"id": "dac", "port": 0}
        }
        self.assertEqual(validate_mcp_request("connect_objects", request)["status"], "valid")
        response = handle_mcp_request("connect_objects", request)
        self.assertEqual(response["status"], "success")
    
    def test_set_param(self):
        """Test modifying a parameter."""
        request = {
            "object_id": "filter1",
            "parameter": "freq",
            "value": "500"
        }
        self.assertEqual(validate_mcp_request("set_param", request)["status"], "valid")
        response = handle_mcp_request("set_param", request)
        self.assertEqual(response["status"], "success")
    
    def test_get_param(self):
        """Test retrieving a parameter value."""
        request = {
            "object_id": "filter1",
            "parameter": "freq"
        }
        self.assertEqual(validate_mcp_request("get_param", request)["status"], "valid")
        response = handle_mcp_request("get_param", request)
        self.assertIn("value", response)
    
    def test_start_dsp(self):
        """Test starting DSP processing."""
        response = handle_mcp_request("start_dsp", {})
        self.assertEqual(response["status"], "success")
    
    def test_stop_dsp(self):
        """Test stopping DSP processing."""
        response = handle_mcp_request("stop_dsp", {})
        self.assertEqual(response["status"], "success")
    
    def test_save_patch(self):
        """Test saving a patch."""
        request = {"file_path": "test_patch.pd"}
        self.assertEqual(validate_mcp_request("save_patch", request)["status"], "valid")
        response = handle_mcp_request("save_patch", request)
        self.assertEqual(response["status"], "success")
    
    def test_load_patch(self):
        """Test loading a patch."""
        request = {"file_path": "test_patch.pd"}
        self.assertEqual(validate_mcp_request("load_patch", request)["status"], "valid")
        response = handle_mcp_request("load_patch", request)
        self.assertEqual(response["status"], "success")
    
    # Add new tests for our dynamic patching format
    def test_dynamic_create_validation(self):
        """Test validation of dynamic create object message format."""
        # Valid request
        valid_request = {
            "object_type": "osc~",
            "position": {"x": 100, "y": 100},
            "args": ["440"]
        }
        self.assertEqual(validate_create_message(valid_request)["status"], "valid")
        
        # Invalid: missing position
        invalid_request = {
            "object_type": "osc~",
            "args": ["440"]
        }
        self.assertEqual(validate_create_message(invalid_request)["status"], "invalid")
        
        # Invalid: position missing y coordinate
        invalid_request = {
            "object_type": "osc~",
            "position": {"x": 100},
            "args": ["440"]
        }
        self.assertEqual(validate_create_message(invalid_request)["status"], "invalid")
    
    def test_dynamic_connect_validation(self):
        """Test validation of dynamic connect objects message format."""
        # Valid request
        valid_request = {
            "source": {"id": "osc1", "port": 0},
            "destination": {"id": "dac1", "port": 0}
        }
        self.assertEqual(validate_connect_message(valid_request)["status"], "valid")
        
        # Invalid: missing destination
        invalid_request = {
            "source": {"id": "osc1", "port": 0}
        }
        self.assertEqual(validate_connect_message(invalid_request)["status"], "invalid")
        
        # Invalid: source missing port
        invalid_request = {
            "source": {"id": "osc1"},
            "destination": {"id": "dac1", "port": 0}
        }
        self.assertEqual(validate_connect_message(invalid_request)["status"], "invalid")
        
        # Invalid: port is not an integer
        invalid_request = {
            "source": {"id": "osc1", "port": "output"},
            "destination": {"id": "dac1", "port": 0}
        }
        self.assertEqual(validate_connect_message(invalid_request)["status"], "invalid")
    
if __name__ == "__main__":
    print("Running MCP Server Test Suite...")
    unittest.main()
