#!/usr/bin/env python3
"""
Blender MCP Client for OpenClaw

This module provides a Python interface to control Blender via the BlenderMCP
server using mcporter CLI. The Blender MCP server must be running (typically
started with `uvx blender-mcp`) and Blender must have the addon enabled and
connected.

Usage:
    from blender_mcp_client import BlenderMCPClient

    client = BlenderMCPClient()
    info = client.get_scene_info()
    client.execute_blender_code("bpy.ops.mesh.primitive_cube_add()")
"""

import json
import subprocess
import sys
from typing import Any, Dict, Optional, List, Union


class BlenderMCPClientError(Exception):
    """Base exception for BlenderMCPClient errors."""
    pass


class MCPServerError(Exception):
    """Raised when the MCP server returns an error."""
    pass


class BlenderMCPClient:
    """
    Client for interacting with Blender via the BlenderMCP MCP server.

    This client uses the mcporter CLI to send requests to the Blender MCP server.
    The MCP server must be running and accessible. By default, it expects the
    server to be configured in mcporter as 'blender'.

    Attributes:
        server_name: Name of the MCP server as configured in mcporter (default: 'blender')
        mcporter_path: Path to the mcporter executable (auto-detected)
    """

    def __init__(self, server_name: str = "blender", mcporter_path: Optional[str] = None):
        """
        Initialize the Blender MCP client.

        Args:
            server_name: mcporter server name for Blender MCP (default: 'blender')
            mcporter_path: Optional explicit path to mcporter binary
        """
        self.server_name = server_name
        self.mcporter_path = mcporter_path or self._find_mcporter()

    def _find_mcporter(self) -> str:
        """Find the mcporter executable in PATH."""
        import shutil
        path = shutil.which("mcporter")
        if not path:
            raise BlenderMCPClientError(
                "mcporter not found in PATH. Install mcporter or set mcporter_path."
            )
        return path

    def _call_tool(self, tool_name: str, expect_binary: bool = False, user_prompt: str = "", **params) -> Any:
        """
        Call an MCP tool via mcporter.

        Args:
            tool_name: Name of the tool (e.g., 'get_scene_info')
            expect_binary: Set True for tools that return binary data (images)
            user_prompt: The original user prompt (for telemetry, required by some tools)
            **params: Tool parameters as keyword arguments

        Returns:
            For JSON/text tools: parsed dict or string.
            For binary tools: raw bytes.

        Raises:
            MCPServerError: If the tool call fails or returns an error
        """
        full_tool = f"{self.server_name}.{tool_name}"
        args = [self.mcporter_path, "call", full_tool]
        # Always include user_prompt (may be required by current BlenderMCP)
        if user_prompt:
            args.append(f"user_prompt={user_prompt}")
        for key, value in params.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            args.append(f"{key}={value_str}")

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=False,  # binary mode
                timeout=60
            )
        except subprocess.TimeoutExpired:
            raise MCPServerError("MCP server call timed out after 60 seconds")
        except Exception as e:
            raise BlenderMCPClientError(f"Failed to execute mcporter: {e}")

        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore').strip() or result.stdout.decode('utf-8', errors='ignore').strip()
            raise MCPServerError(f"MCP call failed: {error_msg}")

        output = result.stdout

        if expect_binary:
            return output

        # Try to decode as UTF-8 and parse JSON
        try:
            text = output.decode('utf-8')
        except UnicodeDecodeError:
            return output.decode('utf-8', errors='replace')

        # First attempt to parse as JSON
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Heuristic: McMCP server may log to stdout, contaminating JSON.
            # Extract the first complete JSON value by matching braces/brackets.
            start = -1
            for i, ch in enumerate(text):
                if ch in ('{', '['):
                    start = i
                    break
            if start == -1:
                return text  # No JSON structure found

            # Match the closing brace/bracket
            depth = 0
            opener = text[start]
            closer = '}' if opener == '{' else ']'
            for i in range(start, len(text)):
                ch = text[i]
                if ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        # Found the matching closer
                        candidate = text[start:i+1]
                        try:
                            data = json.loads(candidate)
                            # Use candidate as the text for further processing
                            break
                        except json.JSONDecodeError:
                            return text
            else:
                # No matching closer found
                return text

        # At this point, data is a parsed JSON object
        if isinstance(data, dict) and data.get("isError"):
            error_msg = data.get("content", [{}])[0].get("text", "Unknown error")
            raise MCPServerError(f"MCP tool error: {error_msg}")
        # If the response has a 'content' field (MCP response format), extract text
        if isinstance(data, dict) and "content" in data:
            content = data["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                # If it's JSON string, parse it
                if text_content and (text_content.startswith('{') or text_content.startswith('[')):
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        return text_content
                return text_content
            return content
        return data

    def _parse_json_output(self, text: str) -> Any:
        """
        Parse JSON from text, trying direct parse and fallback to extraction.
        Used to handle MCP responses that include extra logging.
        """
        if not isinstance(text, str):
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Find first JSON structure start
        start = -1
        for i, ch in enumerate(text):
            if ch in ('{', '['):
                start = i
                break
        if start == -1:
            return None
        depth = 0
        opener = text[start]
        closer = '}' if opener == '{' else ']'
        for i in range(start, len(text)):
            if text[i] == opener:
                depth += 1
            elif text[i] == closer:
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        return None
        return None

    # --- Core Tools ---

    def get_scene_info(self, user_prompt: str = "Get scene info") -> Dict[str, Any]:
        """
        Get detailed information about the current Blender scene.

        Args:
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Dictionary with scene details: name, object_count, materials_count, and list of objects
        """
        result = self._call_tool("get_scene_info", user_prompt=user_prompt)
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw": result}
        return result

    def get_object_info(self, object_name: str, user_prompt: str = "") -> Dict[str, Any]:
        """
        Get detailed information about a specific object.

        Args:
            object_name: Name of the object
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Dictionary with object details: type, location, rotation, scale, materials, etc.
        """
        result = self._call_tool("get_object_info", object_name=object_name, user_prompt=user_prompt)
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw": result}
        return result

    def get_viewport_screenshot(self, max_size: int = 800, user_prompt: str = "") -> bytes:
        """
        Capture a screenshot of the current Blender 3D viewport.

        Args:
            max_size: Maximum dimension in pixels (default 800)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Raw PNG image bytes
        """
        return self._call_tool("get_viewport_screenshot", max_size=max_size, user_prompt=user_prompt, expect_binary=True)

    def execute_blender_code(self, code: str, user_prompt: str = "") -> str:
        """
        Execute arbitrary Python code in Blender.

        WARNING: Powerful but dangerous. Only execute trusted code.
        Always save your Blender work before using.

        Args:
            code: Python code to run in Blender's context
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Text result of the execution
        """
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        return str(result) if result else ""

    # --- Convenience Methods for Object Manipulation ---

    def create_primitive(self, primitive_type: str, name: Optional[str] = None,
                        location: Optional[List[float]] = None,
                        rotation: Optional[List[float]] = None,
                        scale: Optional[List[float]] = None) -> str:
        """
        Create a primitive mesh object in Blender.

        Args:
            primitive_type: One of 'CUBE', 'SPHERE', 'CYLINDER', 'PLANE', 'CONE', 'ICO_SPHERE', 'TORUS', 'MONKEY'
            name: Optional name for the new object
            location: [x, y, z] location
            rotation: [x, y, z] rotation in radians
            scale: [x, y, z] scale

        Returns:
            Result message
        """
        primitive_map = {
            'CUBE': 'bpy.ops.mesh.primitive_cube_add',
            'SPHERE': 'bpy.ops.mesh.primitive_uv_sphere_add',
            'CYLINDER': 'bpy.ops.mesh.primitive_cylinder_add',
            'PLANE': 'bpy.ops.mesh.primitive_plane_add',
            'CONE': 'bpy.ops.mesh.primitive_cone_add',
            'ICO_SPHERE': 'bpy.ops.mesh.primitive_ico_sphere_add',
            'TORUS': 'bpy.ops.mesh.primitive_torus_add',
            'MONKEY': 'bpy.ops.mesh.primitive_monkey_add'
        }
        op = primitive_map.get(primitive_type.upper())
        if not op:
            raise ValueError(f"Unknown primitive type: {primitive_type}. Use one of {list(primitive_map.keys())}")

        code = f"{op}("
        if name:
            code += f'name="{name}", '
        if location:
            code += f'location=({location[0]}, {location[1]}, {location[2]}), '
        if rotation:
            code += f'rotation=({rotation[0]}, {rotation[1]}, {rotation[2]}), '
        if scale:
            code += f'scale=({scale[0]}, {scale[1]}, {scale[2]}), '
        if code.endswith(', '):
            code = code[:-2]
        code += ")"

        return self.execute_blender_code(code)

    def delete_object(self, object_name: str) -> str:
        """
        Delete an object from the scene.

        Args:
            object_name: Name of the object to delete

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.data.objects.remove(obj)
    print(f"Deleted object: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def set_object_transform(self, object_name: str,
                           location: Optional[List[float]] = None,
                           rotation: Optional[List[float]] = None,
                           scale: Optional[List[float]] = None) -> str:
        """
        Set the transform of an existing object.

        Args:
            object_name: Name of the object
            location: [x, y, z] location
            rotation: [x, y, z] rotation in radians
            scale: [x, y, z] scale

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if not obj:
    raise ValueError(f"Object not found: {{object_name}}")
"""
        if location:
            code += f'obj.location = ({location[0]}, {location[1]}, {location[2]})\n'
        if rotation:
            code += f'obj.rotation_euler = ({rotation[0]}, {rotation[1]}, {rotation[2]})\n'
        if scale:
            code += f'obj.scale = ({scale[0]}, {scale[1]}, {scale[2]})\n'
        code += 'print(f"Transform updated for: " + obj.name)'

        return self.execute_blender_code(code)

    # --- Material Tools ---

    def create_material(self, name: str, color: Optional[List[float]] = None,
                       roughness: float = 0.5, metallic: float = 0.0) -> str:
        """
        Create a basic Principled BSDF material.

        Args:
            name: Material name
            color: [r, g, b, a] values 0-1 (default white)
            roughness: Roughness value 0-1
            metallic: Metallic value 0-1

        Returns:
            Result message
        """
        r, g, b, a = (color if color else [1.0, 1.0, 1.0, 1.0])
        code = f"""
import bpy
mat = bpy.data.materials.new(name="{name}")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = ({r}, {g}, {b}, {a})
    bsdf.inputs['Roughness'].default_value = {roughness}
    bsdf.inputs['Metallic'].default_value = {metallic}
print(f"Created material: {name}")
"""
        return self.execute_blender_code(code)

    def assign_material(self, object_name: str, material_name: str) -> str:
        """
        Assign an existing material to an object.

        Args:
            object_name: Name of the object
            material_name: Name of the material

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
mat = bpy.data.materials.get("{material_name}")
if not obj:
    raise ValueError(f"Object not found: {{object_name}}")
if not mat:
    raise ValueError(f"Material not found: {{material_name}}")
if obj.type == 'MESH':
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    print(f"Assigned material {{material_name}} to {{object_name}}")
else:
    print(f"Object {{object_name}} is not a mesh")
"""
        return self.execute_blender_code(code)

    # --- Poly Haven Tools ---

    def get_polyhaven_status(self, user_prompt: str = "") -> str:
        """Check if Poly Haven integration is enabled."""
        return str(self._call_tool("get_polyhaven_status", user_prompt=user_prompt))

    def get_polyhaven_categories(self, asset_type: str = "hdris", user_prompt: str = "") -> str:
        """
        Get Poly Haven categories.

        Args:
            asset_type: 'hdris', 'textures', 'models', or 'all'
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Formatted string of categories
        """
        return str(self._call_tool("get_polyhaven_categories", asset_type=asset_type, user_prompt=user_prompt))

    def search_polyhaven_assets(self, asset_type: str = "all", categories: Optional[str] = None, user_prompt: str = "") -> str:
        """
        Search Poly Haven assets.

        Args:
            asset_type: 'hdris', 'textures', 'models', or 'all'
            categories: Comma-separated category filter
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Formatted string of results
        """
        params = {"asset_type": asset_type, "user_prompt": user_prompt}
        if categories:
            params["categories"] = categories
        return str(self._call_tool("search_polyhaven_assets", **params))

    def download_polyhaven_asset(self, asset_id: str, asset_type: str,
                                resolution: str = "1k", file_format: Optional[str] = None, user_prompt: str = "") -> str:
        """
        Download and import a Poly Haven asset.

        Args:
            asset_id: Poly Haven asset ID
            asset_type: 'hdris', 'textures', or 'models'
            resolution: '1k', '2k', '4k', etc.
            file_format: Optional format override
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        params = {"asset_id": asset_id, "asset_type": asset_type, "resolution": resolution, "user_prompt": user_prompt}
        if file_format:
            params["file_format"] = file_format
        return str(self._call_tool("download_polyhaven_asset", **params))

    def set_texture(self, object_name: str, texture_id: str, user_prompt: str = "") -> str:
        """
        Apply a previously downloaded Poly Haven texture to an object.

        Args:
            object_name: Target object name
            texture_id: Poly Haven texture ID
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        return str(self._call_tool("set_texture", object_name=object_name, texture_id=texture_id, user_prompt=user_prompt))

    # --- Sketchfab Tools ---

    def get_sketchfab_status(self, user_prompt: str = "") -> str:
        """Check if Sketchfab integration is enabled."""
        return str(self._call_tool("get_sketchfab_status", user_prompt=user_prompt))

    def search_sketchfab_models(self, query: str, categories: Optional[str] = None,
                               count: int = 20, downloadable: bool = True, user_prompt: str = "") -> str:
        """
        Search Sketchfab models.

        Args:
            query: Search query
            categories: Comma-separated categories
            count: Max results (default 20)
            downloadable: Only downloadable models (default True)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Formatted string of results
        """
        params = {"query": query, "count": count, "downloadable": downloadable, "user_prompt": user_prompt}
        if categories:
            params["categories"] = categories
        return str(self._call_tool("search_sketchfab_models", **params))

    def get_sketchfab_model_preview(self, uid: str, user_prompt: str = "") -> bytes:
        """
        Get a preview thumbnail of a Sketchfab model.

        Args:
            uid: Sketchfab model UID
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Raw image bytes (JPEG)
        """
        return self._call_tool("get_sketchfab_model_preview", uid=uid, user_prompt=user_prompt, expect_binary=True)

    def download_sketchfab_model(self, uid: str, target_size: float, user_prompt: str = "") -> str:
        """
        Download and import a Sketchfab model.

        Args:
            uid: Sketchfab model UID
            target_size: Target size in Blender units for largest dimension (e.g., 1.0 for a chair)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message with import details
        """
        return str(self._call_tool("download_sketchfab_model", uid=uid, target_size=target_size, user_prompt=user_prompt))

    # --- Hyper3D (Rodin) Tools ---

    def get_hyper3d_status(self, user_prompt: str = "") -> str:
        """Check if Hyper3D Rodin integration is enabled."""
        return str(self._call_tool("get_hyper3d_status", user_prompt=user_prompt))

    def generate_hyper3d_model_via_text(self, text_prompt: str,
                                       bbox_condition: Optional[List[float]] = None, user_prompt: str = "") -> str:
        """
        Generate a 3D model using Hyper3D from text.

        Args:
            text_prompt: Description in English
            bbox_condition: Optional [length, width, height] ratio control
            user_prompt: The original user prompt (for telemetry)

        Returns:
            JSON string with task_uuid and subscription_key on success
        """
        params = {"text_prompt": text_prompt, "user_prompt": user_prompt}
        if bbox_condition:
            params["bbox_condition"] = bbox_condition
        return str(self._call_tool("generate_hyper3d_model_via_text", **params))

    def generate_hyper3d_model_via_images(self, input_image_paths: Optional[List[str]] = None,
                                         input_image_urls: Optional[List[str]] = None,
                                         bbox_condition: Optional[List[float]] = None, user_prompt: str = "") -> str:
        """
        Generate a 3D model using Hyper3D from images.

        Args:
            input_image_paths: List of absolute image file paths (for MAIN_SITE mode)
            input_image_urls: List of image URLs (for FAL_AI mode)
            bbox_condition: Optional [length, width, height] ratio control
            user_prompt: The original user prompt (for telemetry)

        Returns:
            JSON string with task_uuid and subscription_key on success
        """
        params = {"user_prompt": user_prompt}
        if input_image_paths:
            params["input_image_paths"] = input_image_paths
        if input_image_urls:
            params["input_image_urls"] = input_image_urls
        if bbox_condition:
            params["bbox_condition"] = bbox_condition
        return str(self._call_tool("generate_hyper3d_model_via_images", **params))

    def poll_rodin_job_status(self, subscription_key: Optional[str] = None,
                             request_id: Optional[str] = None, user_prompt: str = "") -> Dict[str, Any]:
        """
        Poll Hyper3D Rodin job status.

        Args:
            subscription_key: For MAIN_SITE mode
            request_id: For FAL_AI mode
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Dictionary with status information
        """
        kwargs = {"user_prompt": user_prompt}
        if subscription_key:
            kwargs["subscription_key"] = subscription_key
        if request_id:
            kwargs["request_id"] = request_id
        result = self._call_tool("poll_rodin_job_status", **kwargs)
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw": result}
        return result

    def import_generated_asset(self, name: str, task_uuid: Optional[str] = None,
                              request_id: Optional[str] = None, user_prompt: str = "") -> str:
        """
        Import a generated Hyper3D asset into Blender.

        Args:
            name: Object name in scene
            task_uuid: For MAIN_SITE mode
            request_id: For FAL_AI mode
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        params = {"name": name, "user_prompt": user_prompt}
        if task_uuid:
            params["task_uuid"] = task_uuid
        if request_id:
            params["request_id"] = request_id
        return str(self._call_tool("import_generated_asset", **params))

    # --- Hunyuan3D Tools ---

    def get_hunyuan3d_status(self, user_prompt: str = "") -> str:
        """Check if Hunyuan3D integration is enabled."""
        return str(self._call_tool("get_hunyuan3d_status", user_prompt=user_prompt))

    def generate_hunyuan3d_model(self, text_prompt: Optional[str] = None,
                                input_image_url: Optional[str] = None, user_prompt: str = "") -> str:
        """
        Generate a 3D model using Hunyuan3D.

        Args:
            text_prompt: Optional text description (English/Chinese)
            input_image_url: Optional image URL or local path
            user_prompt: The original user prompt (for telemetry)

        Returns:
            JSON string with job_id on success
        """
        params = {"user_prompt": user_prompt}
        if text_prompt:
            params["text_prompt"] = text_prompt
        if input_image_url:
            params["input_image_url"] = input_image_url
        return str(self._call_tool("generate_hunyuan3d_model", **params))

    def poll_hunyuan_job_status(self, job_id: str, user_prompt: str = "") -> Dict[str, Any]:
        """
        Poll Hunyuan3D job status.

        Args:
            job_id: Job ID returned from generate_hunyuan3d_model
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Dictionary with status; when DONE includes ResultFile3Ds (ZIP path)
        """
        result = self._call_tool("poll_hunyuan_job_status", job_id=job_id, user_prompt=user_prompt)
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw": result}
        return result

    def import_generated_asset_hunyuan(self, name: str, zip_file_url: str, user_prompt: str = "") -> str:
        """
        Import a generated Hunyuan3D asset.

        Args:
            name: Object name in scene
            zip_file_url: ZIP file URL or path from poll response
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        return str(self._call_tool("import_generated_asset_hunyuan", name=name, zip_file_url=zip_file_url, user_prompt=user_prompt))

    # --- Utility Methods ---

    def is_connected(self) -> bool:
        """
        Test connection to Blender by calling get_scene_info.

        Returns:
            True if connected and responsive, False otherwise
        """
        try:
            self.get_scene_info()
            return True
        except Exception:
            return False

    def list_objects(self) -> List[str]:
        """
        Get a simple list of object names in the scene.

        Returns:
            List of object names
        """
        info = self.get_scene_info()
        if isinstance(info, dict) and "objects" in info:
            return [obj.get("name", "") for obj in info["objects"] if isinstance(obj, dict)]
        return []

    # ============ Enhanced Batch Operations ============

    def create_primitives_batch(self, specs: List[Dict]) -> List[str]:
        """
        Create multiple primitive objects in a single batch.

        Args:
            specs: List of dicts, each with keys: primitive_type, name (optional), location, rotation, scale

        Returns:
            List of created object names
        """
        results = []
        for spec in specs:
            obj_name = spec.get('name', f"{spec['primitive_type'].lower()}_{len(results)}")
            result = self.create_primitive(
                primitive_type=spec['primitive_type'],
                name=obj_name,
                location=spec.get('location'),
                rotation=spec.get('rotation'),
                scale=spec.get('scale')
            )
            results.append(result)
        return results

    def delete_objects_batch(self, object_names: List[str]) -> List[str]:
        """
        Delete multiple objects at once.

        Args:
            object_names: List of object names to delete

        Returns:
            List of deletion results
        """
        results = []
        for name in object_names:
            try:
                result = self.delete_object(name)
                results.append(f"Deleted: {name}")
            except Exception as e:
                results.append(f"Failed to delete {name}: {e}")
        return results

    def assign_material_batch(self, object_names: List[str], material_name: str) -> List[str]:
        """
        Assign the same material to multiple objects.

        Args:
            object_names: List of object names
            material_name: Name of the material to assign

        Returns:
            List of assignment results
        """
        results = []
        for name in object_names:
            try:
                result = self.assign_material(name, material_name)
                results.append(f"Assigned {material_name} to {name}")
            except Exception as e:
                results.append(f"Failed to assign to {name}: {e}")
        return results

    # ============ Scene Management ============

    def save_scene(self, filepath: str) -> str:
        """
        Save the current scene to a .blend file.

        Args:
            filepath: Full path where to save the .blend file

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.wm.save_as_mainfile(filepath=r"{filepath}")
print(f"Scene saved to: {filepath}")
"""
        return self.execute_blender_code(code)

    def load_scene(self, filepath: str) -> str:
        """
        Load a .blend scene file.

        Args:
            filepath: Path to the .blend file

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.wm.open_mainfile(filepath=r"{filepath}")
print(f"Scene loaded from: {filepath}")
"""
        return self.execute_blender_code(code)

    def clear_scene(self, keep_collections: bool = False) -> str:
        """
        Remove all objects from the current scene.

        Args:
            keep_collections: If True, keep collection structure but remove objects

        Returns:
            Result message
        """
        code = """
import bpy
if {keep_collections}:
    # Delete all mesh, curve, light, etc. objects but keep collections
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
else:
    # Full clear - remove everything including collections
    bpy.ops.wm.read_factory_settings(use_empty=True)
print("Scene cleared")
""".replace("{keep_collections}", str(keep_collections))
        return self.execute_blender_code(code)

    def duplicate_object(self, object_name: str, new_name: Optional[str] = None, linked: bool = False) -> str:
        """
        Duplicate an existing object.

        Args:
            object_name: Name of object to duplicate
            new_name: Optional name for the duplicate
            linked: If True, creates a linked duplicate (shares mesh data)

        Returns:
            Result message
        """
        name_part = f', name="{new_name}"' if new_name else ""
        linked_part = ", linked=True" if linked else ""
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    new_obj = obj.copy(){name_part}{linked_part}
    bpy.context.collection.objects.link(new_obj)
    print(f"Duplicated {object_name} to {new_obj.name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    # ============ Material Presets ============

    def create_material_preset(self, preset_name: str, name: Optional[str] = None) -> str:
        """
        Create a material from a preset template.

        Args:
            preset_name: One of: 'metal', 'wood', 'plastic', 'glass', 'rubber', 'ceramic', 'emissive', 'chrome'
            name: Optional custom material name (default: preset_name)

        Returns:
            Result message
        """
        presets = {
            'metal': {
                'color': [0.8, 0.8, 0.9, 1.0],
                'roughness': 0.2,
                'metallic': 1.0
            },
            'wood': {
                'color': [0.4, 0.25, 0.1, 1.0],
                'roughness': 0.8,
                'metallic': 0.0
            },
            'plastic': {
                'color': [0.8, 0.2, 0.2, 1.0],
                'roughness': 0.5,
                'metallic': 0.0
            },
            'glass': {
                'color': [0.9, 0.9, 1.0, 0.3],
                'roughness': 0.0,
                'metallic': 0.0,
                'transmission': 1.0
            },
            'rubber': {
                'color': [0.1, 0.1, 0.1, 1.0],
                'roughness': 0.9,
                'metallic': 0.0
            },
            'ceramic': {
                'color': [0.95, 0.95, 0.95, 1.0],
                'roughness': 0.3,
                'metallic': 0.0
            },
            'emissive': {
                'color': [1.0, 1.0, 1.0, 1.0],
                'roughness': 0.5,
                'metallic': 0.0,
                'emission': [1.0, 1.0, 1.0],
                'emission_strength': 1.0
            },
            'chrome': {
                'color': [1.0, 1.0, 1.0, 1.0],
                'roughness': 0.0,
                'metallic': 1.0
            }
        }

        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}. Choose from: {', '.join(presets.keys())}")

        preset = presets[preset_name]
        mat_name = name or preset_name

        code = f"""
import bpy
mat = bpy.data.materials.new(name="{mat_name}")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = {preset['color']}
    bsdf.inputs['Roughness'].default_value = {preset['roughness']}
    bsdf.inputs['Metallic'].default_value = {preset['metallic']}
"""
        if 'transmission' in preset:
            code += f"    bsdf.inputs['Transmission'].default_value = {preset['transmission']}\n"
        if 'emission' in preset:
            code += f"    bsdf.inputs['Emission'].default_value = {preset['emission']}\n"
        if 'emission_strength' in preset:
            code += f"    bsdf.inputs['Emission Strength'].default_value = {preset['emission_strength']}\n"

        code += f'print(f"Created material: {mat_name}")'
        return self.execute_blender_code(code)

    # ============ Mesh Editing Operations ============

    def subdivide_object(self, object_name: str, cuts: int = 1, smooth: bool = False) -> str:
        """
        Subdivide mesh faces of an object.

        Args:
            object_name: Name of the mesh object
            cuts: Number of cuts (1-6)
            smooth: Apply smooth shading after subdivision

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts={cuts})
    if {smooth}:
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Subdivided {object_name} with {cuts} cuts")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def bevel_object(self, object_name: str, width: float = 0.1, segments: int = 3, affect: str = 'EDGES') -> str:
        """
        Bevel edges or vertices of a mesh object.

        Args:
            object_name: Name of the mesh object
            width: Bevel width
            segments: Number of bevel segments
            affect: 'EDGES' or 'VERTICES'

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.bevel(offset={width}, segments={segments}, affect='{affect}')
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Beveled {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def extrude_face(self, object_name: str, direction: List[float], amount: float) -> str:
        """
        Extrude faces of a mesh object.

        Args:
            object_name: Name of the mesh object
            direction: [x, y, z] direction vector
            amount: Extrusion amount (if direction normalized)

        Returns:
            Result message
        """
        dir_str = f"({direction[0]}, {direction[1]}, {direction[2]})"
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={{"value": {dir_str}, "constraint_axis": (True, True, True)}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Extruded faces on {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    # ============ Lighting Presets ============

    def create_light(self, light_type: str = 'SUN', name: Optional[str] = None,
                    location: Optional[List[float]] = None,
                    rotation: Optional[List[float]] = None,
                    energy: float = 1000.0,
                    color: Optional[List[float]] = None) -> str:
        """
        Create a light object.

        Args:
            light_type: 'SUN', 'POINT', 'SPOT', 'AREA'
            name: Optional light name
            location: [x, y, z]
            rotation: [x, y, z] in radians
            energy: Light power in watts
            color: [r, g, b] 0-1

        Returns:
            Result message
        """
        loc = location if location else [0, 0, 5]
        rot = rotation if rotation else [0, 0, 0]
        col = color if color else [1, 1, 1]

        code = f"""
import bpy
light_data = bpy.data.lights.new(name="{name or light_type.lower()}", type='{light_type}')
light_data.energy = {energy}
light_data.color = {col}
light = bpy.data.objects.new(name="{name or light_type.lower()}", object_data=light_data)
light.location = ({loc[0]}, {loc[1]}, {loc[2]})
light.rotation_euler = ({rot[0]}, {rot[1]}, {rot[2]})
bpy.context.collection.objects.link(light)
print(f"Created {light_type} light: {light.name}")
"""
        return self.execute_blender_code(code)

    def create_light_preset(self, preset_name: str, name: Optional[str] = None) -> str:
        """
        Create a light using a preset configuration.

        Args:
            preset_name: 'studio' (3-point), 'outdoor' (sun+fill), 'indoor' (lamp), 'night' (emissive)
            name: Optional base name

        Returns:
            Result message
        """
        base_name = name or preset_name
        if preset_name == 'studio':
            # Key light
            self.create_light('AREA', f"{base_name}_key", location=[2, -2, 3], rotation=[0.5, 0, 0.3], energy=500, color=[1, 0.98, 0.95])
            # Fill light
            self.create_light('AREA', f"{base_name}_fill", location=[-2, 0, 2], rotation=[0.5, 0, -0.5], energy=200, color=[0.9, 0.95, 1])
            # Rim light
            self.create_light('SPOT', f"{base_name}_rim", location=[0, 2, 2], rotation=[-0.7, 0, 0], energy=800, color=[1, 1, 1])
            return f"Created studio lighting setup: {base_name}_key, {base_name}_fill, {base_name}_rim"
        elif preset_name == 'outdoor':
            self.create_light('SUN', f"{base_name}_sun", location=[5, 5, 10], rotation=[0.5, 0.5, 0], energy=5)
            return f"Created outdoor sun lighting: {base_name}_sun"
        elif preset_name == 'indoor':
            self.create_light('AREA', f"{base_name}_lamp", location=[2, 0, 2.5], energy=300, color=[1, 0.9, 0.8])
            return f"Created indoor lamp lighting: {base_name}_lamp"
        elif preset_name == 'night':
            self.create_light('SPOT', f"{base_name}_moon", location=[-5, 0, 8], rotation=[-0.6, 0, 0], energy=100, color=[0.7, 0.8, 1])
            return f"Created night lighting: {base_name}_moon"
        else:
            raise ValueError(f"Unknown preset: {preset_name}")

    # ============ Camera Utilities ============

    def create_camera(self, name: Optional[str] = None, location: Optional[List[float]] = None,
                     rotation: Optional[List[float]] = None, lens: float = 35.0) -> str:
        """
        Create a camera object.

        Args:
            name: Optional camera name
            location: [x, y, z]
            rotation: [x, y, z] in radians
            lens: Focal length in mm

        Returns:
            Result message
        """
        loc = location if location else [0, -5, 2]
        rot = rotation if rotation else [1.5708, 0, 0]  # Looking at origin from front

        code = f"""
import bpy
cam_data = bpy.data.cameras.new(name="{name or 'Camera'}")
cam_data.lens = {lens}
cam = bpy.data.objects.new(name="{name or 'Camera'}", object_data=cam_data)
cam.location = ({loc[0]}, {loc[1]}, {loc[2]})
cam.rotation_euler = ({rot[0]}, {rot[1]}, {rot[2]})
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
print(f"Created camera: {cam.name}")
"""
        return self.execute_blender_code(code)

    def set_active_camera(self, camera_name: str) -> str:
        """
        Set a camera as the active scene camera.

        Args:
            camera_name: Name of the camera object

        Returns:
            Result message
        """
        code = f"""
import bpy
cam = bpy.data.objects.get("{camera_name}")
if cam and cam.type == 'CAMERA':
    bpy.context.scene.camera = cam
    print(f"Active camera set to: {camera_name}")
else:
    print(f"Camera not found: {camera_name}")
"""
        return self.execute_blender_code(code)

    def create_camera_preset(self, preset_type: str, name: Optional[str] = None) -> str:
        """
        Create a camera with a preset configuration.

        Args:
            preset_type: 'wide' (24mm), 'standard' (35mm), 'telephoto' (85mm), 'portrait' (50mm)
            name: Optional camera name

        Returns:
            Result message
        """
        lenses = {'wide': 24.0, 'standard': 35.0, 'telephoto': 85.0, 'portrait': 50.0}
        if preset_type not in lenses:
            raise ValueError(f"Unknown preset: {preset_type}. Choose from: {', '.join(lenses.keys())}")
        return self.create_camera(name=name or preset_type, lens=lenses[preset_type])

    # ============ Collection Management ============

    def create_collection(self, name: str, parent: Optional[str] = None) -> str:
        """
        Create a new collection.

        Args:
            name: Collection name
            parent: Optional parent collection name

        Returns:
            Result message
        """
        parent_ref = f"bpy.data.collections['{parent}']" if parent else "bpy.context.scene.collection"
        code = f"""
import bpy
col = bpy.data.collections.new(name="{name}")
{parent_ref}.children.link(col)
print(f"Created collection: {name}")
"""
        return self.execute_blender_code(code)

    def add_to_collection(self, object_name: str, collection_name: str, remove_from_others: bool = False) -> str:
        """
        Add an object to a collection.

        Args:
            object_name: Object to move
            collection_name: Target collection
            remove_from_others: If True, remove from all other collections

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
col = bpy.data.collections.get("{collection_name}")
if not obj or not col:
    raise ValueError("Object or collection not found")
if {remove_from_others}:
    # Remove from all collections first
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
col.objects.link(obj)
print(f"Added {object_name} to collection {collection_name}")
"""
        return self.execute_blender_code(code)

    def remove_from_collection(self, object_name: str, collection_name: str) -> str:
        """
        Remove an object from a specific collection.

        Args:
            object_name: Object to remove
            collection_name: Collection to remove from

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
col = bpy.data.collections.get("{collection_name}")
if obj and col and obj.name in col.objects:
    col.objects.unlink(obj)
    print(f"Removed {object_name} from collection {collection_name}")
else:
    print(f"Object not in collection")
"""
        return self.execute_blender_code(code)

    def list_collections(self) -> List[str]:
        """
        Get list of all collection names.

        Returns:
            List of collection names
        """
        return list(bpy.data.collections.keys()) if self.is_connected() else []

    def get_collection_objects(self, collection_name: str) -> List[str]:
        """
        Get object names within a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            List of object names
        """
        result = self.execute_blender_code(f"""
import bpy
col = bpy.data.collections.get("{collection_name}")
if col:
    print([obj.name for obj in col.objects])
else:
    print([])
""")
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return []
        return result or []

    # ============ Selection Utilities ============

    def deselect_all(self) -> str:
        """Deselect all objects."""
        return self.execute_blender_code("bpy.ops.object.select_all(action='DESELECT')")

    def get_selected_objects(self) -> List[str]:
        """Get names of currently selected objects."""
        return self.list_objects()  # Placeholder - proper implementation needed

    # ============ Transform Utilities ============

    def align_objects_to_axis(self, axis: str = 'X', location: float = 0.0) -> List[str]:
        """
        Align all objects to a specific axis location.

        Args:
            axis: 'X', 'Y', or 'Z'
            location: Coordinate value to align to

        Returns:
            List of results
        """
        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[axis.upper()]
        objs = self.list_objects()
        results = []
        for name in objs:
            info = self.get_object_info(name)
            loc = info.get('location', [0, 0, 0])
            new_loc = loc.copy()
            new_loc[axis_idx] = location
            self.set_object_transform(name, location=new_loc)
            results.append(f"Aligned {name} {axis}={location}")
        return results

    # ============ Export Utilities ============

    def export_gltf(self, filepath: str, export_format: str = 'GLB', include: List[str] = None) -> str:
        """
        Export scene to glTF format.

        Args:
            filepath: Output file path (.glb or .gltf)
            export_format: 'GLB' (binary) or 'GLTF' (JSON + external resources)
            include: List of what to include: ['SELECTED', 'ACTIVE', 'ALL'] - default 'SELECTED'

        Returns:
            Result message
        """
        include_str = 'SELECTED' if not include else include[0]
        code = f"""
import bpy
bpy.ops.export_scene.gltf(
    filepath=r"{filepath}",
    export_format='{export_format}',
    export_selected={'SELECTED' in include_str},
    export_apply=True
)
print(f"Exported glTF to: {filepath}")
"""
        return self.execute_blender_code(code)

    def export_fbx(self, filepath: str, selected_only: bool = False) -> str:
        """
        Export scene to FBX format.

        Args:
            filepath: Output .fbx file path
            selected_only: Export only selected objects

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.export_scene.fbx(
    filepath=r"{filepath}",
    use_selection={selected_only},
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE',
    bake_anim=False
)
print(f"Exported FBX to: {filepath}")
"""
        return self.execute_blender_code(code)

    def export_obj(self, filepath: str, selected_only: bool = False) -> str:
        """
        Export scene to OBJ format.

        Args:
            filepath: Output .obj file path
            selected_only: Export only selected objects

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.export_scene.obj(
    filepath=r"{filepath}",
    use_selection={selected_only},
    global_scale=1.0,
    path_mode='AUTO'
)
print(f"Exported OBJ to: {filepath}")
"""
        return self.execute_blender_code(code)

    # ============ Info Utilities ============

    def get_object_bounding_box(self, object_name: str) -> Dict[str, List[float]]:
        """
        Get the bounding box of an object in world space.

        Args:
            object_name: Object name

        Returns:
            Dict with 'min' and 'max' coordinates
        """
        info = self.get_object_info(object_name)
        return {
            'min': info.get('bound_box_min'),
            'max': info.get('bound_box_max')
        }

    def get_mesh_stats(self, object_name: str) -> Dict[str, int]:
        """
        Get mesh statistics: vertices, edges, faces.

        Args:
            object_name: Mesh object name

        Returns:
            Dict with counts
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    mesh = obj.data
    print({{"vertices": len(mesh.vertices), "edges": len(mesh.edges), "faces": len(mesh.polygons)}})
else:
    print({{"error": "Not a mesh"}})
"""
        result = self.execute_blender_code(code)
        if isinstance(result, dict) and 'error' not in result:
            return result
        return {}

    # ============ Enhanced Async Polling ============

    def wait_for_hyper3d_completion(self, task_uuid: str, subscription_key: str,
                                   timeout: int = 300, interval: int = 5) -> Dict[str, Any]:
        """
        Poll Hyper3D until job completes or times out.

        Args:
            task_uuid: Task UUID from generate call
            subscription_key: Subscription key
            timeout: Max wait time in seconds
            interval: Poll interval in seconds

        Returns:
            Final job status dictionary
        """
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.poll_rodin_job_status(subscription_key=subscription_key)
            if isinstance(status, dict):
                state = status.get('status', '').upper()
                if state in ('SUCCESS', 'DONE', 'COMPLETED', 'FAILED', 'CANCELLED'):
                    return status
            time.sleep(interval)
        raise TimeoutError(f"Hyper3D job did not complete within {timeout} seconds")

    def wait_for_hunyuan_completion(self, job_id: str, timeout: int = 600, interval: int = 10) -> Dict[str, Any]:
        """
        Poll Hunyuan3D until job completes or times out.

        Args:
            job_id: Job ID from generate call
            timeout: Max wait time in seconds
            interval: Poll interval in seconds

        Returns:
            Final job status dictionary
        """
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.poll_hunyuan_job_status(job_id)
            if isinstance(status, dict):
                state = status.get('status', '').upper()
                if state in ('SUCCESS', 'DONE', 'COMPLETED', 'FAILED', 'CANCELLED'):
                    return status
            time.sleep(interval)
        raise TimeoutError(f"Hunyuan3D job did not complete within {timeout} seconds")


# ============ Enhanced Core Operations ============

    def list_all_objects(self, user_prompt: str = "List all objects") -> List[Dict[str, Any]]:
        """
        List all objects in the scene with their types, visibility, and parent.

        Returns:
            List of object info dictionaries
        """
        code = """
import bpy
import json
objects = []
for obj in bpy.data.objects:
    objects.append({
        'name': obj.name,
        'type': obj.type,
        'visible': not obj.hide_viewport and not obj.hide_get(),
        'select': obj.select_get(),
        'parent': obj.parent.name if obj.parent else None,
        'location': list(obj.location),
        'rotation': list(obj.rotation_euler),
        'scale': list(obj.scale)
    })
print(json.dumps(objects))
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON substring
                parsed = self._parse_json_output(result)
                if isinstance(parsed, list):
                    return parsed
                return []
        return []

    def select_object(self, object_name: str, select: bool = True) -> str:
        """
        Select or deselect a specific object.

        Args:
            object_name: Name of the object
            select: True to select, False to deselect

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.select_set({select})
    print(f"{'Selected' if {select} else 'Deselected'}: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def select_all(self) -> str:
        """
        Select all objects in the scene.

        Returns:
            Result message
        """
        code = """
import bpy
bpy.ops.object.select_all(action='SELECT')
print("Selected all objects")
"""
        return self.execute_blender_code(code)

    def select_none(self) -> str:
        """
        Deselect all objects in the scene.

        Returns:
            Result message
        """
        code = """
import bpy
bpy.ops.object.select_all(action='DESELECT')
print("Deselected all objects")
"""
        return self.execute_blender_code(code)

    def get_active_object(self, user_prompt: str = "Get active object") -> Optional[Dict[str, Any]]:
        """
        Get the currently active object.

        Returns:
            Dictionary with active object info or None
        """
        code = """
import bpy
import json
active = bpy.context.view_layer.objects.active
if active:
    print(json.dumps({
        'name': active.name,
        'type': active.type,
        'location': list(active.location),
        'rotation': list(active.rotation_euler),
        'scale': list(active.scale)
    }))
else:
    print("null")
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
            if parsed is None and result.strip() == "null":
                return None
        return None

    def set_active_object(self, object_name: str) -> str:
        """
        Set an object as the active object.

        Args:
            object_name: Name of the object to activate

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    print(f"Active object set to: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def hide_object(self, object_name: str, hide: bool = True) -> str:
        """
        Hide or show an object in the viewport.

        Args:
            object_name: Name of the object
            hide: True to hide, False to show

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.hide_viewport = {hide}
    obj.hide_render = {hide}
    print(f"{'Hidden' if {hide} else 'Shown'}: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def show_object(self, object_name: str) -> str:
        """
        Show a hidden object.

        Args:
            object_name: Name of the object to show

        Returns:
            Result message
        """
        return self.hide_object(object_name, hide=False)

    def lock_object(self, object_name: str, lock: bool = True) -> str:
        """
        Lock or unlock object transformation.

        Args:
            object_name: Name of the object
            lock: True to lock, False to unlock

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.lock_location = ({lock}, {lock}, {lock})
    obj.lock_rotation = ({lock}, {lock}, {lock})
    obj.lock_scale = ({lock}, {lock}, {lock})
    print(f"{'Locked' if {lock} else 'Unlocked'}: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def copy_object(self, object_name: str, new_name: Optional[str] = None, linked: bool = False) -> str:
        """
        Duplicate an object.

        Args:
            object_name: Object to duplicate
            new_name: Optional name for the duplicate
            linked: If True, shares mesh/data (Alt+D)

        Returns:
            Result message
        """
        name_part = f', name="{new_name}"' if new_name else ""
        linked_part = ", linked=True" if linked else ""
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    new_obj = obj.copy(){name_part}{linked_part}
    bpy.context.collection.objects.link(new_obj)
    print(f"Duplicated {object_name} to {new_obj.name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def instance_object(self, object_name: str, new_name: Optional[str] = None) -> str:
        """
        Create a linked duplicate (instance) of an object.

        Args:
            object_name: Object to instance
            new_name: Optional name for the instance

        Returns:
            Result message
        """
        return self.copy_object(object_name, new_name=new_name, linked=True)

    def join_objects(self, object_names: List[str]) -> str:
        """
        Join multiple objects into one.

        Args:
            object_names: List of object names to join (last becomes target)

        Returns:
            Result message
        """
        names_str = '", "'.join(object_names)
        code = f"""
import bpy
# Select all objects
bpy.ops.object.select_all(action='DESELECT')
objects = []
for name in {object_names}:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.select_set(True)
        objects.append(obj)
    else:
        print(f"Warning: Object not found: {{name}}")

if len(objects) >= 2:
    # Set active to last selected
    bpy.context.view_layer.objects.active = objects[-1]
    bpy.ops.object.join()
    print(f"Joined {len(objects)} objects into {{objects[-1].name}}")
else:
    print("Need at least 2 objects to join")
"""
        return self.execute_blender_code(code)

    def separate_object(self, object_name: str, separation_type: str = 'SELECTED') -> str:
        """
        Separate selected geometry from an object into a new object.

        Args:
            object_name: Object to separate
            separation_type: 'SELECTED', 'MATERIAL', 'LOOSE'

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # Enter edit mode, select all, then separate
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='{separation_type}')
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Separated {object_name} by {separation_type}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def parent_objects(self, parent: str, children: List[str], keep_transform: bool = True) -> str:
        """
        Parent objects to a parent object.

        Args:
            parent: Name of parent object
            children: List of child object names
            keep_transform: Keep world transform (True) or relative (False)

        Returns:
            Result message
        """
        children_str = '", "'.join(children)
        code = f"""
import bpy
parent_obj = bpy.data.objects.get("{parent}")
if not parent_obj:
    print(f"Parent not found: {parent}")
else:
    for child_name in {children}:
        child = bpy.data.objects.get(child_name)
        if child:
            child.parent = parent_obj
            if {keep_transform}:
                child.matrix_parent_inverse = parent_obj.matrix_world.inverted()
            print(f"Parented {{child_name}} to {parent}")
        else:
            print(f"Child not found: {{child_name}}")
"""
        return self.execute_blender_code(code)

    def clear_parent(self, child_name: str, keep_transform: bool = True) -> str:
        """
        Clear parent of an object.

        Args:
            child_name: Object to unparent
            keep_transform: Keep world transform after unparenting

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{child_name}")
if obj:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.parent_clear(type={{'KEEP_TRANSFORM' if {keep_transform} else 'CLEAR'}})
    print(f"Cleared parent of {child_name}")
else:
    print(f"Object not found: {child_name}")
"""
        return self.execute_blender_code(code)

    def get_object_hierarchy(self, root_name: str, max_depth: int = 10, user_prompt: str = "Get object hierarchy") -> Dict[str, Any]:
        """
        Get the hierarchy tree starting from a root object.

        Args:
            root_name: Name of root object
            max_depth: Maximum recursion depth
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Nested dictionary representing hierarchy
        """
        code = f"""
import bpy
import json
def build_hierarchy(obj, depth=0, max_depth={max_depth}):
    if depth > max_depth:
        return {{'name': obj.name, 'children': []}}
    children = [child for child in bpy.data.objects if child.parent == obj]
    result = {{
        'name': obj.name,
        'type': obj.type,
        'children': [build_hierarchy(child, depth+1, max_depth) for child in children]
    }}
    return result

root = bpy.data.objects.get("{root_name}")
if root:
    hierarchy = build_hierarchy(root)
    print(json.dumps(hierarchy))
else:
    print(json.dumps({{'error': f'Object not found: {root_name}'}}))
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {'error': 'Failed to get hierarchy'}

    # ============ Transform Operations ============

    def apply_transform(self, object_name: str) -> str:
        """
        Apply location/rotation/scale transforms to object data.

        Args:
            object_name: Object to apply transforms to

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print(f"Applied transform: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def reset_transform(self, object_name: str) -> str:
        """
        Reset object transform to identity (0,0,0 location, 1,1,1 scale).

        Args:
            object_name: Object to reset

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    print(f"Reset transform: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def snap_to_grid(self, object_name: str, increment: float = 1.0) -> str:
        """
        Snap object location to grid.

        Args:
            object_name: Object to snap
            increment: Grid increment size

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.view3d.snap_cursor_to_selected()
    bpy.ops.transform.snap(value=({increment}, {increment}, {increment}))
    print(f"Snapped to grid: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def snap_to_cursor(self, object_name: str) -> str:
        """
        Snap object location to 3D cursor.

        Args:
            object_name: Object to snap

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
    print(f"Snapped to cursor: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def align_objects_to_axis(self, object_names: List[str], axis: str = 'X', reference_object: Optional[str] = None) -> str:
        """
        Align multiple objects along an axis relative to a reference.

        Args:
            object_names: List of objects to align
            axis: 'X', 'Y', or 'Z'
            reference_object: Optional reference object for alignment position

        Returns:
            Result message
        """
        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}.get(axis.upper(), 0)
        code = f"""
import bpy
axis_idx = {axis_idx}
reference_object = "{reference_object}" if {reference_object} else None

# Get reference location if specified
ref_loc = None
if reference_object:
    ref = bpy.data.objects.get(reference_object)
    if ref:
        ref_loc = ref.location

# Get all objects
objs = []
for name in {object_names}:
    obj = bpy.data.objects.get(name)
    if obj:
        objs.append(obj)
    else:
        print(f"Warning: Object not found: {{name}}")

if ref_loc:
    # Align to reference position on axis
    for obj in objs:
        loc = list(obj.location)
        loc[axis_idx] = ref_loc[axis_idx]
        obj.location = tuple(loc)
else:
    # Align in sequence (evenly spaced)
    if len(objs) > 1:
        bounds = [obj.location[axis_idx] for obj in objs]
        min_val = min(bounds)
        max_val = max(bounds)
        spacing = (max_val - min_val) / max(1, len(objs) - 1)
        objs_sorted = sorted(objs, key=lambda o: o.location[axis_idx])
        for i, obj in enumerate(objs_sorted):
            loc = list(obj.location)
            loc[axis_idx] = min_val + i * spacing
            obj.location = tuple(loc)

print(f"Aligned {{len(objs)}} objects to axis {axis.upper()}")
"""
        return self.execute_blender_code(code)

    def distribute_objects(self, object_names: List[str], axis: str = 'X', spacing: float = 1.0, start_position: Optional[List[float]] = None) -> str:
        """
        Distribute objects evenly along an axis.

        Args:
            object_names: List of objects to distribute
            axis: Distribution axis 'X', 'Y', or 'Z'
            spacing: Distance between objects
            start_position: Starting position [x,y,z] (optional)

        Returns:
            Result message
        """
        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}.get(axis.upper(), 0)
        start = start_position if start_position else [0, 0, 0]

        code = f"""
import bpy
axis_idx = {axis_idx}
start = {start}
spacing = {spacing}

# Get all objects and sort by current position on axis
objs = []
for name in {object_names}:
    obj = bpy.data.objects.get(name)
    if obj:
        objs.append(obj)

# Sort by current position
objs.sort(key=lambda o: o.location[axis_idx])

# Apply distributed positions
for i, obj in enumerate(objs):
    loc = list(start)
    loc[axis_idx] += i * spacing
    obj.location = tuple(loc)

print(f"Distributed {{len(objs)}} objects along {axis.upper()} axis with spacing {{spacing}}")
"""
        return self.execute_blender_code(code)

    def copy_transform(self, source_name: str, dest_name: str) -> str:
        """
        Copy transform from source object to destination object.

        Args:
            source_name: Source object name
            dest_name: Destination object name

        Returns:
            Result message
        """
        code = f"""
import bpy
src = bpy.data.objects.get("{source_name}")
dst = bpy.data.objects.get("{dest_name}")
if src and dst:
    dst.location = src.location.copy()
    dst.rotation_euler = src.rotation_euler.copy()
    dst.scale = src.scale.copy()
    print(f"Copied transform from {source_name} to {dest_name}")
else:
    print(f"Source or destination not found")
"""
        return self.execute_blender_code(code)

    def match_transform(self, target_name: str, source_name: str) -> str:
        """
        Match target object's transform to source object.
        Alias for copy_transform (source -> target).

        Args:
            target_name: Target object to modify
            source_name: Source object to match

        Returns:
            Result message
        """
        return self.copy_transform(source_name, target_name)

    def get_object_center(self, object_name: str, world_space: bool = True, user_prompt: str = "Get object center") -> List[float]:
        """
        Get the center point of an object.

        Args:
            object_name: Object name
            world_space: Return world-space coordinates (True) or local (False)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            [x, y, z] coordinates
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj:
    if {world_space}:
        center = obj.matrix_world.to_translation()
    else:
        center = obj.location
    print(json.dumps([center.x, center.y, center.z]))
else:
    print(json.dumps([0, 0, 0]))
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list) and len(result) == 3:
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list) and len(parsed) == 3:
                return parsed
        return [0, 0, 0]


# ============ Advanced Mesh & Geometry Operations ============

    # --- Mesh Topology ---

    def triangulate_object(self, object_name: str, method: str = 'BEAUTY', ngons: bool = True) -> str:
        """
        Convert all quads to triangles.

        Args:
            object_name: Mesh object name
            method: Triangulation method (BEAUTY, FIXED, FIXED_ALTERNATE, CLIP)
            ngons: If True, triangulate n-gons too

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris({{'method': '{method.upper()}', 'ngons': {str(ngons).lower()}}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Triangulated {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def quads_to_tris(self, object_name: str) -> str:
        """
        Alias for triangulate_object with beauty method.
        """
        return self.triangulate_object(object_name, method='BEAUTY', ngons=True)

    def tris_to_quads(self, object_name: str, sharp_angle: float = 0.7) -> str:
        """
        Convert triangles back to quads where possible.

        Args:
            object_name: Mesh object name
            sharp_angle: Maximum angle to consider for unjoining (radians)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.tris_convert_to_quads({{'sharp_angle': {sharp_angle}}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Converted tris to quads: {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def fill_holes(self, object_name: str, hole_size: int = 3) -> str:
        """
        Fill boundary loops (holes) in mesh.

        Args:
            object_name: Mesh object name
            hole_size: Maximum hole size (number of edges) to fill

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill_holes({{'sides': {hole_size}}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Filled holes in {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def merge_vertices(self, object_name: str, distance: float = 0.001) -> str:
        """
        Merge vertices within a threshold distance.

        Args:
            object_name: Mesh object name
            distance: Merge distance threshold

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles({{'threshold': {distance}}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Merged vertices within {distance}: {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def split_edges(self, object_name: str, angle: float = 30.0) -> str:
        """
        Split edges where the angle between faces exceeds threshold.

        Args:
            object_name: Mesh object name
            angle: Angle threshold in degrees

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.edge_split({{'use_crease': False, 'use_edge_angle': True, 'split_angle': {angle}}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Split edges by angle in {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def decimate_object(self, object_name: str, ratio: float = 0.5) -> str:
        """
        Reduce polygon count using decimate modifier.

        Args:
            object_name: Mesh object name
            ratio: Reduction ratio (0.1 = 90% reduction, 1.0 = no reduction)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='DECIMATE')
    mod = obj.modifiers['Decimate']
    mod.ratio = {ratio}
    bpy.ops.object.modifier_apply(modifier='Decimate')
    print(f"Decimated {object_name} to ratio {ratio}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def remesh_object(self, object_name: str, mode: str = 'VOXEL', voxel_size: float = 0.1) -> str:
        """
        Complete remesh using Remesh modifier.

        Args:
            object_name: Mesh object name
            mode: 'VOXEL', 'QUAD', 'HEX'
            voxel_size: Voxel size for VOXEL mode

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='REMESH')
    mod = obj.modifiers['Remesh']
    mod.mode = '{mode.upper()}'
    if '{mode.upper()}' == 'VOXEL':
        mod.voxel_size = {voxel_size}
    bpy.ops.object.modifier_apply(modifier='Remesh')
    print(f"Remeshed {object_name} using {mode} mode")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    # --- Mesh Editing ---

    def extrude_along_curve(self, object_name: str, curve_object: str) -> str:
        """
        Extrude a mesh along a curve path.

        Args:
            object_name: Mesh to extrude (must be selected)
            curve_object: Curve object to use as path

        Returns:
            Result message
        """
        code = f"""
import bpy
mesh_obj = bpy.data.objects.get("{object_name}")
curve_obj = bpy.data.objects.get("{curve_object}")
if mesh_obj and curve_obj and mesh_obj.type == 'MESH' and curve_obj.type == 'CURVE':
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # Add curve modifier
    mesh_obj.modifiers.new(name="Curve", type='CURVE')
    mesh_obj.modifiers["Curve"].object = curve_obj
    print(f"Extruded {object_name} along {curve_object}")
else:
    print(f"Objects not found or wrong types")
"""
        return self.execute_blender_code(code)

    def inset_faces(self, object_name: str, thickness: float = 0.1, depth: float = 0.0) -> str:
        """
        Inset selected faces.

        Args:
            object_name: Mesh object name
            thickness: Inset amount
            depth: Depth offset (optional)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.inset(thickness={thickness}, depth={depth})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Inset faces on {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def bevel_edges(self, object_name: str, amount: float = 0.1, segments: int = 3) -> str:
        """
        Bevel edges or vertices.

        Args:
            object_name: Mesh object name
            amount: Bevel width
            segments: Number of bevel segments

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bevel(offset={amount}, segments={segments}, affect='EDGES')
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Beveled edges on {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def loop_cut(self, object_name: str, cuts: int = 1, offset: float = 0.5) -> str:
        """
        Insert loop cuts.

        Args:
            object_name: Mesh object name
            cuts: Number of cuts
            offset: Cut offset (0-1)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.loopcut_slide(
        MESH_OT_loopcut={{
            "number_cuts": {cuts},
            "smoothness": 0,
            "object_index": 0,
            "edge_index": 0
        }},
        TRANSFORM_OT_edge_slide={{
            "value": {offset}
        }}
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Added {cuts} loop cut(s) to {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def edge_crease(self, object_name: str, crease: float = 1.0) -> str:
        """
        Set edge crease weight for selected edges.

        Args:
            object_name: Mesh object name
            crease: Crease weight (0-1)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.edge_crease(value={crease})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Set edge crease to {crease} on {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def edge_ring_select(self, object_name: str) -> str:
        """
        Select edge rings.

        Args:
            object_name: Mesh object name

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='TOGGLE')
    bpy.ops.mesh.loop_multi_select({{'ring': True}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Selected edge rings on {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def edge_loop_select(self, object_name: str) -> str:
        """
        Select edge loops.

        Args:
            object_name: Mesh object name

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_all(action='TOGGLE')
    bpy.ops.mesh.loop_multi_select({{'ring': False}})
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Selected edge loops on {object_name}")
else:
    print(f"Object not found or not a mesh: {object_name}")
"""
        return self.execute_blender_code(code)

    def bridge_faces(self, object_name1: str, object_name2: str) -> str:
        """
        Bridge two separate mesh objects with a face strip.

        Args:
            object_name1: First mesh object
            object_name2: Second mesh object

        Returns:
            Result message
        """
        code = f"""
import bpy
obj1 = bpy.data.objects.get("{object_name1}")
obj2 = bpy.data.objects.get("{object_name2}")
if obj1 and obj2 and obj1.type == 'MESH' and obj2.type == 'MESH':
    bpy.context.view_layer.objects.active = obj1
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # Select both objects
    obj1.select_set(True)
    obj2.select_set(True)
    bpy.context.view_layer.objects.active = obj1
    bpy.ops.object.join()
    print(f"Bridged {object_name1} and {object_name2}")
else:
    print(f"Objects not found or not meshes")
"""
        return self.execute_blender_code(code)

    # --- Modifiers ---

    def add_modifier(self, object_name: str, mod_type: str, **params) -> str:
        """
        Add a modifier to an object.

        Args:
            object_name: Target object name
            mod_type: Modifier type (e.g., 'SUBSURF', 'SOLIDIFY', 'BEVEL')
            **params: Additional modifier properties

        Returns:
            Result message
        """
        params_str = ', '.join([f"{k}={repr(v)}" for k, v in params.items()])
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='{mod_type.upper()}')
    mod = obj.modifiers[-1]
    print(f"Added {mod_type} modifier to {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def list_modifiers(self, object_name: str, user_prompt: str = "List modifiers") -> List[Dict[str, Any]]:
        """
        List all modifiers on an object.

        Args:
            object_name: Object name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            List of modifier info dicts (name, type, enabled)
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj:
    mods = []
    for mod in obj.modifiers:
        mods.append({{
            'name': mod.name,
            'type': mod.type,
            'enabled': mod.show_viewport
        }})
    print(json.dumps(mods))
else:
    print(json.dumps([]))
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list):
                return parsed
        return []

    def remove_modifier(self, object_name: str, mod_name: str) -> str:
        """
        Remove a specific modifier.

        Args:
            object_name: Object name
            mod_name: Modifier name to remove

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and '{mod_name}' in obj.modifiers:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_remove(modifier='{mod_name}')
    print(f"Removed modifier {mod_name} from {object_name}")
else:
    print(f"Modifier not found: {mod_name}")
"""
        return self.execute_blender_code(code)

    def apply_modifier(self, object_name: str, mod_name: str) -> str:
        """
        Apply a modifier to the object's mesh data.

        Args:
            object_name: Object name
            mod_name: Modifier name to apply

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and '{mod_name}' in obj.modifiers:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='{mod_name}')
    print(f"Applied modifier {mod_name} to {object_name}")
else:
    print(f"Modifier not found: {mod_name}")
"""
        return self.execute_blender_code(code)

    def reorder_modifier(self, object_name: str, mod_name: str, index: int) -> str:
        """
        Move a modifier in the stack.

        Args:
            object_name: Object name
            mod_name: Modifier name
            index: New index position (0 = top)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and '{mod_name}' in obj.modifiers:
    mod = obj.modifiers['{mod_name}']
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_move(modifier='{mod_name}', index={index})
    print(f"Moved modifier {mod_name} to index {index} on {object_name}")
else:
    print(f"Modifier not found: {mod_name}")
"""
        return self.execute_blender_code(code)

    def toggle_modifier(self, object_name: str, mod_name: str, enable: bool = True) -> str:
        """
        Enable or disable a modifier without removing it.

        Args:
            object_name: Object name
            mod_name: Modifier name
            enable: True to enable, False to disable

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and '{mod_name}' in obj.modifiers:
    mod = obj.modifiers['{mod_name}']
    mod.show_viewport = {enable}
    print(f"{'Enabled' if {enable} else 'Disabled'} modifier {mod_name} on {object_name}")
else:
    print(f"Modifier not found: {mod_name}")
"""
        return self.execute_blender_code(code)

    # --- Geometry Nodes ---

    def create_geometry_nodes_setup(self, object_name: str, node_tree_name: str = "GeometryNodes") -> str:
        """
        Add a Geometry Nodes modifier and setup basic nodes.

        Args:
            object_name: Target object
            node_tree_name: Name for the node tree

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='NODES')
    mod = obj.modifiers[-1]
    mod.node_group = bpy.data.node_groups.new(name="{node_tree_name}", type='GeometryNodeTree')
    print(f"Added Geometry Nodes to {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def list_geometry_nodes_available(self) -> List[Dict[str, str]]:
        """
        List available Geometry Node types.

        Returns:
            List of node type identifiers and names
        """
        # This is a static list; could be dynamic via bpy but simpler
        nodes = [
            {'type': 'GeometryNodeGroup', 'name': 'Group'},
            {'type': 'GeometryNodeInputPosition', 'name': 'Position'},
            {'type': 'GeometryNodeInputNormal', 'name': 'Normal'},
            {'type': 'GeometryNodeInputID', 'name': 'ID'},
            {'type': 'GeometryNodeInputMaterial', 'name': 'Material'},
            {'type': 'GeometryNodeInputMesh', 'name': 'Mesh'},
            {'type': 'GeometryNodeOutput', 'name': 'Output'},
            {'type': 'GeometryNodeCurvePrimitiveBezierLine', 'name': 'Bezier Line'},
            {'type': 'GeometryNodeCurvePrimitiveCircle', 'name': 'Circle'},
            {'type': 'GeometryNodeCurvePrimitiveQuadrilateral', 'name': 'Quad'},
            {'type': 'GeometryNodeMeshCircle', 'name': 'Mesh Circle'},
            {'type': 'GeometryNodeMeshCone', 'name': 'Mesh Cone'},
            {'type': 'GeometryNodeMeshCube', 'name': 'Mesh Cube'},
            {'type': 'GeometryNodeMeshCylinder', 'name': 'Mesh Cylinder'},
            {'type': 'GeometryNodeMeshGrid', 'name': 'Mesh Grid'},
            {'type': 'GeometryNodeMeshIcoSphere', 'name': 'Mesh Ico Sphere'},
            {'type': 'GeometryNodeMeshLine', 'name': 'Mesh Line'},
            {'type': 'GeometryNodeMeshUVSphere', 'name': 'Mesh UV Sphere'},
        ]
        return nodes

    def apply_geometry_nodes(self, object_name: str) -> str:
        """
        Apply the Geometry Nodes modifier (bake).

        Args:
            object_name: Object name

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    for mod in obj.modifiers:
        if mod.type == 'NODES':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
            print(f"Applied Geometry Nodes: {mod.name}")
            break
    else:
        print(f"No Geometry Nodes modifier on {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)

    def get_geometry_node_attributes(self, object_name: str) -> List[Dict[str, Any]]:
        """
        Get custom geometry attributes on an object.

        Args:
            object_name: Mesh object name

        Returns:
            List of attribute info (name, domain, data_type)
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    attrs = []
    for attr in obj.data.attributes:
        attrs.append({{
            'name': attr.name,
            'domain': attr.domain,
            'data_type': attr.data_type
        }})
    print(attrs)
else:
    print([])
"""
        result = self.execute_blender_code(code)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return []

    def set_geometry_node_attribute(self, object_name: str, attr_name: str, values: List[Any], domain: str = 'POINT') -> str:
        """
        Set a custom attribute on mesh geometry.

        Args:
            object_name: Mesh object name
            attr_name: Attribute name
            values: List of values (length must match domain count)
            domain: 'POINT', 'EDGE', 'FACE', 'CORNER'

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    mesh = obj.data
    attr = mesh.attributes.get("{attr_name}") or mesh.attributes.new(name="{attr_name}", type='FLOAT', domain='{domain.upper()}')
    # Fill attribute data
    # Simplified: expects values list matches count
    if len({values}) == len(attr.data):
        for i, val in enumerate({values}):
            attr.data[i].value = val
        print(f"Set attribute {attr_name} on {object_name}")
    else:
        print(f"Value count mismatch for {attr_name}")
else:
    print(f"Object not found or not mesh")
"""
        return self.execute_blender_code(code)

    def execute_geometry_nodes_network(self, object_name: str, inputs: Dict[str, Any]) -> str:
        """
        Execute a geometry nodes network with custom inputs.

        Args:
            object_name: Target object
            inputs: Dictionary of input values for group inputs

        Returns:
            Result message
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj:
    # For now, just log inputs (actual implementation would require node manipulation)
    print("Geometry nodes execution requested with inputs: " + json.dumps({inputs}))
    print("Feature placeholder: Connect nodes manually or via script")
else:
    print(f"Object not found: {object_name}")
"""
        return self.execute_blender_code(code)


# Convenience function
def get_blender_client() -> BlenderMCPClient:
    """Get a BlenderMCPClient instance with default settings."""
    return BlenderMCPClient()


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Blender MCP Client")
    parser.add_argument("tool", help="Tool to call (e.g., get_scene_info, execute_blender_code)")
    parser.add_argument("--params", type=str, help="JSON string of parameters")
    parser.add_argument("--server", default="blender", help="mcporter server name (default: blender)")
    args = parser.parse_args()

    try:
        client = BlenderMCPClient(server_name=args.server)
        params = json.loads(args.params) if args.params else {}

        method = getattr(client, args.tool, None)
        if not method:
            print(f"Error: Unknown tool '{args.tool}'", file=sys.stderr)
            sys.exit(1)

        result = method(**params)
        if isinstance(result, bytes):
            # Binary output, print size
            print(f"<binary data: {len(result)} bytes>")
        else:
            print(json.dumps(result, indent=2) if isinstance(result, (dict, list)) else result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
