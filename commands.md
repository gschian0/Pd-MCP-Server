# MCP Commands for Pure Data Integration

This document outlines a comprehensive set of MCP tools, resources, and prompts that would enable a complete integration between Claude AI and Pure Data.

## MCP Tools

### Core Object Manipulation

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_object` | Create a new Pd object | `object_type`, `args`, `position` |
| `delete_object` | Delete a Pd object | `object_id` |
| `move_object` | Move an object to a new position | `object_id`, `new_position` |
| `clone_object` | Duplicate an existing object | `object_id`, `new_position` |
| `resize_object` | Change the size of an object | `object_id`, `width`, `height` |

### Connection Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `connect_objects` | Create a connection between objects | `source`, `destination` |
| `disconnect_objects` | Remove a connection | `source_id`, `destination_id` |
| `disconnect_all` | Remove all connections from an object | `object_id` |
| `get_connections` | List all connections for an object | `object_id` |
| `reconnect_object` | Reconnect an object after moving | `object_id`, `connection_map` |

### Parameter Control

| Tool | Description | Parameters |
|------|-------------|------------|
| `set_param` | Modify an object's parameter | `object_id`, `parameter`, `value` |
| `get_param` | Get the current value of a parameter | `object_id`, `parameter` |
| `animate_param` | Smoothly change a parameter over time | `object_id`, `parameter`, `start_value`, `end_value`, `duration` |
| `automate_param` | Set up parameter automation | `object_id`, `parameter`, `automation_data` |
| `bind_params` | Bind parameters between objects | `source_object_id`, `source_param`, `target_object_id`, `target_param` |

### DSP Control

| Tool | Description | Parameters |
|------|-------------|------------|
| `start_dsp` | Enable DSP processing | None |
| `stop_dsp` | Disable DSP processing | None |
| `get_dsp_status` | Check if DSP is running | None |
| `set_block_size` | Set the DSP block size | `block_size` |
| `set_sample_rate` | Set the sample rate | `sample_rate` |
| `calculate_cpu_load` | Get current CPU usage | None |

### Patch Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `save_patch` | Save the current patch | `file_path` |
| `load_patch` | Load a patch from a file | `file_path` |
| `merge_patch` | Merge another patch into the current one | `file_path`, `position` |
| `create_subpatch` | Create a new subpatch | `name`, `position` |
| `export_subpatch` | Export a subpatch as an abstraction | `subpatch_id`, `file_path` |
| `clear_patch` | Clear the entire patch | None |
| `get_patch_state` | Get the entire patch state | None |
| `undo` | Undo the last action | None |
| `redo` | Redo the last undone action | None |

### GUI Objects

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_slider` | Create a slider | `position`, `min`, `max`, `default`, `orientation` |
| `create_toggle` | Create a toggle switch | `position`, `default` |
| `create_number_box` | Create a number box | `position`, `min`, `max`, `default` |
| `create_bang` | Create a bang button | `position` |
| `create_message` | Create a message box | `position`, `message` |
| `create_canvas` | Create a canvas | `position`, `width`, `height`, `color` |
| `create_graph` | Create a graph | `position`, `width`, `height`, `dimensions` |
| `create_comment` | Add a comment | `position`, `text`, `font_size` |

### Audio File Handling

| Tool | Description | Parameters |
|------|-------------|------------|
| `load_sample` | Load an audio sample | `file_path`, `position` |
| `play_sample` | Play a loaded sample | `object_id` |
| `stop_sample` | Stop a playing sample | `object_id` |
| `record_audio` | Start recording audio | `duration`, `file_path` |
| `stop_recording` | Stop an ongoing recording | None |
| `analyze_audio` | Analyze an audio file | `file_path`, `analysis_type` |

### Data Structures

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_array` | Create a data array | `name`, `size`, `position` |
| `set_array_data` | Set values in an array | `array_id`, `data` |
| `get_array_data` | Get values from an array | `array_id`, `start`, `end` |
| `create_table` | Create a table | `name`, `size`, `position` |
| `load_array_from_file` | Load array data from a file | `array_id`, `file_path` |
| `save_array_to_file` | Save array data to a file | `array_id`, `file_path` |

### MIDI Integration

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_midi_devices` | List available MIDI devices | None |
| `open_midi_input` | Open a MIDI input device | `device_id` |
| `open_midi_output` | Open a MIDI output device | `device_id` |
| `send_midi_note` | Send a MIDI note | `note`, `velocity`, `channel` |
| `send_midi_cc` | Send a MIDI control change | `cc_number`, `value`, `channel` |
| `create_midi_mapping` | Map a MIDI controller to a parameter | `cc_number`, `channel`, `object_id`, `parameter` |

### Workspace Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `refresh_gui` | Force Pure Data to refresh its GUI | None |
| `set_canvas_size` | Set the canvas size | `width`, `height` |
| `set_canvas_position` | Set the canvas position | `x`, `y` |
| `zoom_canvas` | Zoom the canvas view | `zoom_level` |
| `center_on_object` | Center the view on an object | `object_id` |
| `arrange_objects` | Auto-arrange objects | `layout_type` |
| `get_object_at_position` | Find an object at a position | `x`, `y` |

### Library and External Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_available_objects` | List all available Pd objects | None |
| `list_loaded_externals` | List loaded external libraries | None |
| `load_external` | Load an external library | `library_name` |
| `get_object_help` | Get help for an object | `object_type` |
| `get_object_documentation` | Get documentation for an object | `object_type` |
| `search_objects` | Search for objects matching a pattern | `query` |

### Network and OSC

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_osc_receiver` | Create an OSC receiver | `port`, `position` |
| `create_osc_sender` | Create an OSC sender | `host`, `port`, `position` |
| `send_osc_message` | Send an OSC message | `host`, `port`, `address`, `args` |
| `set_osc_callback` | Set up a callback for OSC messages | `address`, `callback` |
| `set_network_timeout` | Set network timeout | `timeout_ms` |

### Analysis Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `analyze_patch` | Analyze the current patch structure | None |
| `find_feedback_loops` | Find feedback loops in the patch | None |
| `trace_signal_flow` | Trace signal flow from an object | `object_id` |
| `find_unused_objects` | Find objects with no connections | None |
| `validate_patch` | Validate the patch against common issues | None |
| `get_memory_usage` | Get memory usage statistics | None |

## MCP Resources

| Resource | Description | Example Usage |
|----------|-------------|--------------|
| `pd://objects` | List of available Pd objects with descriptions | `@pd://objects` |
| `pd://port-info` | Current OSC port configuration | `@pd://port-info` |
| `pd://patch-state` | Current state of the patch | `@pd://patch-state` |
| `pd://object-help/{object_type}` | Help page for a specific object | `@pd://object-help/osc~` |
| `pd://object-categories` | Categories of Pd objects | `@pd://object-categories` |
| `pd://audio-objects` | List of audio processing objects | `@pd://audio-objects` |
| `pd://control-objects` | List of control objects | `@pd://control-objects` |
| `pd://gui-objects` | List of GUI objects | `@pd://gui-objects` |
| `pd://io-objects` | List of input/output objects | `@pd://io-objects` |
| `pd://patch-validation` | Validation results for the current patch | `@pd://patch-validation` |
| `pd://dsp-status` | Current DSP status | `@pd://dsp-status` |
| `pd://audio-settings` | Current audio settings | `@pd://audio-settings` |
| `pd://midi-devices` | Available MIDI devices | `@pd://midi-devices` |
| `pd://templates` | Available patch templates | `@pd://templates` |
| `pd://schema` | JSON schema for Pd patches | `@pd://schema` |
| `pd://version` | Version information | `@pd://version` |

## MCP Prompts

| Prompt | Description | Parameters |
|--------|-------------|------------|
| `create_oscillator_patch` | Create a simple oscillator patch | None |
| `create_synth_voice` | Create a complete synthesizer voice | `voice_type` |
| `create_drum_machine` | Create a drum machine patch | `num_pads` |
| `create_audio_effect` | Create an audio effect chain | `effect_types` |
| `create_sampler` | Create a sample playback patch | `num_samples` |
| `create_sequencer` | Create a sequencer patch | `num_steps`, `num_tracks` |
| `create_mixer` | Create a mixer patch | `num_channels` |
| `create_generative_patch` | Create a generative music patch | `complexity` |
| `create_granular_processor` | Create a granular processing patch | None |
| `create_audio_visualizer` | Create an audio visualization patch | `viz_type` |
| `optimize_patch` | Optimize the current patch for CPU usage | None |
| `document_patch` | Generate documentation for the current patch | None |
| `convert_midi_to_audio` | Create a patch for MIDI to audio conversion | None |
| `create_spatial_audio` | Create a spatial audio processing patch | `channels` |
| `create_spectral_processor` | Create a spectral processing patch | None |
| `create_machine_learning_patch` | Create a patch using ML for audio processing | `ml_type` |
| `create_network_collaboration` | Create a collaborative network patch | `participants` |

## Integration Patterns

### Synthesis Design Pattern

1. Create oscillator sources
2. Add modulation (ADSR, LFO, etc.)
3. Apply effects (filtering, distortion, etc.)
4. Mix and route to output
5. Add control interfaces (sliders, MIDI)

### Audio Processing Design Pattern

1. Create audio input (file or live)
2. Apply processing chain
3. Create parameter controls
4. Create visualization of the signal
5. Route to output

### Sequencing and Composition Design Pattern

1. Create timing source (clock, metro)
2. Add sequencing logic
3. Connect to sound generators
4. Add randomization or algorithmic components
5. Add user controls for parameters

### Machine Learning Design Pattern

1. Load or create a model
2. Connect audio input for analysis
3. Process the audio through the model
4. Map model outputs to synthesis parameters
5. Create feedback loop for continuous learning 