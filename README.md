# Blender MCP Skill for OpenClaw

This skill integrates Blender with OpenClaw through the Model Context Protocol (MCP), allowing you to control Blender remotely to create, edit, and manipulate 3D models.

## Prerequisites

- **Blender 3.6+** installed (typically at `/opt/blender-3.6.23`)
- **Python 3.10+** with pip/uv available
- **mcporter** CLI installed (comes with OpenClaw)
- OpenClaw environment (`OpenClawENV` conda env recommended)

## Installation

### 1. Install Blender MCP Python Package

On the OpenClaw host machine (where you'll run the MCP server):

```bash
# Using uv (recommended)
uvx blender-mcp

# Or using pip
pip install blender-mcp
```

This installs the MCP server that mediates between OpenClaw and Blender.

### 2. Install Blender Addon

1. Open Blender
2. Go to **Edit > Preferences > Add-ons**
3. Click **Install...**
4. Navigate to this skill's `assets/` directory and select `addon.py`
5. Enable the addon by checking the box
6. Open the 3D View sidebar (press `N` if hidden)
7. Find the **BlenderMCP** tab
8. (Optional) Check "Enable Poly Haven" for asset downloads
9. Click **Connect to Claude** to start the Blender socket server (listens on localhost:9876 by default)

**Note**: Keep Blender running with the addon connected while using this skill.

### 3. Start the MCP Server

In a terminal (keep this running):

```bash
# Using uvx
uvx blender-mcp

# Or if installed via pip
blender-mcp
```

The MCP server will connect to Blender via the socket and wait for MCP clients.

### 4. Configure mcporter

You need to tell mcporter about the Blender MCP server. Create or edit your mcporter config:

```json
{
  "servers": {
    "blender": {
      "type": "stdio",
      "command": "blender-mcp",  // or "uvx blender-mcp"
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

If you installed blender-mcp via uvx, the command is just `blender-mcp` when installed as a package:
```bash
uv tool install blender-mcp  # installs as a tool
```
Or use `uvx blender-mcp` directly as the command.

**Quick test**: Verify mcporter can call Blender MCP:
```bash
mcporter call blender.get_scene_info
```

## Usage in OpenClaw

### Python Module

Import the client in your OpenClaw Python scripts:

```python
from blender_mcp_client import BlenderMCPClient

# Connect to Blender
client = BlenderMCPClient()

# Check connection
if client.is_connected():
    print("Blender is connected!")

# Get scene info
scene = client.get_scene_info()
print(f"Scene: {scene['name']}, Objects: {scene['object_count']}")

# Create a cube
client.create_primitive("CUBE", name="MyCube", location=(0, 0, 0), scale=(2, 2, 2))

# Move an object
client.set_object_transform("MyCube", location=(5, 3, 0))

# Get a screenshot
screenshot = client.get_viewport_screenshot()
with open("/tmp/blender_view.png", "wb") as f:
    f.write(screenshot)

# Execute arbitrary Python code
client.execute_blender_code("""
import bpy
bpy.ops.mesh.primitive_monkey_add()
print("Suzanne added!")
""")
```

### From the OpenClaw CLI

Use the client script directly:

```bash
python3 scripts/blender_mcp_client.py get_scene_info
python3 scripts/blender_mcp_client.py create_primitive --params '{"primitive_type":"SPHERE","scale":[1,1,1]}'
```

## Available Tools

### Scene & Object Info
- `get_scene_info()` - Get full scene information
- `get_object_info(name)` - Get detailed object data
- `list_objects()` - Simple list of object names

### Object Creation & Manipulation
- `create_primitive(type, name, location, rotation, scale)` - Create CUBE, SPHERE, CYLINDER, PLANE, CONE, ICO_SPHERE, TORUS, MONKEY
- `delete_object(name)` - Remove an object
- `set_object_transform(name, location, rotation, scale)` - Modify position/rotation/scale
- `execute_blender_code(code)` - Run any Blender Python

### Materials
- `create_material(name, color, roughness, metallic)` - Create Principled BSDF material
- `assign_material(object_name, material_name)` - Apply material to object

### Screenshots
- `get_viewport_screenshot(max_size=800)` - Capture viewport as PNG bytes

### Poly Haven (if enabled in Blender addon)
- `get_polyhaven_status()`
- `get_polyhaven_categories(asset_type)`
- `search_polyhaven_assets(asset_type, categories)`
- `download_polyhaven_asset(asset_id, asset_type, resolution, file_format)`
- `set_texture(object_name, texture_id)`

### Sketchfab (if API configured)
- `get_sketchfab_status()`
- `search_sketchfab_models(query, categories, count, downloadable)`
- `get_sketchfab_model_preview(uid)` - Returns image bytes
- `download_sketchfab_model(uid, target_size)`

### Hyper3D (Rodin) - AI 3D Generation
- `get_hyper3d_status()`
- `generate_hyper3d_model_via_text(text_prompt, bbox_condition)`
- `generate_hyper3d_model_via_images(input_image_paths, input_image_urls, bbox_condition)`
- `poll_rodin_job_status(subscription_key, request_id)`
- `import_generated_asset(name, task_uuid, request_id)`

### Hunyuan3D - AI 3D Generation (Tencent)
- `get_hunyuan3d_status()`
- `generate_hunyuan3d_model(text_prompt, input_image_url)`
- `poll_hunyuan_job_status(job_id)`
- `import_generated_asset_hunyuan(name, zip_file_url)`

## Example Workflows

### Create a Simple Scene
```python
client = BlenderMCPClient()

# Clear existing objects (optional)
for obj in client.list_objects():
    client.delete_object(obj)

# Add ground plane
client.create_primitive("PLANE", name="Ground", scale=(10, 10, 1))

# Add a red sphere
client.create_primitive("SPHERE", name="Ball", location=(0, 0, 1))
mat = client.create_material("Red", color=[1, 0, 0, 1])
client.assign_material("Ball", "Red")

# Take a screenshot
img = client.get_viewport_screenshot(max_size=1024)
```

### Import an Asset from Poly Haven
```python
client = BlenderMCPClient()
# First search for a rock texture
results = client.search_polyhaven_assets(asset_type="textures", categories="rocks")
# Then download and apply to an object
client.download_polyhaven_asset("rock_wall_01", asset_type="textures", resolution="2k")
client.set_texture("MyCube", "rock_wall_01")
```

### Generate a Model with Hyper3D
```python
client = BlenderMCPClient()
# Generate from text
result = client.generate_hyper3d_model_via_text("A small ceramic mug with handle")
import json
job = json.loads(result)

# Poll until done (you'd typically loop with sleep)
status = client.poll_rodin_job_status(subscription_key=job['subscription_key'])
# If done:
client.import_generated_asset("MyMug", task_uuid=job['task_uuid'])
```

## Troubleshooting

**Connection errors**
- Ensure Blender is running and the addon is enabled
- The "Connect to Claude" button must be clicked to start the socket server
- Verify port 9876 is not blocked by firewall
- Check that the MCP server (`blender-mcp` process) is running

**Timeout errors**
- Simplify requests: break complex operations into smaller steps
- Use `execute_blender_code` sparingly; prefer built-in tools

**Poly Haven not working**
- In Blender, verify the Poly Haven checkbox is enabled in the BlenderMCP sidebar
- Restart Blender and the MCP server

**No objects appearing**
- Check the Scene Collection in Blender; objects may be hidden
- Use `get_scene_info()` to verify objects were created

## Compatibility

- Blender 3.6+ (addon requires Blender 3.0+)
- Tested on Linux, macOS, Windows
- MCP server must be same architecture as Blender (both 64-bit)

## Security Notes

- The `execute_blender_code` tool runs arbitrary Python in Blender. Only use with trusted code.
- Keep Blender scripts from untrusted sources to a minimum.
- Save your work before executing code.

## Resources

- **BlenderMCP PyPI**: https://pypi.org/project/blender-mcp/
- **MCP Docs**: https://modelcontextprotocol.io
- **Demo Video**: https://www.youtube.com/watch?v=lCyQ717DuzQ
- **Discord**: https://discord.gg/z5apgR8TFU

## License

This skill wrapper is provided under MIT License. The BlenderMCP addon and server are © Siddharth Ahuja and licensed under their original terms.
