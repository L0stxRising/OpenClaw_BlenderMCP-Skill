"""
Blender MCP AI Integration & Utilities Client

Extends BlenderMCPClient with:
- AI-powered 3D generation (DALL-E, Stable Diffusion, Midjourney, Hyper3D, Hunyuan3D)
- AI-assisted operations (material suggestion, UV, retopology, rigging, etc.)
- Automation & scripting utilities
- Additional utilities (system info, performance stats, scene validation, etc.)
"""

from blender_mcp_client import BlenderMCPClient
import json
import os
import subprocess
from typing import Any, Dict, List, Optional, Union


class BlenderAIClient(BlenderMCPClient):
    """
    AI and utility-focused client extending BlenderMCPClient.

    WARNING: AI features require external API keys/credentials. These are placeholders.
    """

    # --- AI 3D Generation (Placeholder implementations) ---

    def generate_model_openai_dalle(self, prompt: str, style: str = 'realistic',
                                   user_prompt: str = "Generate 3D via DALL-E") -> str:
        """
        Generate a 3D model from text using DALL-E 3 (via image-to-3D).

        Args:
            prompt: Text description
            style: 'realistic', 'stylized', 'low-poly', etc.
            user_prompt: For telemetry

        Returns:
            Result message with generated object name or path
        """
        code = f"""
import bpy
# Placeholder: would call OpenAI API to generate image, then convert to mesh
# This requires internet and API key; not implemented here
print("DALL-E 3 generation requested: {prompt} (style: {style})")
print("Note: This feature requires external API integration.")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def generate_model_stable_diffusion(self, prompt: str, negative_prompt: str = '',
                                       user_prompt: str = "Generate 3D via Stable Diffusion") -> str:
        """
        Generate a 3D model from text using Stable Diffusion (via image-to-3D).

        Args:
            prompt: Text prompt
            negative_prompt: Negative prompt
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print("Stable Diffusion generation requested: {prompt}")
print("Negative: {negative_prompt}")
print("Note: Requires local SD service or API.")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def img_to_3d_reconstruction(self, image_path: str, detail: str = 'high',
                                 user_prompt: str = "Image to 3D") -> str:
        """
        Convert an image to a 3D mesh using reconstruction algorithms.

        Args:
            image_path: Path to input image
            detail: 'low', 'medium', 'high'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"Image-to-3D requested for {image_path} (detail: {detail})")
# Could use OpenMVG/OpenMVS or external service
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def generate_hyper3d_model_via_text(self, prompt: str, user_prompt: str = "Generate Hyper3D via text") -> str:
        """
        Generate using Hyper3D (Rodin) AI via text.

        Args:
            prompt: Text description
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print("Hyper3D (Rodin) text generation: {prompt}")
print("Note: Requires Hyper3D API key.")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def generate_hyper3d_model_via_images(self, image_paths: List[str], user_prompt: str = "Generate Hyper3D via images") -> str:
        """
        Generate using Hyper3D via reference images.

        Args:
            image_paths: List of image file paths
            user_prompt: For telemetry

        Returns:
            Result message
        """
        paths_str = json.dumps(image_paths)
        code = f"""
import bpy
print(f"Hyper3D image generation with {len({paths_str})} images")
print("Note: Requires Hyper3D API access.")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def generate_hunyuan3d_model(self, prompt: str, user_prompt: str = "Generate Hunyuan3D") -> str:
        """
        Generate 3D model using Tencent Hunyuan.

        Args:
            prompt: Text description
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print("Hunyuan3D generation: {prompt}")
print("Note: Requires Hunyuan API.")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- AI-assisted Operations (Placeholders) ---

    def ai_material_suggestion(self, object_name: str, description: str = "realistic",
                              user_prompt: str = "AI material suggestion") -> str:
        """
        Let AI suggest and create a material for the object.

        Args:
            object_name: Object to apply material to
            description: Material style description
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    # Use AI to decide material parameters based on description
    print(f"AI material suggestion for {object_name}: {description}")
    # Placeholder: could call external service or use ML model
else:
    print("Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_uv_unwrap(self, object_name: str, method: str = 'AI', user_prompt: str = "AI UV unwrap") -> str:
        """
        AI-optimized UV unwrapping.

        Args:
            object_name: Mesh object
            method: Unwrap method hint (AI will decide)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI UV unwrap for {object_name} using {method}")
# Could integrate with smart UV project or external AI tool
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_retopology(self, object_name: str, target_tris: Optional[int] = None,
                     user_prompt: str = "AI retopology") -> str:
        """
        AI-based mesh retopology.

        Args:
            object_name: High-poly mesh
            target_tris: Optional target polygon count
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI retopology for {object_name}" + (f" to ~{target_tris} tris" if {target_tris} else ""))
# Placeholder: could call external retopology service
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_rig_autorig(self, object_name: str, rig_type: str = 'HUMAN',
                      user_prompt: str = "AI auto-rig") -> str:
        """
        AI-powered automatic rigging.

        Args:
            object_name: Mesh to rig
            rig_type: 'HUMAN', 'CREATURE', etc.
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI auto-rig for {object_name} (type: {rig_type})")
# Could use RigNet or similar AI rigging
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_animation_transfer(self, source_action: str, target_object: str,
                            user_prompt: str = "AI animation transfer") -> str:
        """
        Transfer animation from one object to another using AI.

        Args:
            source_action: Name of action to transfer
            target_object: Target object name
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI animation transfer: action='{source_action}' -> object='{target_object}'")
# Placeholder: motion retargeting with AI assistance
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_scene_setup(self, description: str, user_prompt: str = "AI scene setup") -> str:
        """
        Let AI generate a complete scene from text.

        Args:
            description: Scene description
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI scene generation: {description}")
# Placeholder: Could generate lights, objects, materials based on prompt
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_model_repair(self, object_name: str, issues: Optional[List[str]] = None,
                       user_prompt: str = "AI model repair") -> str:
        """
        AI diagnostic and repair of mesh issues.

        Args:
            object_name: Object to repair
            issues: Optional list of issues (e.g., 'non-manifold', 'holes')
            user_prompt: For telemetry

        Returns:
            Result message
        """
        issues_str = json.dumps(issues) if issues else '[]'
        code = f"""
import bpy
print(f"AI model repair for {object_name}" + (f" issues={issues_str}" if {issues_str} != '[]' else ""))
# Placeholder: AI could suggest or apply fixes
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_texture_enhance(self, material_name: str, description: str = "4k detailed",
                          user_prompt: str = "AI texture enhance") -> str:
        """
        AI upscaling/generation of textures.

        Args:
            material_name: Material to enhance
            description: Enhancement description
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI texture enhance for material '{material_name}': {description}")
# Placeholder: Could upsample texture images using ESRGAN etc.
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- AI-powered Tools (Placeholders) ---

    def ai_scene_description(self, user_prompt: str = "Describe scene") -> str:
        """
        Generate a natural language description of the current scene.

        Args:
            user_prompt: For telemetry

        Returns:
            Scene description text
        """
        code = """
import bpy
# Compile scene info into natural language (placeholder)
scene = bpy.context.scene
objs = [obj.name for obj in bpy.data.objects]
desc = f"Scene '{scene.name}' contains {len(objs)} objects: {', '.join(objs[:10])}"
if len(objs) > 10:
    desc += "..."
print(desc)
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_camera_suggestions(self, user_prompt: str = "Camera suggestions") -> List[Dict[str, Any]]:
        """
        Let AI recommend camera angles/positions.

        Args:
            user_prompt: For telemetry

        Returns:
            List of camera pose suggestions
        """
        code = """
import bpy
# Placeholder: could compute best shots based on scene bounds
suggestions = [
    {'name': 'front', 'location': [0, -5, 2], 'rotation': [1.0, 0, 0]},
    {'name': 'top', 'location': [0, 0, 5], 'rotation': [0, 0, 0]}
]
print(suggestions)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list):
                return parsed
        return []

    def ai_lighting_setup(self, mode: str = 'studio', user_prompt: str = "AI lighting setup") -> str:
        """
        AI-computed lighting setup for the scene.

        Args:
            mode: 'studio', 'outdoor', 'indoor', 'night'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI lighting setup: {mode}")
# Placeholder: could create appropriate lights based on mode
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_render_settings(self, scene_name: Optional[str] = None, user_prompt: str = "AI render settings") -> str:
        """
        Optimize render settings via AI.

        Args:
            scene_name: Optional scene to optimize
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
target_scene = bpy.data.scenes.get("{scene_name or ''}") or bpy.context.scene
print(f"AI optimizing render settings for {{target_scene.name}}")
# Placeholder: tweak samples, clamping, etc. based on hardware
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_noise_reduction(self, image_path: str, strength: float = 0.5,
                          user_prompt: str = "AI denoise") -> str:
        """
        AI-based denoising for rendered images.

        Args:
            image_path: Path to image file
            strength: Denoise strength (0-1)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI denoise for {image_path} (strength {strength})")
# Placeholder: could call external AI denoiser or use OpenCV DNN
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_upscale_render(self, image_path: str, scale: float = 2.0,
                         user_prompt: str = "AI upscale") -> str:
        """
        AI upscaling of rendered images.

        Args:
            image_path: Path to image file
            scale: Upscale factor
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI upscale {image_path} by {scale}x")
# Placeholder: use real-ESRGAN or similar
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def ai_inpaint_render(self, image_path: str, mask_path: str, prompt: str,
                         user_prompt: str = "AI inpaint") -> str:
        """
        AI inpainting for rendered images.

        Args:
            image_path: Path to image
            mask_path: Path to mask image (white = inpaint region)
            prompt: Text description for inpaint content
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"AI inpaint: image={image_path}, mask={mask_path}, prompt='{prompt}'")
# Placeholder: integrate with Stable Diffusion inpainting
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Automation & Scripting Utilities ---

    def record_actions_to_script(self, filepath: str, user_prompt: str = "Record actions") -> str:
        """
        Start recording UI actions to a Python script.

        Args:
            filepath: Output .py file path
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
print(f"Action recording to {filepath} started (placeholder)")
# Real implementation would use bpy.ops.wm.record_operator() or custom handler
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def playback_script(self, filepath: str, dry_run: bool = False,
                       user_prompt: str = "Playback script") -> str:
        """
        Execute a recorded Python script.

        Args:
            filepath: Path to .py script
            dry_run: If True, only validate without execution
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy, os
if os.path.exists("{filepath}"):
    if {dry_run}:
        print(f"Script validation (dry run): {filepath}")
    else:
        # Execute in Blender's context
        print(f"Executing script: {filepath}")
        # Would use exec or bpy.ops.text.run_script()
else:
    print(f"Script not found: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def create_parameterized_script(self, object_name: str, params: Dict[str, Any],
                                   user_prompt: str = "Create parameterized script") -> str:
        """
        Generate a configurable Python script for an object.

        Args:
            object_name: Object to generate script for
            params: Dictionary of parameters
            user_prompt: For telemetry

        Returns:
            Script content as string
        """
        code = f"""
import bpy, json
obj = bpy.data.objects.get("{object_name}")
if obj:
    # Generate a script template that can be re-run with different params
    script = f\\"""# Generated script for {object_name}
from blender_mcp_client import BlenderMCPClient
client = BlenderMCPClient()
# Apply parameters: {json.dumps(params)}
print("Script applied")
\\"""
    print(script)
else:
    print("Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def batch_process_script(self, object_names: List[str], script_content: str,
                            user_prompt: str = "Batch process script") -> List[str]:
        """
        Apply a script to multiple objects.

        Args:
            object_names: List of object names to process
            script_content: Python script to execute (will have 'object_name' variable)
            user_prompt: For telemetry

        Returns:
            List of result strings
        """
        results = []
        for name in object_names:
            try:
                # Execute script with object_name set
                # Use execute_blender_code with a wrapper
                wrapped = f"object_name = \"{name}\"\n" + script_content
                res = self.execute_blender_code(wrapped)
                results.append(f"{name}: OK")
            except Exception as e:
                results.append(f"{name}: Error - {e}")
        return results

    def validate_script(self, script_content: str, user_prompt: str = "Validate script") -> Dict[str, Any]:
        """
        Check a Python script for syntax and potential issues.

        Args:
            script_content: Script text
            user_prompt: For telemetry

        Returns:
            Dictionary with validation results
        """
        code = f"""
import py_compile, tempfile, os
script = """ + script_content.replace('"""', '\\"\\"\\"') + f"""
# Write to temp file for compile check
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(script)
    tmp_path = f.name
try:
    py_compile.compile(tmp_path, doraise=True)
    result = {{'valid': True, 'errors': []}}
except py_compile.PyCompileError as e:
    result = {{'valid': False, 'errors': [str(e)]}}
finally:
    os.unlink(tmp_path)
print(result)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {'valid': False, 'errors': ['Parse error']}

    def explain_script(self, script_content: str, user_prompt: str = "Explain script") -> str:
        """
        AI-driven explanation of what a script does.

        Args:
            script_content: Python script text
            user_prompt: For telemetry

        Returns:
            Explanation text (placeholder)
        """
        return "AI script explanation not implemented. This would use a language model to describe the script's purpose."

    def optimize_script(self, script_content: str, user_prompt: str = "Optimize script") -> str:
        """
        Optimize a Python script for performance.

        Args:
            script_content: Python script
            user_prompt: For telemetry

        Returns:
            Optimized script (placeholder)
        """
        return "AI script optimization not implemented. Would return improved version."

    def convert_script_to_mcp(self, script_content: str, user_prompt: str = "Convert to MCP") -> str:
        """
        Convert a regular Blender Python script to MCP method calls.

        Args:
            script_content: Original Blender Python script
            user_prompt: For telemetry

        Returns:
            MCP-style method calls (placeholder)
        """
        return "Conversion to MCP not implemented. Would translate API calls."

    # --- Additional Utilities ---

    def get_system_info(self, user_prompt: str = "Get system info") -> Dict[str, Any]:
        """
        Get Blender and system information.

        Returns:
            Dictionary with version, platform, GPU, etc.
        """
        code = """
import bpy, platform, sys
info = {
    'blender_version': bpy.app.version_string,
    'platform': platform.platform(),
    'python_version': sys.version,
    'has_gpu': any(dev.use for dev in bpy.context.preferences.system.devices if dev.type == 'CUDA' or dev.type == 'OPENCL'),
}
print(info)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def get_performance_stats(self, user_prompt: str = "Get performance stats") -> Dict[str, Any]:
        """
        Get current performance statistics (memory, object count, etc.).

        Returns:
            Dictionary with stats
        """
        code = """
import bpy
stats = {
    'object_count': len(bpy.data.objects),
    'mesh_count': len([o for o in bpy.data.objects if o.type == 'MESH']),
    'material_count': len(bpy.data.materials),
    'vertex_count': sum(len(m.data.vertices) for m in bpy.data.objects if m.type == 'MESH' and m.data),
    'memory_estimate_mb': bpy.context.preferences.system.memory_limit if hasattr(bpy.context.preferences.system, 'memory_limit') else None,
}
print(stats)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def validate_scene(self, user_prompt: str = "Validate scene") -> Dict[str, List[str]]:
        """
        Check for common scene issues (missing textures, unused data, etc.).

        Args:
            user_prompt: For telemetry

        Returns:
            Dictionary mapping issue types to lists
        """
        code = """
import bpy
issues = {{
    'unused_materials': [],
    'orphaned_data': [],
    'missing_textures': [],
}}
# Find unused materials
for mat in bpy.data.materials:
    if mat.users == 0:
        issues['unused_materials'].append(mat.name)
# Find orphaned meshes
for mesh in bpy.data.meshes:
    if mesh.users == 0:
        issues['orphaned_data'].append(mesh.name)
print(issues)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def find_orphaned_data(self, user_prompt: str = "Find orphaned data") -> Dict[str, List[str]]:
        """
        Find data-blocks with zero users.

        Args:
            user_prompt: For telemetry

        Returns:
            Dictionary by data type
        """
        code = """
import bpy
orphans = {}
for collection in [bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.images, bpy.data.armatures]:
    type_name = collection.__name__.split('.')[-1]
    orphan_list = [item.name for item in collection if item.users == 0]
    if orphan_list:
        orphans[type_name] = orphan_list
print(orphans)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def purge_unused_data(self, user_prompt: str = "Purge unused data") -> str:
        """
        Remove all orphaned data-blocks from the file.

        Args:
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = """
import bpy
before = sum(len(c) for c in [bpy.data.meshes, bpy.data.materials, bpy.data.images])
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
after = sum(len(c) for c in [bpy.data.meshes, bpy.data.materials, bpy.data.images])
deleted = before - after
print(f"Purged {{deleted}} data-blocks")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def pack_resources_into_blend(self, user_prompt: str = "Pack resources") -> str:
        """
        Pack all external resources (images, etc.) into the .blend file.

        Args:
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = """
import bpy
bpy.ops.file.pack_all()
print("Packed all resources into blend file")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def list_objects_by_type(self, type: str = 'MESH', user_prompt: str = "List objects by type") -> List[Dict[str, str]]:
        """
        List objects filtered by type.

        Args:
            type: Object type (MESH, LIGHT, CAMERA, ARMATURE, etc.)
            user_prompt: For telemetry

        Returns:
            List of object info dicts
        """
        code = f"""
import bpy
objs = []
for obj in bpy.data.objects:
    if obj.type == '{type.upper()}':
        objs.append({{'name': obj.name, 'type': obj.type}})
print(objs)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list):
                return parsed
        return []

    def find_objects_by_name(self, pattern: str, regex: bool = False,
                            user_prompt: str = "Find objects by name") -> List[str]:
        """
        Search objects by name (substring or regex).

        Args:
            pattern: Search pattern
            regex: If True, treat as regex; else substring match
            user_prompt: For telemetry

        Returns:
            List of matching object names
        """
        import re
        code = f"""
import bpy
import re
matches = []
pattern = r"{pattern}" if {regex} else None
for obj in bpy.data.objects:
    if {regex}:
        if re.search(pattern, obj.name):
            matches.append(obj.name)
    else:
        if "{pattern}" in obj.name:
            matches.append(obj.name)
print(matches)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list):
                return parsed
        return []

    def get_scene_bbox(self, user_prompt: str = "Get scene bbox") -> Dict[str, List[float]]:
        """
        Compute overall bounding box of all mesh objects.

        Args:
            user_prompt: For telemetry

        Returns:
            {'min': [x,y,z], 'max': [x,y,z]}
        """
        code = """
import bpy
from mathutils import Vector
min_vec = None
max_vec = None
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        for v in bbox:
            if min_vec is None:
                min_vec = v.copy()
                max_vec = v.copy()
            else:
                min_vec = Vector((min(min_vec[i], v[i]) for i in range(3)))
                max_vec = Vector((max(max_vec[i], v[i]) for i in range(3)))
if min_vec:
    print({{'min': list(min_vec), 'max': list(max_vec)}})
else:
    print({{}})
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def calculate_scene_stats(self, user_prompt: str = "Calculate scene stats") -> Dict[str, Any]:
        """
        Compute statistics about the scene.

        Args:
            user_prompt: For telemetry

        Returns:
            Dictionary of stats (poly count, material count, etc.)
        """
        code = """
import bpy
total_verts = 0
total_edges = 0
total_faces = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mesh = obj.data
        total_verts += len(mesh.vertices)
        total_edges += len(mesh.edges)
        total_faces += len(mesh.polygons)
stats = {
    'object_count': len(bpy.data.objects),
    'mesh_count': len([o for o in bpy.data.objects if o.type == 'MESH']),
    'total_vertices': total_verts,
    'total_edges': total_edges,
    'total_faces': total_faces,
    'material_count': len(bpy.data.materials),
    'texture_count': len(bpy.data.images),
}
print(stats)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}


# Convenience function
def get_ai_client() -> BlenderAIClient:
    """Get a BlenderAIClient instance with default settings."""
    return BlenderAIClient()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Blender MCP AI & Utilities Client")
    parser.add_argument("tool", help="Tool to call")
    parser.add_argument("--params", type=str, help="JSON string of parameters")
    parser.add_argument("--server", default="blender", help="mcporter server name")
    args = parser.parse_args()

    try:
        client = get_ai_client()
        params = json.loads(args.params) if args.params else {}
        method = getattr(client, args.tool, None)
        if not method:
            print(f"Error: Unknown tool '{args.tool}'", file=sys.stderr)
            sys.exit(1)

        result = method(**params)
        if isinstance(result, bytes):
            print(f"<binary data: {len(result)} bytes>")
        else:
            print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
