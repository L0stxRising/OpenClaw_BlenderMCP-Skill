"""
Blender MCP Asset Management & I/O Client

Extends BlenderMCPClient with:
- Import/Export for common formats (OBJ, FBX, GLTF, STL, USD, Alembic, PLY)
- Asset library integration
- Batch operations for multiple files/objects
"""

from blender_mcp_client import BlenderMCPClient
import json
from typing import Any, Dict, List, Optional, Union


class BlenderMCPAssetsClient(BlenderMCPClient):
    """
    Asset management client adding import, export, batch, and asset library tools.
    """

    # --- Import Operations ---

    def import_obj(self, filepath: str, name: Optional[str] = None, use_smooth_groups: bool = True,
                  use_split_objects: bool = True, use_split_groups: bool = True,
                  global_scale: float = 1.0, axis_forward: str = '-Z', axis_up: str = 'Y',
                  user_prompt: str = "Import OBJ") -> str:
        """
        Import a Wavefront .obj file.

        Args:
            filepath: Path to .obj file
            name: Object name (defaults to file stem)
            use_smooth_groups: Use smooth groups
            use_split_objects: Split by object
            use_split_groups: Split by group
            global_scale: Scale factor
            axis_forward: Forward axis ('Z', '-Z', 'Y', '-Y', 'X', '-X')
            axis_up: Up axis ('Z', '-Z', 'Y', '-Y', 'X', '-X')
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
import os
bpy.ops.import_scene.obj(
    filepath="{filepath}",
    name="{name or ''}",
    use_smooth_groups={str(use_smooth_groups).lower()},
    use_split_objects={str(use_split_objects).lower()},
    use_split_groups={str(use_split_groups).lower()},
    global_scale={global_scale},
    axis_forward='{axis_forward}',
    axis_up='{axis_up}'
)
print(f"Imported OBJ: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def import_fbx(self, filepath: str, automatic_bone_orientation: bool = True,
                  global_scale: float = 1.0, axis_forward: str = '-Z', axis_up: str = 'Y',
                  use_image_search: bool = True, user_prompt: str = "Import FBX") -> str:
        """
        Import an FBX file.

        Args:
            filepath: Path to .fbx file
            automatic_bone_orientation: Auto-orient bones
            global_scale: Scale factor
            axis_forward: Forward axis
            axis_up: Up axis
            use_image_search: Search for textures
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.import_scene.fbx(
    filepath="{filepath}",
    automatic_bone_orientation={str(automatic_bone_orientation).lower()},
    global_scale={global_scale},
    axis_forward='{axis_forward}',
    axis_up='{axis_up}',
    use_image_search={str(use_image_search).lower()}
)
print(f"Imported FBX: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def import_glb_gltf(self, filepath: str, filter_glob: str = "*.glb;*.gltf",
                       import_pack_images: bool = True, import_shading: str = 'NORMALS',
                       user_prompt: str = "Import GLTF") -> str:
        """
        Import a glTF/glB file.

        Args:
            filepath: Path to .gltf or .glb
            filter_glob: File filter
            import_pack_images: Pack imported images
            import_shading: 'NORMALS', 'FLAT', 'SMOOTH'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.import_scene.gltf(
    filepath="{filepath}",
    filter_glob='{filter_glob}',
    import_pack_images={str(import_pack_images).lower()},
    import_shading='{import_shading.upper()}'
)
print(f"Imported glTF: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def import_stl(self, filepath: str, global_scale: float = 1.0, use_scene_unit: bool = True,
                  user_prompt: str = "Import STL") -> str:
        """
        Import an STL file.

        Args:
            filepath: Path to .stl file
            global_scale: Scale factor
            use_scene_unit: Use scene unit scale
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.import_mesh.stl(
    filepath="{filepath}",
    global_scale={global_scale},
    use_scene_unit={str(use_scene_unit).lower()}
)
print(f"Imported STL: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def import_usd(self, filepath: str, import_visible_only: bool = False,
                  import_all_materials: bool = True, user_prompt: str = "Import USD") -> str:
        """
        Import a USD file.

        Args:
            filepath: Path to .usd/.usdc/.usda
            import_visible_only: Only import visible objects
            import_all_materials: Import all materials
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.wm.usd_import(
    filepath="{filepath}",
    import_visible_only={str(import_visible_only).lower()},
    import_all_materials={str(import_all_materials).lower()}
)
print(f"Imported USD: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def import_abc(self, filepath: str, use_frame_range: bool = False, start_frame: int = 1,
                  end_frame: int = 250, user_prompt: str = "Import ABC") -> str:
        """
        Import Alembic cache.

        Args:
            filepath: Path to .abc file
            use_frame_range: Use custom frame range
            start_frame: Start frame
            end_frame: End frame
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.wm.alembic_import(
    filepath="{filepath}",
    use_frame_range={str(use_frame_range).lower()},
    start_frame={start_frame},
    end_frame={end_frame}
)
print(f"Imported Alembic: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def import_ply(self, filepath: str, user_prompt: str = "Import PLY") -> str:
        """
        Import a PLY point cloud or mesh.

        Args:
            filepath: Path to .ply file
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.import_mesh.ply(filepath="{filepath}")
print(f"Imported PLY: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def import_3ds(self, filepath: str, global_scale: float = 1.0,
                  use_image_search: bool = True, user_prompt: str = "Import 3DS") -> str:
        """
        Import legacy 3DS file.

        Args:
            filepath: Path to .3ds file
            global_scale: Scale factor
            use_image_search: Search for textures
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.import_scene.max3d(
    filepath="{filepath}",
    global_scale={global_scale},
    use_image_search={str(use_image_search).lower()}
)
print(f"Imported 3DS: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def preview_import(self, filepath: str, format: str) -> Dict[str, Any]:
        """
        Quick preview of a file before import (lightweight check of contents).

        Args:
            filepath: Path to file
            format: Format hint (e.g., 'OBJ', 'FBX', 'GLTF')

        Returns:
            Dictionary with preview info (object count, bounds, etc.)
        """
        # Simplified: just check file size and extension
        code = f"""
import bpy, os, json
stat = os.stat("{filepath}")
info = {{
    'filepath': '{filepath}',
    'size_bytes': stat.st_size,
    'format': '{format}',
    'exists': True
}}
print(json.dumps(info))
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt="preview_import")
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}

    # --- Export Operations ---

    def export_obj(self, filepath: str, selected_only: bool = False, apply_modifiers: bool = True,
                  global_scale: float = 1.0, axis_forward: str = '-Z', axis_up: str = 'Y',
                  user_prompt: str = "Export OBJ") -> str:
        """
        Export selection to Wavefront .obj.

        Args:
            filepath: Output .obj file
            selected_only: Export only selected objects
            apply_modifiers: Apply modifiers
            global_scale: Scale factor
            axis_forward: Forward axis
            axis_up: Up axis
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.export_scene.obj(
    filepath="{filepath}",
    use_selection={str(selected_only).lower()},
    use_mesh_modifiers={str(apply_modifiers).lower()},
    global_scale={global_scale},
    axis_forward='{axis_forward}',
    axis_up='{axis_up}'
)
print(f"Exported OBJ: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def export_fbx(self, filepath: str, selected_only: bool = False, apply_modifiers: bool = True,
                  global_scale: float = 1.0, axis_forward: str = '-Z', axis_up: str = 'Y',
                  use_mesh_modifiers: bool = True, user_prompt: str = "Export FBX") -> str:
        """
        Export selection to FBX.

        Args:
            filepath: Output .fbx file
            selected_only: Export only selected
            apply_modifiers: Apply modifiers
            global_scale: Scale factor
            axis_forward, axis_up: Coordinate system
            use_mesh_modifiers: Apply mesh modifiers
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.export_scene.fbx(
    filepath="{filepath}",
    use_selection={str(selected_only).lower()},
    use_mesh_modifiers={str(use_mesh_modifiers).lower()},
    global_scale={global_scale},
    axis_forward='{axis_forward}',
    axis_up='{axis_up}'
)
print(f"Exported FBX: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def export_glb_gltf(self, filepath: str, format: str = 'GLB', selected_only: bool = False,
                       export_format: str = 'GLB', user_prompt: str = "Export glTF") -> str:
        """
        Export to glTF/glB.

        Args:
            filepath: Output .glb or .gltf
            format: 'GLB' (binary) or 'GLTF' (JSON + external)
            selected_only: Export only selected
            export_format: Alias for format (for compatibility)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.export_scene.gltf(
    filepath="{filepath}",
    export_format='{format.upper()}',
    use_selection={str(selected_only).lower()}
)
print(f"Exported {format}: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def export_stl(self, filepath: str, selected_only: bool = False, ascii: bool = False,
                  global_scale: float = 1.0, use_mesh_modifiers: bool = True,
                  user_prompt: str = "Export STL") -> str:
        """
        Export to STL.

        Args:
            filepath: Output .stl file
            selected_only: Export only selected
            ascii: Export as ASCII (vs binary)
            global_scale: Scale factor
            use_mesh_modifiers: Apply modifiers
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.export_mesh.stl(
    filepath="{filepath}",
    use_selection={str(selected_only).lower()},
    ascii={str(ascii).lower()},
    global_scale={global_scale},
    use_mesh_modifiers={str(use_mesh_modifiers).lower()}
)
print(f"Exported STL: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def export_usd(self, filepath: str, selected_only: bool = False, export_format: str = 'USD',
                  user_prompt: str = "Export USD") -> str:
        """
        Export to USD.

        Args:
            filepath: Output .usd/.usdc/.usda
            selected_only: Export only selected objects
            export_format: 'USD', 'USDC', 'USDA'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.wm.usd_export(
    filepath="{filepath}",
    selected={str(selected_only).lower()},
    export_format='{export_format.upper()}'
)
print(f"Exported USD: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def export_abc(self, filepath: str, start_frame: int = 1, end_frame: int = 250,
                  global_scale: float = 1.0, selected_only: bool = False,
                  user_prompt: str = "Export ABC") -> str:
        """
        Export Alembic cache.

        Args:
            filepath: Output .abc file
            start_frame: Start frame
            end_frame: End frame
            global_scale: Scale factor
            selected_only: Export selected only
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.wm.alembic_export(
    filepath="{filepath}",
    start={start_frame},
    end={end_frame},
    global_scale={global_scale},
    selected={str(selected_only).lower()}
)
print(f"Exported Alembic: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def export_ply(self, filepath: str, selected_only: bool = False, ascii: bool = False,
                  user_prompt: str = "Export PLY") -> str:
        """
        Export to PLY.

        Args:
            filepath: Output .ply file
            selected_only: Export selected
            ascii: ASCII (vs binary)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.ops.export_mesh.ply(
    filepath="{filepath}",
    use_selection={str(selected_only).lower()},
    ascii={str(ascii).lower()}
)
print(f"Exported PLY: {filepath}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def export_three_js(self, filepath: str, user_prompt: str = "Export Three.js") -> str:
        """
        Export scene in Three.js JSON format (legacy).

        Args:
            filepath: Output .js file
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
# Three.js exporter is usually an addon; call if available
try:
    bpy.ops.export_three.js(filepath="{filepath}")
    print(f"Exported Three.js: {filepath}")
except AttributeError:
    print("Three.js exporter not available (addon missing)")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Asset Library Integration ---

    def list_asset_libraries(self, user_prompt: str = "List asset libraries") -> List[Dict[str, str]]:
        """
        List all configured asset libraries.

        Returns:
            List of library info (name, path)
        """
        code = f"""
import bpy
import json
libraries = []
for lib in bpy.context.preferences.filepaths.asset_libraries:
    libraries.append({{'name': lib.name, 'path': lib.path}})
print(json.dumps(libraries))
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list):
                return parsed
        return []

    def import_from_library(self, library_name: str, asset_name: str, target_collection: Optional[str] = None,
                           user_prompt: str = "Import from library") -> str:
        """
        Import an asset from an asset library into the current scene.

        Args:
            library_name: Asset library name (as configured)
            asset_name: Asset identifier
            target_collection: Optional collection to place asset in
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
# Find library
lib = None
for l in bpy.context.preferences.filepaths.asset_libraries:
    if l.name == "{library_name}":
        lib = l
        break
if lib:
    # Look up asset in library (simplified)
    # Full implementation would use bpy.ops.asset.library_refresh() and asset catalogs
    print(f"Importing asset '{asset_name}' from library '{library_name}' (placeholder)")
    # Actual import would use:bpy.ops.asset.activate_asset(...)
else:
    print(f"Library not found: {library_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def publish_to_library(self, object_name: str, library_name: str, catalog: Optional[str] = None,
                          user_prompt: str = "Publish to library") -> str:
        """
        Publish an object as an asset to a library.

        Args:
            object_name: Object to publish
            library_name: Target asset library
            catalog: Optional catalog name
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    # Mark as asset
    obj.asset_mark()
    if "{catalog}":
        obj.asset_data.catalog = "{catalog}"
    # Save to library path would require write access
    print(f"Marked {object_name} as asset for library {library_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def create_asset_preview(self, object_name: str, filepath: str, user_prompt: str = "Create asset preview") -> str:
        """
        Generate a thumbnail preview render for an asset.

        Args:
            object_name: Object to preview
            filepath: Output image filepath (PNG)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
# Simplified: just render the object with a simple lighting setup
print(f"Asset preview generation placeholder - would render {object_name} to {filepath}")
# Actual implementation would set up a preview scene and render
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def mark_as_asset(self, object_name: str, catalog: str = '', user_prompt: str = "Mark as asset") -> str:
        """
        Mark a data-block as an asset.

        Args:
            object_name: Object name
            catalog: Optional catalog name
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.asset_mark()
    if "{catalog}":
        obj.asset_data.catalog = "{catalog}"
    print(f"Marked {object_name} as asset")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def unmark_asset(self, object_name: str, user_prompt: str = "Unmark asset") -> str:
        """
        Remove asset flag from an object.

        Args:
            object_name: Object name
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.asset_clear()
    print(f"Unmarked asset: {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def list_assets_in_library(self, library_name: str, catalog: str = '') -> List[Dict[str, str]]:
        """
        List assets in a library/catalog.

        Args:
            library_name: Library name
            catalog: Optional catalog filter
            user_prompt: For telemetry

        Returns:
            List of asset info (name, type, catalog)
        """
        code = f"""
import bpy
assets = []
# Placeholder: real implementation would iterate library's asset catalog
print(assets)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt if user_prompt else "list_assets_in_library")
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list):
                return parsed
        return []

    def search_assets(self, query: str, libraries: Optional[List[str]] = None,
                    user_prompt: str = "Search assets") -> List[Dict[str, str]]:
        """
        Search for assets by name/description across libraries.

        Args:
            query: Search string
            libraries: Optional list of library names to restrict search
            user_prompt: For telemetry

        Returns:
            List of matching assets
        """
        code = f"""
import bpy
query = "{query}".lower()
results = []
# Search current file's assets as fallback
for obj in bpy.data.objects:
    if obj.asset_data and query in obj.name.lower():
        results.append({{'name': obj.name, 'type': obj.type, 'library': 'Current File'}})
print(results)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, list):
                return parsed
        return []

    # --- Batch Operations ---

    def batch_import(self, filepaths: List[str], format: str, **kwargs) -> List[str]:
        """
        Import multiple files.

        Args:
            filepaths: List of file paths
            format: Format hint (e.g., 'OBJ', 'FBX', 'GLTF')
            **kwargs: Additional arguments passed to importer

        Returns:
            List of result messages
        """
        results = []
        for fp in filepaths:
            try:
                if format.upper() == 'OBJ':
                    res = self.import_obj(fp, **kwargs)
                elif format.upper() == 'FBX':
                    res = self.import_fbx(fp, **kwargs)
                elif format.upper() in ('GLB', 'GLTF'):
                    res = self.import_glb_gltf(fp, **kwargs)
                elif format.upper() == 'STL':
                    res = self.import_stl(fp, **kwargs)
                elif format.upper() == 'USD':
                    res = self.import_usd(fp, **kwargs)
                elif format.upper() == 'ABC':
                    res = self.import_abc(fp, **kwargs)
                elif format.upper() == 'PLY':
                    res = self.import_ply(fp, **kwargs)
                else:
                    res = f"Unsupported format: {format}"
                results.append(res)
            except Exception as e:
                results.append(f"Error importing {fp}: {e}")
        return results

    def batch_export(self, object_names: List[str], filepath_pattern: str, format: str,
                    base_dir: str = '.', **kwargs) -> List[str]:
        """
        Export multiple objects to files.

        Args:
            object_names: List of object names to export
            filepath_pattern: Pattern with {name} placeholder, e.g., "/exports/{name}.obj"
            format: Export format ('OBJ', 'FBX', 'GLB', 'STL', etc.)
            base_dir: Base directory for relative paths
            **kwargs: Additional export arguments

        Returns:
            List of result messages
        """
        results = []
        for name in object_names:
            filepath = filepath_pattern.format(name=name)
            if not os.path.isabs(filepath):
                filepath = os.path.join(base_dir, filepath)
            try:
                if format.upper() == 'OBJ':
                    res = self.export_obj(filepath, selected_only=True, **kwargs)
                elif format.upper() == 'FBX':
                    res = self.export_fbx(filepath, selected_only=True, **kwargs)
                elif format.upper() in ('GLB', 'GLTF'):
                    res = self.export_glb_gltf(filepath, selected_only=True, format=format, **kwargs)
                elif format.upper() == 'STL':
                    res = self.export_stl(filepath, selected_only=True, **kwargs)
                else:
                    res = f"Unsupported format: {format}"
                results.append(res)
            except Exception as e:
                results.append(f"Error exporting {name}: {e}")
        return results

    def batch_material_assign(self, object_names: List[str], material_name: str,
                             user_prompt: str = "Batch assign material") -> List[str]:
        """
        Assign the same material to multiple objects.

        Args:
            object_names: List of object names
            material_name: Material to assign
            user_prompt: For telemetry

        Returns:
            List of result strings
        """
        results = []
        for obj_name in object_names:
            try:
                res = self.assign_material(obj_name, material_name)
                results.append(f"{obj_name}: {res}")
            except Exception as e:
                results.append(f"{obj_name}: Error - {e}")
        return results

    def batch_set_parent(self, children: List[str], parent: str, keep_transform: bool = True,
                        user_prompt: str = "Batch parent") -> List[str]:
        """
        Parent multiple children to one parent object.

        Args:
            children: List of child object names
            parent: Parent object name
            keep_transform: Keep world transform
            user_prompt: For telemetry

        Returns:
            List of result strings
        """
        results = []
        for child in children:
            try:
                res = self.parent_objects(parent, [child], keep_transform=keep_transform)
                results.append(f"{child}: {res}")
            except Exception as e:
                results.append(f"{child}: Error - {e}")
        return results

    def batch_delete(self, object_names: List[str], user_prompt: str = "Batch delete") -> List[str]:
        """
        Delete multiple objects efficiently.

        Args:
            object_names: List of object names to delete
            user_prompt: For telemetry

        Returns:
            List of result strings
        """
        results = []
        for name in object_names:
            try:
                res = self.delete_object(name)
                results.append(f"{name}: {res}")
            except Exception as e:
                results.append(f"{name}: Error - {e}")
        return results

    def batch_duplicate(self, object_names: List[str], count: int = 2, offset: List[float] = (0,0,0),
                       user_prompt: str = "Batch duplicate") -> List[str]:
        """
        Duplicate multiple objects with offset.

        Args:
            object_names: List of object names to duplicate
            count: Number of copies
            offset: Offset per copy [dx, dy, dz]
            user_prompt: For telemetry

        Returns:
            List of result strings
        """
        results = []
        for name in object_names:
            try:
                # Create copies sequentially
                for i in range(count):
                    new_name = f"{name}_{i+1}"
                    res = self.copy_object(name, new_name=new_name)
                    if offset != (0,0,0):
                        self.set_object_transform(new_name, location=offset)  # simplified
                results.append(f"{name}: duplicated {count} times")
            except Exception as e:
                results.append(f"{name}: Error - {e}")
        return results


# Convenience function
def get_assets_client() -> BlenderMCPAssetsClient:
    """Get a BlenderMCPAssetsClient instance with default settings."""
    return BlenderMCPAssetsClient()


if __name__ == "__main__":
    import argparse, os
    parser = argparse.ArgumentParser(description="Blender MCP Assets Client")
    parser.add_argument("tool", help="Tool to call")
    parser.add_argument("--params", type=str, help="JSON string of parameters")
    parser.add_argument("--server", default="blender", help="mcporter server name")
    args = parser.parse_args()

    try:
        client = get_assets_client()
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
