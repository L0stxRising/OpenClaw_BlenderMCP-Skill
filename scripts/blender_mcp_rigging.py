"""
Blender MCP Rigging Client

Extends BlenderMCPClient with armatures, bones, constraints, skinning, and shape keys.
"""

from blender_mcp_client import BlenderMCPClient
import json
from typing import Any, Dict, List, Optional


class BlenderMCPRiggingClient(BlenderMCPClient):
    """
    Rigging-focused client extending BlenderMCPClient.

    Adds armature creation, bone editing, constraints, vertex groups/weights, and shape keys.
    """

    # --- Armatures & Bones ---

    def create_armature(self, name: str, display_type: str = 'WIRE', user_prompt: str = "Create armature") -> str:
        """
        Create a new armature object.

        Args:
            name: Armature object name
            display_type: Display type ('WIRE', 'SOLID', 'ENVELOPE')
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
armature = bpy.data.armatures.new(name="{name}")
obj = bpy.data.objects.new("{name}", armature)
obj.data.display_type = '{display_type.upper()}'
bpy.context.collection.objects.link(obj)
print(f"Created armature: {name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def add_armature_bone(self, armature_name: str, bone_name: str, head: Optional[List[float]] = None, tail: Optional[List[float]] = None, user_prompt: str = "Add bone") -> str:
        """
        Add a bone to an armature.

        Args:
            armature_name: Armature object name
            bone_name: Name for the new bone
            head: [x, y, z] head location (optional; defaults to 0,0,0)
            tail: [x, y, z] tail location (optional; defaults to (0,0,1) relative to armature)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        head_str = f"[{head[0]}, {head[1]}, {head[2]}]" if head else "[0.0, 0.0, 0.0]"
        tail_str = f"[{tail[0]}, {tail[1]}, {tail[2]}]" if tail else "[0.0, 0.0, 1.0]"
        code = f"""
import bpy
arm_obj = bpy.data.objects.get("{armature_name}")
if arm_obj and arm_obj.type == 'ARMATURE':
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bone = arm_obj.data.edit_bones.new("{bone_name}")
    bone.head = {head_str}
    bone.tail = {tail_str}
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Added bone {bone_name} to {armature_name}")
else:
    print(f"Armature not found: {armature_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def edit_bone_transform(self, armature_name: str, bone_name: str, head: Optional[List[float]] = None, tail: Optional[List[float]] = None, roll: Optional[float] = None, user_prompt: str = "Edit bone transform") -> str:
        """
        Edit an existing bone's transform in Edit mode.

        Args:
            armature_name: Armature object name
            bone_name: Bone name
            head: New head location [x,y,z]
            tail: New tail location [x,y,z]
            roll: New roll angle (radians)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        head_part = f"bone.head = [{head[0]}, {head[1]}, {head[2]}];\n" if head else ""
        tail_part = f"bone.tail = [{tail[0]}, {tail[1]}, {tail[2]}];\n" if tail else ""
        roll_part = f"bone.roll = {roll};\n" if roll is not None else ""
        code = f"""
import bpy
arm_obj = bpy.data.objects.get("{armature_name}")
if arm_obj and arm_obj.type == 'ARMATURE':
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bone = arm_obj.data.edit_bones.get("{bone_name}")
    if bone:
        {head_part}{tail_part}{roll_part}
        print(f"Edited bone {bone_name}")
    else:
        print(f"Bone not found: {bone_name}")
    bpy.ops.object.mode_set(mode='OBJECT')
else:
    print(f"Armature not found: {armature_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def parent_bone(self, child_bone: str, parent_bone: str, armature_name: str, connected: bool = False, user_prompt: str = "Parent bone") -> str:
        """
        Parent a bone to another bone in the same armature.

        Args:
            child_bone: Child bone name
            parent_bone: Parent bone name (empty string for root)
            armature_name: Armature object name
            connected: Connect child to parent (makes them share a joint)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        parent_ref = f'bpy.data.objects["{armature_name}"].data.edit_bones["{parent_bone}"]' if parent_bone else 'None'
        code = f"""
import bpy
arm_obj = bpy.data.objects.get("{armature_name}")
if arm_obj and arm_obj.type == 'ARMATURE':
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    child = arm_obj.data.edit_bones.get("{child_bone}")
    parent = {parent_ref}
    if child and (parent or parent is None):
        if parent is None:
            child.parent = None
        else:
            child.parent = parent
            child.use_connect = {connected}
        print(f"Parented {child_bone} to {parent_bone if parent_bone else 'root'}")
    else:
        print(f"Bone(s) not found")
    bpy.ops.object.mode_set(mode='OBJECT')
else:
    print(f"Armature not found: {armature_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def create_bone_constraint(self, bone_name: str, armature_name: str, constraint_type: str, user_prompt: str = "Create bone constraint", **params) -> str:
        """
        Add a constraint to a bone.

        Args:
            bone_name: Bone name
            armature_name: Armature object name
            constraint_type: Constraint type (e.g., 'IK', 'COPY_ROTATION', 'COPY_LOCATION')
            **params: Constraint-specific properties (target, subtarget, influence, etc.)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        # Simplify: expects mandatory 'target' (object name) and optional 'subtarget' (bone name)
        target = params.get('target')
        subtarget = params.get('subtarget', '')
        other_params = ', '.join([f"{k}={repr(v)}" for k, v in params.items() if k not in ('target', 'subtarget')])
        code = f"""
import bpy
arm_obj = bpy.data.objects.get("{armature_name}")
if arm_obj and arm_obj.type == 'ARMATURE':
    pb = arm_obj.pose.bones.get("{bone_name}")
    if pb:
        constraint = pb.constraints.new(type='{constraint_type.upper()}')
        if "{target}":
            constraint.target = bpy.data.objects.get("{target}")
        if "{subtarget}":
            constraint.subtarget = "{subtarget}"
        # Set additional properties
        {f'constraint.{other_params}.' if other_params else ''}
        print(f"Added {constraint_type} constraint to {bone_name}")
    else:
        print(f"Pose bone not found: {bone_name}")
else:
    print(f"Armature not found: {armature_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def assign_skin_armature(self, mesh_name: str, armature_name: str, user_prompt: str = "Assign armature") -> str:
        """
        Bind a mesh to an armature (Add Armature modifier).

        Args:
            mesh_name: Mesh object name
            armature_name: Armature object name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
mesh = bpy.data.objects.get("{mesh_name}")
arm = bpy.data.objects.get("{armature_name}")
if mesh and arm and mesh.type == 'MESH' and arm.type == 'ARMATURE':
    mod = mesh.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm
    print(f"Added Armature modifier to {mesh_name} targeting {armature_name}")
else:
    print(f"Objects not found or wrong types")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def weight_paint_auto(self, mesh_name: str, armature_name: str, user_prompt: str = "Auto weight paint") -> str:
        """
        Automatic skinning (bone heat weighting).

        Args:
            mesh_name: Mesh object name
            armature_name: Armature object name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
mesh = bpy.data.objects.get("{mesh_name}")
arm = bpy.data.objects.get("{armature_name}")
if mesh and arm:
    # Select mesh, then armature in object mode
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    print(f"Auto-weighted {mesh_name} to {armature_name}")
else:
    print(f"Objects not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def list_vertex_groups(self, object_name: str, user_prompt: str = "List vertex groups") -> List[Dict[str, Any]]:
        """
        List all vertex groups (including bone weights if armature-bound).

        Args:
            object_name: Mesh or armature bound object
            user_prompt: The original user prompt (for telemetry)

        Returns:
            List of vertex group info (name, index, weight sum)
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    groups = []
    for vg in obj.vertex_groups:
        # Compute total weight sum and vertex count
        total = 0.0
        count = 0
        for v in obj.data.vertices:
            try:
                w = vg.weight(v.index)
                total += w
                count += 1
            except:
                pass
        groups.append({{
            'name': vg.name,
            'index': vg.index,
            'total_weight': total,
            'vertex_count': count
        }})
    print(json.dumps(groups))
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

    def get_vertex_weights(self, object_name: str, group_name: str, user_prompt: str = "Get vertex weights") -> Dict[int, float]:
        """
        Get weights for a specific vertex group.

        Args:
            object_name: Mesh object
            group_name: Vertex group name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Dictionary mapping vertex indices to weight values
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    vg = obj.vertex_groups.get("{group_name}")
    if vg:
        weights = {{}}
        for v in obj.data.vertices:
            try:
                w = vg.weight(v.index)
                weights[v.index] = w
            except:
                pass
        print(json.dumps(weights))
    else:
        print(json.dumps({{}}))
else:
    print(json.dumps({{}}))
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return {}

    def assign_vertex_weight(self, object_name: str, group_name: str, vertex_indices: List[int], weight: float, user_prompt: str = "Assign vertex weight") -> str:
        """
        Assign weight to specific vertices in a vertex group.

        Args:
            object_name: Mesh object
            group_name: Vertex group name
            vertex_indices: List of vertex indices
            weight: Weight value (0-1)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        indices_str = ', '.join(map(str, vertex_indices))
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    vg = obj.vertex_groups.get("{group_name}")
    if not vg:
        vg = obj.vertex_groups.new(name="{group_name}")
    for idx in {vertex_indices}:
        vg.add([idx], {weight}, 'REPLACE')
    print(f"Assigned weight {weight} to {{len({vertex_indices})}} vertices in {group_name}")
else:
    print(f"Object not found or not mesh")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Shape Keys (Morph Targets) ---

    def add_shape_key(self, object_name: str, name: str, from_mix: bool = False, user_prompt: str = "Add shape key") -> str:
        """
        Add a new shape key to a mesh.

        Args:
            object_name: Mesh object name
            name: Name for the new shape key
            from_mix: If True, create from current vertex positions
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    if not obj.data.shape_keys:
        obj.shape_key_add(name='Basis', from_mix=False)
    sk = obj.shape_key_add(name="{name}", from_mix={str(from_mix).lower()})
    print(f"Added shape key '{name}' to {object_name}")
else:
    print(f"Object not found or not a mesh")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def list_shape_keys(self, object_name: str, user_prompt: str = "List shape keys") -> List[Dict[str, Any]]:
        """
        List all shape keys on a mesh.

        Args:
            object_name: Mesh object name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            List of shape key info (name, value, slider_min, slider_max, etc.)
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj and obj.data.shape_keys:
    keys = []
    for sk in obj.data.shape_keys.key_blocks:
        keys.append({{
            'name': sk.name,
            'value': sk.value,
            'slider_min': sk.slider_min,
            'slider_max': sk.slider_max,
            'is_basis': sk.name == 'Basis'
        }})
    print(json.dumps(keys))
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

    def set_shape_key_value(self, object_name: str, key_name: str, value: float, user_prompt: str = "Set shape key value") -> str:
        """
        Set the influence value of a shape key (0.0 to 1.0).

        Args:
            object_name: Mesh object name
            key_name: Shape key name
            value: Value (typically 0.0 - 1.0)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.data.shape_keys:
    sk = obj.data.shape_keys.key_blocks.get("{key_name}")
    if sk:
        sk.value = {value}
        print(f"Set {key_name} value to {value}")
    else:
        print(f"Shape key not found: {key_name}")
else:
    print(f"No shape keys")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def key_shape_keys(self, object_name: str, key_name: str, user_prompt: str = "Key shape key") -> str:
        """
        Set a shape key as the active key for editing (keying).
        Equivalent to clicking the key icon in UI.

        Args:
            object_name: Mesh object name
            key_name: Shape key name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.data.shape_keys:
    sk = obj.data.shape_keys.key_blocks.get("{key_name}")
    if sk:
        sk.keyframe_insert(data_path="value")
        print(f"Inserted keyframe for shape key {key_name}")
    else:
        print(f"Shape key not found: {key_name}")
else:
    print(f"No shape keys")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def rename_shape_key(self, object_name: str, old_name: str, new_name: str, user_prompt: str = "Rename shape key") -> str:
        """
        Rename a shape key.

        Args:
            object_name: Mesh object name
            old_name: Current shape key name
            new_name: New name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.data.shape_keys:
    sk = obj.data.shape_keys.key_blocks.get("{old_name}")
    if sk:
        sk.name = "{new_name}"
        print(f"Renamed shape key '{old_name}' to '{new_name}'")
    else:
        print(f"Shape key not found: {old_name}")
else:
    print(f"No shape keys")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def remove_shape_key(self, object_name: str, key_name: str, user_prompt: str = "Remove shape key") -> str:
        """
        Remove a shape key (except Basis which cannot be removed).

        Args:
            object_name: Mesh object name
            key_name: Shape key name to remove
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.data.shape_keys:
    sk = obj.data.shape_keys.key_blocks.get("{key_name}")
    if sk and sk.name != 'Basis':
        obj.shape_key_remove(sk)
        print(f"Removed shape key: {key_name}")
    elif sk.name == 'Basis':
        print(f"Cannot remove Basis shape key")
    else:
        print(f"Shape key not found: {key_name}")
else:
    print(f"No shape keys")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def transfer_shape_key(self, src_object: str, dest_object: str, key_name: str, user_prompt: str = "Transfer shape key") -> str:
        """
        Transfer a shape key from one mesh to another (basic: copy vertex positions from basis to target).

        Args:
            src_object: Source mesh object (with shape key)
            dest_object: Destination mesh object
            key_name: Name of shape key to transfer
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
src = bpy.data.objects.get("{src_object}")
dst = bpy.data.objects.get("{dest_object}")
if src and dst and src.type == 'MESH' and dst.type == 'MESH':
    src_sk = src.data.shape_keys.key_blocks.get("{key_name}") if src.data.shape_keys else None
    if src_sk:
        # Ensure destination has shape key
        if not dst.data.shape_keys:
            dst.shape_key_add(name='Basis', from_mix=False)
        dst_sk = dst.shape_key_add(name="{key_name}", from_mix=False)
        # Copy coordinates
        for i, vert in enumerate(src.data.vertices):
            if i < len(dst.data.vertices):
                dst_sk.data[i].co = src_sk.data[i].co
        print(f"Transferred shape key '{key_name}' from {src_object} to {dest_object}")
    else:
        print(f"Shape key not found on source: {key_name}")
else:
    print(f"Objects not found or not meshes")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)


# Convenience function
def get_rigging_client() -> BlenderMCPRiggingClient:
    """Get a BlenderMCPRiggingClient instance with default settings."""
    return BlenderMCPRiggingClient()


if __name__ == "__main__":
    # Simple CLI for testing rigging tools
    import argparse
    parser = argparse.ArgumentParser(description="Blender MCP Rigging Client")
    parser.add_argument("tool", help="Tool to call (e.g., create_armature, add_shape_key)")
    parser.add_argument("--params", type=str, help="JSON string of parameters")
    parser.add_argument("--server", default="blender", help="mcporter server name")
    args = parser.parse_args()

    try:
        client = get_rigging_client()
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
