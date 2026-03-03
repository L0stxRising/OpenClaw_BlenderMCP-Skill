"""
Blender MCP Animation Client

Extends BlenderMCPClient with animation and NLA (Non-Linear Animation) tools.
"""

from blender_mcp_client import BlenderMCPClient
import json
from typing import Any, Dict, List, Optional


class BlenderMCPAnimationClient(BlenderMCPClient):
    """
    Animation-focused client extending BlenderMCPClient.

    Adds keyframe animation, f-curve manipulation, NLA tracks, and action management.
    """

    # --- Keyframe Animation ---

    def insert_keyframe(self, object_name: str, data_path: str, frame: int, value: Any, user_prompt: str = "Insert keyframe") -> str:
        """
        Insert a keyframe for a specific property.

        Args:
            object_name: Object name
            data_path: Property data path (e.g., 'location', 'rotation_euler', 'scale', '["prop"]')
            frame: Frame number
            value: Value to keyframe (single number or list for vectors)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        # Ensure value is represented correctly in Python code
        if isinstance(value, (list, tuple)):
            value_str = f"[{', '.join(map(str, value))}]"
        else:
            value_str = str(value)
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.keyframe_insert(data_path="{data_path}", frame={frame}, value={value_str})
    print(f"Inserted keyframe on {object_name}.{data_path} at frame {frame}")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def insert_location_keyframe(self, object_name: str, frame: int, location: Optional[List[float]] = None, user_prompt: str = "Insert location keyframe") -> str:
        """
        Insert a location keyframe.

        Args:
            object_name: Object name
            frame: Frame number
            location: [x, y, z] location (if None, uses current)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        if location:
            loc_str = f"[{location[0]}, {location[1]}, {location[2]}]"
            code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.location = {loc_str}
    obj.keyframe_insert(data_path="location", frame={frame})
    print(f"Inserted location keyframe at frame {frame}")
else:
    print(f"Object not found: {object_name}")
"""
        else:
            code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.keyframe_insert(data_path="location", frame={frame})
    print(f"Inserted location keyframe at frame {frame} (current location)")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def insert_rotation_keyframe(self, object_name: str, frame: int, rotation: Optional[List[float]] = None, mode: str = 'EULER', user_prompt: str = "Insert rotation keyframe") -> str:
        """
        Insert a rotation keyframe.

        Args:
            object_name: Object name
            frame: Frame number
            rotation: [x, y, z] rotation in radians (if None, uses current)
            mode: 'EULER' or 'QUATERNION'
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        if rotation:
            rot_str = f"[{rotation[0]}, {rotation[1]}, {rotation[2]}]"
            code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.rotation_{mode.lower()} = {rot_str}
    obj.keyframe_insert(data_path="rotation_{mode.lower()}", frame={frame})
    print(f"Inserted rotation keyframe at frame {frame}")
else:
    print(f"Object not found: {object_name}")
"""
        else:
            data_path = f"rotation_{mode.lower()}"
            code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.keyframe_insert(data_path="{data_path}", frame={frame})
    print(f"Inserted rotation keyframe at frame {frame} (current rotation)")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def insert_scale_keyframe(self, object_name: str, frame: int, scale: Optional[List[float]] = None, user_prompt: str = "Insert scale keyframe") -> str:
        """
        Insert a scale keyframe.

        Args:
            object_name: Object name
            frame: Frame number
            scale: [x, y, z] scale (if None, uses current)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        if scale:
            scale_str = f"[{scale[0]}, {scale[1]}, {scale[2]}]"
            code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.scale = {scale_str}
    obj.keyframe_insert(data_path="scale", frame={frame})
    print(f"Inserted scale keyframe at frame {frame}")
else:
    print(f"Object not found: {object_name}")
"""
        else:
            code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.keyframe_insert(data_path="scale", frame={frame})
    print(f"Inserted scale keyframe at frame {frame} (current scale)")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def insert_visibility_keyframe(self, object_name: str, frame: int, visible: bool = True, user_prompt: str = "Insert visibility keyframe") -> str:
        """
        Insert a visibility/hide keyframe.

        Args:
            object_name: Object name
            frame: Frame number
            visible: True for visible, False for hidden
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.hide_viewport = not {visible}
    obj.hide_render = not {visible}
    obj.keyframe_insert(data_path="hide_viewport", frame={frame})
    obj.keyframe_insert(data_path="hide_render", frame={frame})
    print(f"Inserted visibility keyframe at frame {frame} (visible={visible})")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def get_keyframes(self, object_name: str, data_path: str, user_prompt: str = "Get keyframes") -> List[Dict[str, Any]]:
        """
        List all keyframes for a specific property.

        Args:
            object_name: Object name
            data_path: Property data path
            user_prompt: The original user prompt (for telemetry)

        Returns:
            List of keyframe info dicts (frame, value, interpolation, etc.)
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    keyframes = []
    for fc in fcurves:
        for kp in fc.keyframe_points:
            keyframes.append({{
                'frame': kp.frame,
                'value': kp.co.y,
                'interpolation': kp.interpolation,
                'handle_left': list(kp.handle_left),
                'handle_right': list(kp.handle_right)
            }})
    print(json.dumps(keyframes))
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

    def delete_keyframe(self, object_name: str, data_path: str, frame: int, user_prompt: str = "Delete keyframe") -> str:
        """
        Delete a specific keyframe.

        Args:
            object_name: Object name
            data_path: Property data path
            frame: Frame number to delete
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    for fc in fcurves:
        for kp in list(fc.keyframe_points):
            if kp.frame == {frame}:
                fc.keyframe_points.remove(kp)
    print(f"Deleted keyframe on {object_name}.{data_path} at frame {frame}")
else:
    print(f"No animation data or keyframe not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def delete_all_keyframes(self, object_name: str, data_path: Optional[str] = None, user_prompt: str = "Delete all keyframes") -> str:
        """
        Delete all keyframes for an object (or specific property).

        Args:
            object_name: Object name
            data_path: Optional property data path; if None, clears all
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        dp_part = f', data_path="{data_path}"' if data_path else ''
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    if {data_path is not None}:
        fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    else:
        fcurves = obj.animation_data.action.fcurves[:]
    for fc in fcurves:
        fc.keyframe_points.clear()
    print(f"Deleted keyframes{f' for {data_path}' if {data_path} else ''} on {object_name}")
else:
    print(f"No animation data")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_autokey(self, enabled: bool = True, user_prompt: str = "Set autokey") -> str:
        """
        Enable or disable Auto Keying globally.

        Args:
            enabled: True to enable, False to disable
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
bpy.context.scene.tool_settings.use_keyframe_insert_auto = {enabled}
print("Auto Keying " + ("enabled" if {enabled} else "disabled"))
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_keyframe_interpolation(self, object_name: str, data_path: str, frame: int, mode: str = 'BEZIER', user_prompt: str = "Set interpolation") -> str:
        """
        Set interpolation mode for a keyframe.

        Args:
            object_name: Object name
            data_path: Property data path
            frame: Frame number
            mode: Interpolation mode (BEZIER, LINEAR, CONSTANT)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    for fc in fcurves:
        for kp in fc.keyframe_points:
            if kp.frame == {frame}:
                kp.interpolation = '{mode.upper()}'
    print(f"Set interpolation to {mode} for keyframe at frame {frame}")
else:
    print(f"Keyframe not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- F-Curves (Animation Curves) ---

    def get_fcurve(self, object_name: str, data_path: str, index: int = 0, user_prompt: str = "Get fcurve") -> Optional[Dict[str, Any]]:
        """
        Get a specific fcurve.

        Args:
            object_name: Object name
            data_path: Property data path
            index: Array index for vector properties (0=x,1=y,2=z)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Dictionary with fcurve info or None
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == "{data_path}" and fc.array_index == {index}:
            points = [{{'frame': kp.frame, 'value': kp.co.y}} for kp in fc.keyframe_points]
            info = {{
                'data_path': fc.data_path,
                'array_index': fc.array_index,
                'keyframe_points': points,
                'auto_smoothing': fc.auto_smoothing
            }}
            print(json.dumps(info))
            break
    else:
        print(null)
else:
    print(null)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            parsed = self._parse_json_output(result)
            if isinstance(parsed, dict):
                return parsed
        return None

    def list_fcurves(self, object_name: str, user_prompt: str = "List fcurves") -> List[Dict[str, Any]]:
        """
        List all f-curves on an object.

        Args:
            object_name: Object name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            List of fcurve descriptors (data_path, array_index, keyframe_count)
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = []
    for fc in obj.animation_data.action.fcurves:
        fcurves.append({{
            'data_path': fc.data_path,
            'array_index': fc.array_index,
            'keyframe_count': len(fc.keyframe_points),
            'auto_smoothing': fc.auto_smoothing
        }})
    print(json.dumps(fcurves))
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

    def modify_fcurve_handles(self, object_name: str, data_path: str, frame: int, handle_type: str = 'AUTO', user_prompt: str = "Modify fcurve handles") -> str:
        """
        Modify handle type for a specific keyframe.

        Args:
            object_name: Object name
            data_path: Property data path
            frame: Frame number
            handle_type: 'AUTO', 'VECTOR', 'ALIGNED', 'FREE'
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    found = False
    for fc in fcurves:
        for kp in fc.keyframe_points:
            if kp.frame == {frame}:
                kp.handle_left_type = '{handle_type.upper()}'
                kp.handle_right_type = '{handle_type.upper()}'
                found = True
    if found:
        print(f"Set handle type to {handle_type} for keyframe at frame {frame}")
    else:
        print(f"Keyframe not found")
else:
    print(f"No animation data")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def add_fcurve_modifier(self, object_name: str, data_path: str, mod_type: str, user_prompt: str = "Add fcurve modifier", **params) -> str:
        """
        Add a modifier to an fcurve (e.g., noise, cycles, limits).

        Args:
            object_name: Object name
            data_path: Property data path
            mod_type: Modifier type (e.g., 'NOISE', 'CYCLES', 'LIMITS')
            **params: Modifier-specific parameters
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        params_str = ', '.join([f"{k}={repr(v)}" for k, v in params.items()])
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    if fcurves:
        mod = fcurves[0].modifiers.new(name='{mod_type.upper()}', type='{mod_type.upper()}')
        print(f"Added {mod_type} modifier to fcurve")
    else:
        print(f"Fcurve not found")
else:
    print(f"No animation data")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_fcurve_extrapolation(self, object_name: str, data_path: str, mode: str = 'CONSTANT', user_prompt: str = "Set fcurve extrapolation") -> str:
        """
        Set extrapolation mode for fcurves.

        Args:
            object_name: Object name
            data_path: Property data path
            mode: 'CONSTANT', 'LINEAR', 'MAKE_LINEAR', 'MAKE_CYCLIC', 'REVERSE_MAKE_CYCLIC'
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    for fc in fcurves:
        fc.extrapolation = '{mode.upper()}'
    print(f"Set fcurve extrapolation to {mode}")
else:
    print(f"No animation data")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def sample_fcurve(self, object_name: str, data_path: str, frame: float, user_prompt: str = "Sample fcurve") -> float:
        """
        Get the value of an fcurve at a specific frame (including interpolation).

        Args:
            object_name: Object name
            data_path: Property data path
            frame: Frame number (can be fractional)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Evaluated value at that frame
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    values = []
    for fc in fcurves:
        val = fc.evaluate({frame})
        values.append(val)
    print(values if len(values) > 1 else values[0])
else:
    print(0.0)
"""
        result = self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)
        if isinstance(result, (int, float)):
            return result
        if isinstance(result, list) and result:
            return result[0]
        return 0.0

    def smooth_fcurve(self, object_name: str, data_path: str, factor: float = 0.5, user_prompt: str = "Smooth fcurve") -> str:
        """
        Smooth fcurve keyframe values using a simple moving average-like smoothing.

        Args:
            object_name: Object name
            data_path: Property data path
            factor: Smoothing factor (0-1)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    fcurves = [fc for fc in obj.animation_data.action.fcurves if fc.data_path == "{data_path}"]
    for fc in fcurves:
        # Simple smoothing: average with neighbors (placeholder)
        kps = fc.keyframe_points
        for i in range(1, len(kps)-1):
            prev_val = kps[i-1].co.y
            curr_val = kps[i].co.y
            next_val = kps[i+1].co.y
            kps[i].co.y = curr_val * {factor} + (prev_val + next_val) * (1 - {factor}) / 2
    print(f"Smoothed fcurve for {data_path}")
else:
    print(f"No animation data")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- NLA (Non-Linear Animation) ---

    def create_nla_strip(self, object_name: str, action_name: str, start_frame: int, name: Optional[str] = None, user_prompt: str = "Create NLA strip") -> str:
        """
        Add an NLA strip from an Action.

        Args:
            object_name: Object name that owns the action
            action_name: Name of the Action to push
            start_frame: Starting frame for the strip
            name: Optional strip name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        strip_name = f'"{name}"' if name else "None"
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    action = obj.animation_data.action
    if obj.animation_data.nla_tracks is None:
        obj.animation_data.nla_tracks.new()
    track = obj.animation_data.nla_tracks[0]
    strip = track.strips.new(name={strip_name or action.name + '_strip'}, start={start_frame}, action=action)
    print(f"Created NLA strip '{strip.name}' from action '{action.name}' at frame {start_frame}")
else:
    print(f"Object has no active action")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def list_nla_strips(self, object_name: str, user_prompt: str = "List NLA strips") -> List[Dict[str, Any]]:
        """
        List all NLA strips on an object.

        Args:
            object_name: Object name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            List of strip info dictionaries (name, start, end, action, etc.)
        """
        code = f"""
import bpy
import json
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data:
    strips_info = []
    for track in obj.animation_data.nla_tracks:
        for strip in track.strips:
            strips_info.append({{
                'name': strip.name,
                'start': strip.frame_start,
                'end': strip.frame_end,
                'action': strip.action.name if strip.action else None,
                'extrapolation': strip.extrapolation,
                'blend_type': strip.blend_type,
                'use_reverse': strip.use_reverse
            }})
    print(json.dumps(strips_info))
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

    def nla_strip_blend_type(self, strip_name: str, object_name: str, blend_type: str = 'REPLACE', user_prompt: str = "Set NLA strip blend type") -> str:
        """
        Set blend type for an NLA strip.

        Args:
            strip_name: Name of the NLA strip
            object_name: Object name
            blend_type: Blend type (REPLACE, ADD, SUBTRACT, MULTIPLY, etc.)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
found = False
if obj and obj.animation_data:
    for track in obj.animation_data.nla_tracks:
        for strip in track.strips:
            if strip.name == "{strip_name}":
                strip.blend_type = '{blend_type.upper()}'
                found = True
                break
        if found:
            break
    print(f"Set blend_type to {blend_type}" if found else f"Strip not found: {strip_name}")
else:
    print("No animation data")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def nla_strip_extrapolation(self, strip_name: str, object_name: str, mode: str = 'HOLD', user_prompt: str = "Set NLA strip extrapolation") -> str:
        """
        Set extrapolation for an NLA strip.

        Args:
            strip_name: Name of the NLA strip
            object_name: Object name
            mode: Extrapolation mode (HOLD, HOLD_FORWARD, HOLD_BACKWARD, NONE, etc.)
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
found = False
if obj and obj.animation_data:
    for track in obj.animation_data.nla_tracks:
        for strip in track.strips:
            if strip.name == "{strip_name}":
                strip.extrapolation = '{mode.upper()}'
                found = True
                break
        if found:
            break
    print(f"Set extrapolation to {mode}" if found else f"Strip not found: {strip_name}")
else:
    print("No animation data")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def push_down_action(self, object_name: str, user_prompt: str = "Push down action") -> str:
        """
        Convert the current action into an NLA strip (Push Down).

        Args:
            object_name: Object name
            user_prompt: The original user prompt (for telemetry)

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.animation_data and obj.animation_data.action:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.nla.action_pushdown(action_name=obj.animation_data.action.name)
    print(f"Pushed down action to NLA for {object_name}")
else:
    print(f"No active action")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)


# Convenience function
def get_animation_client() -> BlenderMCPAnimationClient:
    """Get a BlenderMCPAnimationClient instance with default settings."""
    return BlenderMCPAnimationClient()


if __name__ == "__main__":
    # Simple CLI for testing animation tools
    import argparse
    parser = argparse.ArgumentParser(description="Blender MCP Animation Client")
    parser.add_argument("tool", help="Tool to call (e.g., insert_location_keyframe, list_fcurves)")
    parser.add_argument("--params", type=str, help="JSON string of parameters")
    parser.add_argument("--server", default="blender", help="mcporter server name")
    args = parser.parse_args()

    try:
        client = get_animation_client()
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
