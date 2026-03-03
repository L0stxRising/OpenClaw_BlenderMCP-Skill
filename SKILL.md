# Blender MCP Skill (Enhanced)

OpenClaw skill for controlling Blender via the BlenderMCP Model Context Protocol server.

## Overview

This skill provides a comprehensive Python client (`blender_mcp_client.py`) for remotely controlling Blender. It supports:

- Primitive creation and object manipulation
- Material creation and assignment
- Scene inspection and screenshots
- Code execution in Blender
- Asset imports from Poly Haven, Sketchfab
- AI 3D generation: Hyper3D (Rodin) and Hunyuan3D
- **Enhanced utilities** (batch ops, scene management, presets, exports, etc.)

See `scripts/blender_mcp_client.py` for the full API reference.

## Prerequisites

- Blender 3.6+ with BlenderMCP addon installed and socket server active (default port 9876)
- `uvx blender-mcp` or `blender-mcp` MCP server running
- `mcporter` CLI configured with a `blender` server
- Workspace Python environment (OpenClawENV recommended)

## Setup

1. Install BlenderMCP server:
   ```bash
   uvx blender-mcp
   ```
   Or: `pip install blender-mcp`

2. Install the Blender addon:
   - Open Blender → Edit → Preferences → Add-ons → Install
   - Select `skills/blender-mcp-skill/assets/addon.py` (if shipped) or download from PyPI
   - Enable the addon and click "Connect to Claude" in the 3D View sidebar

3. Configure mcporter:
   ```json
   {
     "servers": {
       "blender": {
         "type": "stdio",
         "command": "uvx",
         "args": ["blender-mcp"],
         "env": {
           "BLENDER_HOST": "localhost",
           "BLENDER_PORT": "9876"
         }
       }
     }
   }
   ```

4. Test connection:
   ```bash
   mcporter call blender.get_scene_info
   ```

## Usage

Import in your Python scripts:

```python
from blender_mcp_client import BlenderMCPClient

client = BlenderMCPClient()
client.is_connected()  # → True/False

# Create objects
client.create_primitive('CUBE', name='Box', location=[0,0,1], scale=[2,2,2])

# Materials
client.create_material_preset('metal', name='Steel')
client.assign_material('Box', 'Steel')

# Screenshot
img_bytes = client.get_viewport_screenshot(max_size=1024)
```

See the comprehensive docstrings in `scripts/blender_mcp_client.py` for all methods.

## Enhanced Features

The client includes many utility methods beyond the core MCP tools:

- Batch creation/deletion/assignment
- Scene save/load/clear
- Material presets (metal, wood, glass, etc.)
- Mesh editing: subdivide, bevel, extrude
- Lighting presets (studio 3-point, outdoor, indoor, night)
- Camera presets (wide, standard, telephoto, portrait)
- Collection management
- Export to glTF, FBX, OBJ
- Auto-polling helpers for async AI generation jobs

## Documentation

Full API documentation is available in the module docstring and method docstrings:
```bash
pydoc blender_mcp_client.BlenderMCPClient
```

For the official BlenderMCP server docs: https://pypi.org/project/blender-mcp/

## Troubleshooting

- Connection errors: Ensure Blender addon is connected (green status), MCP server running, and port 9876 accessible.
- Tool timeouts: Break complex operations into smaller steps; avoid massive scene queries in one call.
- Poly Haven: Enable it in the Blender addon sidebar.
- `execute_blender_code` is powerful but dangerous; only run trusted code.

## License

MIT. The BlenderMCP server and addon are © Siddharth Ahuja.
