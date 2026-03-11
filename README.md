# Blender MCP Skill – Comprehensive Documentation

Just Download This and Put it in your Openclaw_Workspace Folder, and ask your agent to Explore the Skill!

## 📖 Table of Contents

1. [Overview](#overview)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Skill Structure](#skill-structure)
4. [Client Modules](#client-modules)
   - [Base Client](#base-client-blender_mcp_clientpy)
   - [Animation Client](#animation-client-blender_mcp_animationpy)
   - [Rigging Client](#rigging-client-blender_mcp_riggingpy)
   - [Physics Client](#physics-client-blender_mcp_physicspy)
   - [Rendering Client](#rendering-client-blender_mcp_renderingpy)
   - [Assets Client](#assets-client-blender_mcp_assetspy)
   - [AI & Utils Client](#ai--utils-client-blender_mcp_ai_utilspy)
5. [API Reference](#api-reference)
6. [Usage Examples](#usage-examples)
7. [MCP Server Configuration](#mcp-server-configuration)
8. [Troubleshooting](#troubleshooting)
9. [Testing & Verification](#testing--verification)
10. [Future Enhancements](#future-enhancements)

---

## Overview

The **Blender MCP Skill** provides a comprehensive Model Context Protocol (MCP) interface to Blender 3.6+ for 3D modeling, animation, simulation, rendering, and asset management. It extends OpenClaw with powerful 3D automation capabilities through a suite of specialized Python client modules.

### Key Features

- **~190 new methods** across 7 specialized clients
- Covers all major Blender domains: core operations, mesh editing, animation, rigging, physics, rendering, asset I/O, AI integration, utilities
- Modular design – inherit only the capabilities you need
- Robust JSON extraction from MCP responses (handles log contamination)
- Full type hints and docstrings
- Compatible with `blender-mcp` Python package and Blender 3.6+

---

## Prerequisites & Setup

### System Requirements

- **Blender 3.6+** installed and accessible in your system PATH
- **Python 3.10+** with `pip` or `uv` available
- **OpenClaw** environment with `conda` (optional but recommended)

### Install Dependencies

```bash
# Activate OpenClaw environment (if using conda)
conda activate OpenClawENV

# Install blender-mcp package
uvx blender-mcp
# or
pip install blender-mcp
```

### Install Blender Addon

1. In Blender: Edit > Preferences > Add-ons > Install
2. Navigate to `skills/blender-mcp-skill/assets/addon.py`
3. Enable "Blender MCP" addon
4. The addon runs a socket server on `localhost:9876`

### Configure mcporter

Create or update `config/mcporter.json` in the workspace root:

```json
{
  "servers": {
    "blender": {
      "type": "stdio",
      "command": "blender-mcp",
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

If `blender-mcp` is not in your PATH, provide the full path to the executable:

```json
{
  "servers": {
    "blender": {
      "type": "stdio",
      "command": "/full/path/to/blender-mcp",
      "env": {
        "BLENDER_HOST": "localhost",
        "BLENDER_PORT": "9876"
      }
    }
  }
}
```

---

## Skill Structure

```
skills/blender-mcp-skill/
├── README.md                 (this file)
├── BLENDER_MCP.md            (original quick reference)
├── CHANGELOG.md              (version history)
├── assets/
│   └── addon.py              (Blender addon)
└── scripts/
    ├── __init__.py
    ├── blender_mcp_client.py         (Base client - Parts 1&2)
    ├── blender_mcp_animation.py      (Part 3 Animation)
    ├── blender_mcp_rigging.py        (Part 3 Rigging)
    ├── blender_mcp_physics.py        (Part 4 Physics)
    ├── blender_mcp_rendering.py      (Part 5 Rendering)
    ├── blender_mcp_assets.py         (Part 6 Assets & I/O)
    └── blender_mcp_ai_utils.py       (Part 7 AI & Utilities)
```

### Usage Pattern

Choose the client based on the capabilities you need. All clients inherit from the base client, so you get all core methods automatically.

```python
# Add the scripts directory to Python path
import sys
sys.path.insert(0, 'skills/blender-mcp-skill/scripts')

# Import desired client
from blender_mcp_client import BlenderMCPClient          # Core only (Parts 1-2)
from blender_mcp_animation import BlenderMCPAnimationClient  # +Animation
from blender_mcp_rigging import BlenderMCPRiggingClient      # +Rigging
from blender_mcp_physics import BlenderMCPPhysicsClient      # +Physics
from blender_mcp_rendering import BlenderMCPRenderingClient  # +Rendering
from blender_mcp_assets import BlenderMCPAssetsClient        # +Assets I/O
from blender_mcp_ai_utils import BlenderAIClient             # +AI & Utils

# Create client instance
client = BlenderMCPRenderingClient()  # example

# Call methods
client.set_render_engine('CYCLES')
client.create_area_light('MainLight', location=[5,5,5], width=2, height=2, energy=500)
```

---

## Client Modules

### Base Client (`blender_mcp_client.py`)

**Total Methods:** 112 (including `assign_material`)

**Provides:** Core object manipulation, transform operations, mesh topology, modifiers, geometry nodes, material creation, etc.

#### Core Operations (22 methods)

| Method | Description |
|--------|-------------|
| `list_all_objects()` | List all objects with types, visibility, parent |
| `select_object(name, select=True)` | Select/deselect object |
| `select_all()` | Select all objects |
| `select_none()` | Deselect all |
| `get_active_object()` | Get currently active object |
| `set_active_object(name)` | Set active object |
| `hide_object(name, hide=True)` | Hide/show in viewport and render |
| `show_object(name)` | Alias to show |
| `lock_object(name, lock=True)` | Lock transforms |
| `copy_object(name, new_name=None, linked=False)` | Duplicate object |
| `instance_object(name, new_name=None)` | Linked duplicate |
| `join_objects(object_names)` | Join multiple objects |
| `separate_object(name, separation_type='SELECTED')` | Separate geometry |
| `parent_objects(parent, children, keep_transform=True)` | Parent objects |
| `clear_parent(child_name, keep_transform=True)` | Remove parent |
| `get_object_hierarchy(root_name, max_depth=10)` | Get hierarchy tree |
| `apply_transform(name)` | Apply location/rotation/scale |
| `reset_transform(name)` | Reset to identity |
| `snap_to_grid(name, increment=1.0)` | Snap to grid |
| `snap_to_cursor(name)` | Snap to 3D cursor |
| `align_objects_to_axis(object_names, axis='X', reference_object=None)` | Align along axis |
| `distribute_objects(object_names, axis='X', spacing=1.0, start_position=None)` | Distribute evenly |
| `copy_transform(source, dest)` | Copy transform |
| `match_transform(target, source)` | Alias for copy_transform |
| `get_object_center(name, world_space=True)` | Get object center point |
| `get_object_bounding_box(name)` | Get world-space AABB (already existed) |

#### Advanced Mesh & Geometry (28 methods)

| Category | Methods |
|----------|---------|
| **Mesh Topology** | `triangulate_object`, `quads_to_tris`, `tris_to_quads`, `fill_holes`, `merge_vertices`, `split_edges`, `decimate_object`, `remesh_object` |
| **Mesh Editing** | `extrude_along_curve`, `inset_faces`, `bevel_edges`, `loop_cut`, `edge_crease`, `edge_ring_select`, `edge_loop_select`, `bridge_faces` |
| **Modifiers** | `add_modifier`, `list_modifiers`, `remove_modifier`, `apply_modifier`, `reorder_modifier`, `toggle_modifier` |
| **Geometry Nodes** | `create_geometry_nodes_setup`, `list_geometry_nodes_available`, `apply_geometry_nodes`, `get_geometry_node_attributes`, `set_geometry_node_attribute`, `execute_geometry_nodes_network` |

#### Materials (Existing)

Base client also includes material methods from original skill:
- `create_material`, `create_material_preset`, `assign_material` (newly added), etc.

---

### Animation Client (`blender_mcp_animation.py`)

**Total Methods:** 134 (22 new)

**New Methods (22):**

#### Keyframe Animation
- `insert_keyframe(object_name, data_path, frame, value)`
- `insert_location_keyframe(object_name, frame, location=None)`
- `insert_rotation_keyframe(object_name, frame, rotation=None, mode='EULER')`
- `insert_scale_keyframe(object_name, frame, scale=None)`
- `insert_visibility_keyframe(object_name, frame, visible=True)`

#### Keyframe Management
- `get_keyframes(object_name, data_path)` → list of keyframe info
- `delete_keyframe(object_name, data_path, frame)`
- `delete_all_keyframes(object_name, data_path=None)`
- `set_keyframe_interpolation(object_name, data_path, frame, mode)`

#### F-Curves
- `get_fcurve(object_name, data_path, index=0)` → fcurve dict
- `list_fcurves(object_name)` → list of descriptors
- `modify_fcurve_handles(object_name, data_path, frame, handle_type)`
- `add_fcurve_modifier(object_name, data_path, mod_type, **params)`
- `set_fcurve_extrapolation(object_name, data_path, mode)`
- `sample_fcurve(object_name, data_path, frame)` → float value
- `smooth_fcurve(object_name, data_path, factor=0.5)`

#### NLA (Non-Linear Animation)
- `create_nla_strip(object_name, action_name, start_frame, name=None)`
- `list_nla_strips(object_name)` → list of strip info
- `nla_strip_blend_type(strip_name, object_name, blend_type)`
- `nla_strip_extrapolation(strip_name, object_name, mode)`
- `push_down_action(object_name)`

#### Auto Keying
- `set_autokey(enabled=True)`

---

### Rigging Client (`blender_mcp_rigging.py`)

**Total Methods:** 129 (17 new)

**New Methods (17):**

#### Armatures & Bones
- `create_armature(name, display_type='WIRE')`
- `add_armature_bone(armature_name, bone_name, head=None, tail=None)`
- `edit_bone_transform(armature_name, bone_name, head=None, tail=None, roll=None)`
- `parent_bone(child_bone, parent_bone, armature_name, connected=False)`
- `create_bone_constraint(bone_name, armature_name, constraint_type, **params)`

#### Skinning
- `assign_skin_armature(mesh_name, armature_name)` (adds Armature modifier)
- `weight_paint_auto(mesh_name, armature_name)` (auto skinning)
- `list_vertex_groups(object_name)` → list of group info
- `get_vertex_weights(object_name, group_name)` → {vertex_index: weight}
- `assign_vertex_weight(object_name, group_name, vertex_indices, weight)`

#### Shape Keys (Morph Targets)
- `add_shape_key(object_name, name, from_mix=False)`
- `list_shape_keys(object_name)` → list of shape key info
- `set_shape_key_value(object_name, key_name, value)`
- `key_shape_keys(object_name, key_name)` (insert keyframe for shape key)
- `rename_shape_key(object_name, old_name, new_name)`
- `remove_shape_key(object_name, key_name)`
- `transfer_shape_key(src_object, dest_object, key_name)`

---

### Physics Client (`blender_mcp_physics.py`)

**Total Methods:** 143 (31 new)

**Categories:**

#### Rigid Body (6)
- `add_rigid_body(object_name, body_type='ACTIVE', mass=1.0, friction=0.5, bounce=0.0, use_margin=False, margin=0.0)`
- `set_rigid_body_collision_shape(object_name, shape='CONVEX_HULL', use_deform=False, mesh_source='BASE')`
- `add_rigid_body_constraint(constraint_type, object1, object2, pivot_type='CENTER', pivot_x=0, pivot_y=0, pivot_z=0, limit_lin_x=False, limit_lin_y=False, limit_lin_z=False, limit_ang_x=False, limit_ang_y=False, limit_ang_z=False)`
- `apply_rigid_body_force(object_name, force)` – vector
- `bake_rigid_body(object_name, frame_start=1, frame_end=250)`
- `delete_rigid_body_physics(object_name)`

#### Soft Body (5)
- `add_soft_body(object_name, goal=-0.5, mass=1.0, use_self_collision=False)`
- `set_soft_body_spring_length(object_name, length)` – note: maps to `bend` as proxy (Blender API limitation)
- `set_soft_body_damping(object_name, damping)` – viscous damping
- `pin_soft_body_vertex(object_name, vertex_index, pin=True)` – via vertex group
- `bake_soft_body(object_name, frame_start=1, frame_end=250)`

#### Cloth (5)
- `add_cloth(object_name, quality=5, mass=0.3, tension=0.5, compression=0.5, bending=0.5)`
- `set_cloth_presets(object_name, preset='COTTON')` – preset mapping stub
- `pin_cloth_vertices(object_name, vertex_indices)` – via "Pin" vertex group
- `add_cloth_collision(object_name, distance=0.015, friction=0.5)`
- `bake_cloth(object_name, frame_start=1, frame_end=250)`

#### Fluids (2)
- `add_fluid(object_name, fluid_type='DOMAIN')` – DOMAIN, FLOW, EFFECTOR
- `set_fluid_presets(object_name, preset='WATER')` – density/viscosity mapping

#### Particles (5)
- `add_particle_system(object_name, count=1000)`
- `set_particle_type(object_name, ptype='EMITTER')` – EMITTER or HAIR
- `particle_render_as(object_name, render_type='OBJECT')` – OBJECT, GROUP, HALO, BILLBOARD
- `bake_particles(object_name, frame_start=1, frame_end=250)`
- `add_flow_fluid(object_name, flow_type='INFLOW')` – INFLOW, OUTFLOW, GEOMETRY

#### Smoke & Fire (4)
- `add_smoke(object_name, smoke_type='DOMAIN', fire_type='NONE')`
- `set_smoke_resolution(object_name, resolution=32)`
- `set_smoke_type(object_name, smoke_type, fire_type)`
- `bake_smoke(object_name)`

#### Dynamic Paint (4)
- `add_dynamic_paint(object_name, canvas=True, brush=False)`
- `set_paint_surface(object_name, surface_type='PAINT')` – PAINT, DISPLACE, WAVE
- `set_paint_brush(object_name, color=[1,0,0], radius=0.5)`
- `bake_dynamic_paint(object_name, frame_start=1, frame_end=250)`

---

### Rendering Client (`blender_mcp_rendering.py`)

**Total Methods:** 159 (47 new)

#### Render Engine Control (7)
- `set_render_engine(engine='CYCLES')` – CYCLES, EEVEE, WORKBENCH
- `set_render_resolution(x, y, percentage=100)`
- `set_render_samples(samples=256)` – Cycles only
- `set_denoising(enabled=True)` – Cycles only
- `set_render_device(device='GPU')` – CPU/GPU selection
- `get_render_engine_info()` → dict
- `use_contour_render(threshold=0.25)` – Freestyle NPR

#### Render Output (8)
- `render_to_file(filepath)` – Render and save still
- `render_to_bytes()` – Return PNG bytes
- `render_viewport_to_bytes(viewport='VIEW_3D')`
- `set_output_path(path)`
- `set_output_format(format='PNG')` – PNG, JPEG, EXR, TIFF, TARGA, OPEN_EXR_MULTILAYER
- `enable_transparency(background=True)` – Film transparent
- `set_frame_range(start, end, step=1)`
- `set_output_multilayer(multilayer=True)`

#### Lighting (8)
- `create_area_light(name, location, rotation, width, height, color, energy)`
- `create_point_light(name, location, color, energy, radius)`
- `create_spot_light(name, location, rotation, color, energy, spot_size, spot_blend)`
- `create_sun_light(name, location, rotation, color, energy, angle)`
- `create_volume_scatter(name, location, density, color)` – placeholder
- `set_light_shadow(light_name, shadow=True, soft=False)`
- `light_bake_indirect(light_name, samples=128)` – placeholder
- `list_light_probes()` – list reflection/irradiance probes

#### World & Environment (5)
- `set_world_color(r, g, b)` – solid background
- `use_sky_texture(sun_elevation, turbidity)` – Nishita procedural sky
- `use_hdri(filepath, strength)` – load environment map
- `set_world_mist(depth, intensity)` – volumetric mist
- `get_world_settings()` → dict

#### Camera (7)
- `set_camera_lens(camera_name, lens, focal_length)` – PERSP, ORTHO, PANO
- `set_camera_dof(camera_name, focus_distance, fstop)`
- `set_camera_motion_blur(camera_name, shutter)`
- `set_camera_shift(camera_name, shift_x, shift_y)`
- `create_camera_from_view(name)` – creates camera
- `set_camera_to_object(camera_name, target_object)` – adds Track To constraint
- `animate_camera_path(camera_name, locations, frames)` – insert keyframes

#### Compositing (8)
- `enable_compositing(enabled=True)`
- `add_compositor_node(node_type, location)` – any node
- `link_compositor_nodes(from_node, from_socket, to_node, to_socket)`
- `get_compositor_render_layers()` – find/create Render Layers node
- `add_glare(node_name, glare_type, threshold)`
- `add_blur(node_name, size_x, size_y)`
- `set_composite_output(filepath)`
- `render_composited(filepath)`

#### AOVs (4)
- `enable_aov(aov_name)` – enable pass in view layer
- `list_available_aovs()` – list common passes
- `set_aov_path(aov_name, filepath)`
- `bake_aov(aov_name)` – placeholder

---

### Assets Client (`blender_mcp_assets.py`)

**Total Methods:** 144 (32 new)

#### Import (9 formats)
- `import_obj(filepath, name, use_smooth_groups, use_split_objects, use_split_groups, global_scale, axis_forward, axis_up)`
- `import_fbx(filepath, automatic_bone_orientation, global_scale, axis_forward, axis_up, use_image_search)`
- `import_glb_gltf(filepath, filter_glob, import_pack_images, import_shading)`
- `import_stl(filepath, global_scale, use_scene_unit)`
- `import_usd(filepath, import_visible_only, import_all_materials)`
- `import_abc(filepath, use_frame_range, start_frame, end_frame)`
- `import_ply(filepath)`
- `import_3ds(filepath, global_scale, use_image_search)`
- `preview_import(filepath, format)` → info dict (metadata)

#### Export (8 formats)
- `export_obj(filepath, selected_only, apply_modifiers, global_scale, axis_forward, axis_up)`
- `export_fbx(filepath, selected_only, apply_modifiers, global_scale, axis_forward, axis_up, use_mesh_modifiers)`
- `export_glb_gltf(filepath, format, selected_only)` – GLB or GLTF
- `export_stl(filepath, selected_only, ascii, global_scale, use_mesh_modifiers)`
- `export_usd(filepath, selected_only, export_format)` – USD, USDC, USDA
- `export_abc(filepath, start_frame, end_frame, global_scale, selected_only)`
- `export_ply(filepath, selected_only, ascii)`
- `export_three_js(filepath)` – requires addon

#### Asset Library (8)
- `list_asset_libraries()` → list of {name, path}
- `import_from_library(library_name, asset_name, target_collection=None)` – placeholder
- `publish_to_library(object_name, library_name, catalog=None)`
- `create_asset_preview(object_name, filepath)` – placeholder
- `mark_as_asset(object_name, catalog='')`
- `unmark_asset(object_name)`
- `list_assets_in_library(library_name, catalog='')` – placeholder (current file only)
- `search_assets(query, libraries=None)` – searches current file

#### Batch Operations (6)
- `batch_import(filepaths, format, **kwargs)` → list of results
- `batch_export(object_names, filepath_pattern, format, base_dir='.', **kwargs)` → list of results
- `batch_material_assign(object_names, material_name)` → list of results (now fixed)
- `batch_set_parent(children, parent, keep_transform=True)` → list of results
- `batch_delete(object_names)` → list of results
- `batch_duplicate(object_names, count=2, offset=(0,0,0))` → list of results (offset placeholder)

---

### AI & Utils Client (`blender_mcp_ai_utils.py`)

**Total Methods:** 152 (40 new)

#### AI 3D Generation (6 placeholders)
- `generate_model_openai_dalle(prompt, style='realistic')`
- `generate_model_stable_diffusion(prompt, negative_prompt='')`
- `img_to_3d_reconstruction(image_path, detail='high')`
- `generate_hyper3d_model_via_text(prompt)`
- `generate_hyper3d_model_via_images(image_paths)`
- `generate_hunyuan3d_model(prompt)`

#### AI-assisted Operations (8 placeholders)
- `ai_material_suggestion(object_name, description='realistic')`
- `ai_uv_unwrap(object_name, method='AI')`
- `ai_retopology(object_name, target_tris=None)`
- `ai_rig_autorig(object_name, rig_type='HUMAN')`
- `ai_animation_transfer(source_action, target_object)`
- `ai_scene_setup(description)`
- `ai_model_repair(object_name, issues=None)`
- `ai_texture_enhance(material_name, description='4k detailed')`

#### AI-powered Tools (7 placeholders)
- `ai_scene_description()` → text
- `ai_camera_suggestions()` → list of pose dicts
- `ai_lighting_setup(mode='studio')`
- `ai_render_settings(scene_name=None)`
- `ai_noise_reduction(image_path, strength=0.5)`
- `ai_upscale_render(image_path, scale=2.0)`
- `ai_inpaint_render(image_path, mask_path, prompt)`

#### Automation & Scripting (8)
- `record_actions_to_script(filepath)` – placeholder
- `playback_script(filepath, dry_run=False)` – executes script
- `create_parameterized_script(object_name, params)` → script string
- `batch_process_script(object_names, script_content)` → list of results
- `validate_script(script_content)` → {'valid': bool, 'errors': []}
- `explain_script(script_content)` → explanation text (placeholder)
- `optimize_script(script_content)` → optimized script (placeholder)
- `convert_script_to_mcp(script_content)` → MCP-style calls (placeholder)

#### Utilities (11)
- `get_system_info()` → dict with Blender version, platform, Python, GPU
- `get_performance_stats()` → dict with object counts, memory estimate
- `validate_scene()` → dict of issues (unused materials, orphaned data, missing textures)
- `find_orphaned_data()` → dict by data type
- `purge_unused_data()` → str message with count deleted
- `pack_resources_into_blend()` → str
- `list_objects_by_type(type='MESH')` → list of object info dicts
- `find_objects_by_name(pattern, regex=False)` → list of names
- `get_scene_bbox()` → {'min': [x,y,z], 'max': [x,y,z]}
- `calculate_scene_stats()` → dict with poly counts, material count, etc.

---

## API Reference

All clients share common patterns:

### Method Signatures

Most methods follow:

```python
def method_name(self, required_arg: type, optional_arg: type = default, user_prompt: str = "Description") -> ReturnType:
```

- `user_prompt` is optional but recommended for MCP telemetry.
- Methods returning structured data emit JSON from Blender and parse it with `_parse_json_output`.
- Errors are returned as strings; exceptions are caught and converted to messages.

### Returning Data

- **List/Dict returns:** Methods like `list_all_objects()`, `get_system_info()` return Python lists/dicts.
- **String returns:** Most operations return a human-readable message.
- **Binary returns:** `render_to_bytes()` returns raw PNG bytes with `expect_binary=True`.

### Error Handling

If Blender encounters an error, the Python code printed is captured and returned as a string. The client does not raise exceptions for most operations; check the returned message for "Error" or "not found".

---

## Usage Examples

### Quick Start: Core Operations

```python
from blender_mcp_client import BlenderMCPClient

client = BlenderMCPClient()

# List all objects
objects = client.list_all_objects()
for obj in objects:
    print(obj['name'], obj['type'])

# Select and transform
client.select_object('Cube')
client.apply_transform('Cube')
client.set_active_object('Light')
center = client.get_object_center('Light')
print(f"Light center: {center}")
```

### Animation Workflow

```python
from blender_mcp_animation import BlenderMCPAnimationClient

anim = BlenderMCPAnimationClient()

# Insert keyframes
anim.insert_location_keyframe('Cube', frame=1, location=[0,0,0])
anim.insert_location_keyframe('Cube', frame=50, location=[5,5,0])
anim.insert_rotation_keyframe('Cube', frame=50, rotation=[0,0,1.57])

# Work with F-curves
fcurves = anim.list_fcurves('Cube')
print(fcurves)

# Set interpolation
anim.set_keyframe_interpolation('Cube', 'location', frame=50, mode='LINEAR')
```

### Physics Simulation

```python
from blender_mcp_physics import BlenderMCPPhysicsClient

phys = BlenderMCPPhysicsClient()

# Add rigid body
phys.add_rigid_body('Cube', body_type='ACTIVE', mass=2.0, bounce=0.8)

# Add ground plane as passive
phys.add_rigid_body('Plane', body_type='PASSIVE')

# Add cloth to a plane
phys.add_cloth('ClothPlane', quality=5, mass=0.3)

# Bake simulation
phys.bake_cloth('ClothPlane', frame_start=1, frame_end=250)
```

### Rendering Setup

```python
from blender_mcp_rendering import BlenderMCPRenderingClient

render = BlenderMCPRenderingClient()

# Set up render
render.set_render_engine('CYCLES')
render.set_render_resolution(1920, 1080)
render.set_render_samples(512)

# Create lights
render.create_point_light('Key', location=[5,5,5], color=[1,1,1], energy=500)
render.create_area_light('Fill', location=[-5,5,3], width=3, height=3, energy=200)

# Set world
render.use_sky_texture(sun_elevation=45, turbidity=2)

# Render
render.render_to_file('/tmp/render.png')
```

### Asset Management

```python
from blender_mcp_assets import BlenderMCPAssetsClient

assets = BlenderMCPAssetsClient()

# Import multiple files
files = ['model1.obj', 'model2.obj']
assets.batch_import(files, format='OBJ')

# Export selected objects
objects = ['Cube', 'Sphere']
assets.batch_export(objects, '/exports/{name}.fbx', format='FBX')

# Mark as asset
assets.mark_as_asset('Cube', catalog='Props')
```

### Utilities

```python
from blender_mcp_ai_utils import BlenderAIClient

utils = BlenderAIClient()

# Get system info
info = utils.get_system_info()
print(f"Blender: {info['blender_version']}, GPU: {info['has_gpu']}")

# Scene statistics
stats = utils.calculate_scene_stats()
print(f"Total faces: {stats['total_faces']}")

# Find and purge unused data
orphans = utils.find_orphaned_data()
utils.purge_unused_data()
```

### Combining Clients

Since clients inherit from `BlenderMCPClient`, you can combine them by multiple inheritance:

```python
from blender_mcp_client import BlenderMCPClient
from blender_mcp_animation import BlenderMCPAnimationClient
from blender_mcp_physics import BlenderMCPPhysicsClient

class MyClient(BlenderMCPAnimationClient, BlenderMCPPhysicsClient):
    pass

client = MyClient()
client.insert_location_keyframe('Cube', 1, [0,0,0])  # from Animation
client.add_rigid_body('Cube')  # from Physics
```

---

## MCP Server Configuration

Ensure `config/mcporter.json` points to the correct `blender-mcp` executable. When running from the workspace root, mcporter auto-discovers this config.

Start Blender and enable the addon. The server will listen on `localhost:9876`. Test connection:

```bash
mcporter call blender.get_scene_info user_prompt="test"
```

---

## Troubleshooting

### "Object not found" errors
- Ensure object name is spelled correctly and exists in the scene.
- Some methods require the object to be of a specific type (e.g., mesh for soft body).

### "No rigid body" or "No modifier"
- The operation requires a modifier or physics component to already exist. Use the appropriate `add_*` method first.

### Import/Export errors
- Verify file paths exist and are accessible.
- For imports, ensure the file format is supported by your Blender build.
- Some importers (like Three.js) require additional addons.

### JSON parsing issues
- The client's `_parse_json_output` handles log contamination. If you see raw Python dicts, check that the method's code uses `print(json.dumps(...))` for structured returns.

### MCP connection refused
- Confirm Blender addon is enabled and listening on port 9876.
- Check that `config/mcporter.json` is in the current working directory when calling `mcporter`.

---

## Testing & Verification

All modules have been compiled and tested against a live Blender MCP server. Basic functionality confirmed for:

- Core: `list_all_objects`, `select_object`, `get_active_object`, `assign_material`
- Animation: `set_autokey`, `insert_location_keyframe`, `list_fcurves`
- Rigging: `create_armature`, `add_shape_key`
- Physics: `add_rigid_body`, `add_soft_body`, `add_cloth`
- Rendering: `set_render_engine`, `create_area_light`, `set_world_color`, `set_camera_lens`
- Assets: `list_asset_libraries`, `preview_import`, `batch_import`
- AI/Utils: `get_system_info`, `calculate_scene_stats`, `find_orphaned_data`, `validate_scene`

Run your own tests:

```python
import sys
sys.path.insert(0, 'skills/blender-mcp-skill/scripts')
from blender_mcp_rendering import BlenderMCPRenderingClient
client = BlenderMCPRenderingClient()
print(client.set_render_engine('CYCLES'))
```

---

## Future Enhancements

- **Material System:** Expand beyond simple Principled BSDF creation; add `create_material`, `create_material_preset` with full node control.
- **AI Integration:** Implement actual API backends for DALL-E, Stable Diffusion, Hyper3D, etc.
- **Geometry Nodes:** Full node tree manipulation API.
- **Asset Libraries:** Complete implementation of library browsing and catalog queries.
- **Batch Duplicate Offset:** Implement spatial offset for `batch_duplicate`.
- **Performance:** Add caching, async operations for long-running simulations.
- **Documentation:** Generate full API reference with Sphinx; include example gallery.

---

## License

MIT (as per original skill). Enhancements by OpenClaw agent.

---

**Happy Blending!** 🎨
