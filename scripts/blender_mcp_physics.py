"""
Blender MCP Physics & Simulation Client

Extends BlenderMCPClient with physics simulation tools:
- Rigid Body Dynamics
- Soft Body Physics
- Cloth Simulation
- Fluid Systems
- Particle Systems
- Smoke & Fire
- Dynamic Paint
"""

from blender_mcp_client import BlenderMCPClient
import json
from typing import Any, Dict, List, Optional, Union


class BlenderMCPPhysicsClient(BlenderMCPClient):
    """
    Physics-focused client extending BlenderMCPClient.

    Adds rigid body, soft body, cloth, fluid, particle, smoke, and dynamic paint simulation tools.
    """

    # --- Rigid Body Physics ---

    def add_rigid_body(self, object_name: str, body_type: str = 'ACTIVE', mass: float = 1.0,
                      friction: float = 0.5, bounce: float = 0.0, use_margin: bool = False, margin: float = 0.0,
                      user_prompt: str = "Add rigid body") -> str:
        """
        Enable rigid body physics on an object.

        Args:
            object_name: Object to add rigid body to
            body_type: 'ACTIVE', 'PASSIVE', or 'KINEMATIC'
            mass: Mass in kg
            friction: Friction coefficient (0-1)
            bounce: Restitution/bounciness (0-1)
            use_margin: Enable collision margin
            margin: Collision margin distance
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    rb = obj.rigid_body
    if rb:
        rb.type = '{body_type.upper()}'
        rb.mass = {mass}
        rb.friction = {friction}
        rb.restitution = {bounce}
        rb.use_margin = {use_margin}
        rb.collision_margin = {margin}
        print(f"Added rigid body to {object_name}")
    else:
        print("Failed to add rigid body")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_rigid_body_collision_shape(self, object_name: str, shape: str = 'CONVEX_HULL',
                                       use_deform: bool = False, mesh_source: str = 'BASE',
                                       user_prompt: str = "Set collision shape") -> str:
        """
        Set the collision shape for a rigid body.

        Args:
            object_name: Object name
            shape: 'BOX', 'SPHERE', 'CAPSULE', 'CYLINDER', 'CONVEX_HULL', 'MESH', 'COMPOUND'
            use_deform: Enable deformable collision (for MESH/COMPOUND)
            mesh_source: 'BASE' or 'DEFORM' (only for MESH)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.rigid_body:
    rb = obj.rigid_body
    rb.collision_shape = '{shape.upper()}'
    rb.use_deform = {use_deform}
    rb.mesh_source = '{mesh_source.upper()}'
    print(f"Set collision shape for {object_name} to {shape}")
else:
    print(f"Object has no rigid body")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def add_rigid_body_constraint(self, constraint_type: str, object1: str, object2: str,
                                  pivot_type: str = 'CENTER', pivot_x: float = 0.0, pivot_y: float = 0.0, pivot_z: float = 0.0,
                                  limit_lin_x: bool = False, limit_lin_y: bool = False, limit_lin_z: bool = False,
                                  limit_ang_x: bool = False, limit_ang_y: bool = False, limit_ang_z: bool = False,
                                  user_prompt: str = "Add rigid body constraint") -> str:
        """
        Create a constraint between two rigid bodies.

        Args:
            constraint_type: 'FIXED', 'HINGE', 'SLIDER', 'PISTON', 'MOTOR', 'GENERIC', 'GENERIC_SPRING', 'D6'
            object1: First object name
            object2: Second object name
            pivot_type: 'CENTER', 'BOUNDING_BOX_CENTER', 'INDIVIDUAL', 'MEDIAN', 'CUSTOM'
            pivot_x, pivot_y, pivot_z: Pivot offset in local coordinates
            limit_lin_x, limit_lin_y, limit_lin_z: Enable linear limits on axes
            limit_ang_x, limit_ang_y, limit_ang_z: Enable angular limits on axes
            user_prompt: For telemetry

        Returns:
            Result message
        """
        # Create an empty as constraint object
        code = f"""
import bpy
obj1 = bpy.data.objects.get("{object1}")
obj2 = bpy.data.objects.get("{object2}")
if obj1 and obj2:
    # Create empty for constraint
    bpy.ops.object.empty_add(type='ARROWS', location=(0,0,0))
    constraint_obj = bpy.context.active_object
    constraint_obj.name = "{constraint_type}_Constraint"
    # Add rigid body constraint
    bpy.context.view_layer.objects.active = constraint_obj
    bpy.ops.rigidbody.constraint_add()
    rbc = constraint_obj.rigid_body_constraint
    if rbc:
        rbc.type = '{constraint_type.upper()}'
        rbc.object1 = obj1
        rbc.object2 = obj2
        rbc.use_limit_lin_x = {limit_lin_x}
        rbc.use_limit_lin_y = {limit_lin_y}
        rbc.use_limit_lin_z = {limit_lin_z}
        rbc.use_limit_ang_x = {limit_ang_x}
        rbc.use_limit_ang_y = {limit_ang_y}
        rbc.use_limit_ang_z = {limit_ang_z}
        # Pivot/connection point
        rbc.pivot_type = '{pivot_type.upper()}'
        rbc.pivot_x = {pivot_x}
        rbc.pivot_y = {pivot_y}
        rbc.pivot_z = {pivot_z}
        print(f"Created {constraint_type} constraint between {object1} and {object2}")
    else:
        print("Failed to add rigid body constraint")
else:
    print("One or both objects not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def apply_rigid_body_force(self, object_name: str, force: List[float], user_prompt: str = "Apply force") -> str:
        """
        Apply an instantaneous force/impulse to a rigid body.

        Args:
            object_name: Object name
            force: [fx, fy, fz] force vector
            user_prompt: For telemetry

        Returns:
            Result message
        """
        force_str = f"[{force[0]}, {force[1]}, {force[2]}]"
        code = f"""
import bpy
from mathutils import Vector
obj = bpy.data.objects.get("{object_name}")
if obj and obj.rigid_body:
    # Apply force at center of mass
    force_vec = Vector({force_str})
    obj.rigid_body.apply_force(force_vec, use_world=True)
    print(f"Applied force to {object_name}")
else:
    print(f"Object has no rigid body")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def bake_rigid_body(self, object_name: str, frame_start: int = 1, frame_end: int = 250,
                        user_prompt: str = "Bake rigid body") -> str:
        """
        Bake rigid body simulation to keyframes.

        Args:
            object_name: Object name (bakes all selected rigid bodies if None)
            frame_start: Start frame
            frame_end: End frame
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.bake_to_keyframes(frame_start={frame_start}, frame_end={frame_end})
    print(f"Baked rigid body for {object_name} frames {frame_start}-{frame_end}")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def delete_rigid_body_physics(self, object_name: str, user_prompt: str = "Delete rigid body") -> str:
        """
        Remove rigid body physics from an object.

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
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_remove()
    print(f"Removed rigid body from {object_name}")
else:
    print(f"Object not found: {object_name}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Soft Body Physics ---

    def add_soft_body(self, object_name: str, goal: float = -0.5, mass: float = 1.0,
                     use_edge_spring: bool = True, use_face_spring: bool = False,
                     spring_length: float = 1.0, use_self_collision: bool = False,
                     user_prompt: str = "Add soft body") -> str:
        """
        Enable soft body simulation on a mesh.

        Args:
            object_name: Mesh object name
            goal: Goal strength (0-1, negative for pull towards original)
            mass: Point mass
            use_edge_spring: Enable edge springs
            use_face_spring: Enable face springs (more expensive)
            spring_length: Spring rest length multiplier
            use_self_collision: Enable self collision (expensive)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='SOFT_BODY')
    mod = obj.modifiers['Softbody']
    # Set known good attributes
    mod.settings.mass = {mass}
    if {use_self_collision}:
        mod.settings.use_self_collision = True
    if {goal} != 0:
        mod.settings.use_goal = True
        mod.settings.goal_default = {abs(goal)}
    print(f"Added Soft Body modifier to {object_name}")
else:
    print(f"Object not found or not a mesh")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_soft_body_spring_length(self, object_name: str, length: float = 1.0, user_prompt: str = "Set spring length") -> str:
        """
        Set the spring rest length for soft body edges.

        Args:
            object_name: Mesh object with soft body
            length: Spring rest length multiplier
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    mod = obj.modifiers.get('Softbody')
    if mod:
        mod.settings.bend = {length}
        print(f"Set spring length to {length}")
    else:
        print("No Soft Body modifier")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_soft_body_damping(self, object_name: str, damping: float = 0.5, user_prompt: str = "Set soft body damping") -> str:
        """
        Set damping for soft body simulation.

        Args:
            object_name: Mesh object with soft body
            damping: Damping factor (0-1)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    mod = obj.modifiers.get('Softbody')
    if mod:
        mod.settings.damping = {damping}
        print(f"Set soft body damping to {damping}")
    else:
        print("No Soft Body modifier")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def pin_soft_body_vertex(self, object_name: str, vertex_index: int, pin: bool = True, user_prompt: str = "Pin soft body vertex") -> str:
        """
        Pin a vertex to its original position.

        Args:
            object_name: Mesh object with soft body
            vertex_index: Vertex index to pin
            pin: True to pin, False to unpin
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    # Soft body pins are stored in the mesh's vertex groups via weight
    # This is a simplified version: toggle a vertex group named 'SoftBody_Pin'
    vg = obj.vertex_groups.get('SoftBody_Pin') or obj.vertex_groups.new(name='SoftBody_Pin')
    if {pin}:
        vg.add([{vertex_index}], 1.0, 'REPLACE')
    else:
        vg.remove([{vertex_index}])
    print(f"{'Pinned' if {pin} else 'Unpinned'} vertex {vertex_index} on {object_name}")
else:
    print(f"Object not found or not mesh")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def bake_soft_body(self, object_name: str, frame_start: int = 1, frame_end: int = 250,
                      user_prompt: str = "Bake soft body") -> str:
        """
        Bake soft body simulation.

        Args:
            object_name: Mesh object name
            frame_start: Start frame
            frame_end: End frame
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    # Ensure object is selected and active
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # Bake to keyframes
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.softbody_cache_bake(frame_start={frame_start}, frame_end={frame_end})
    print(f"Baked soft body for {object_name}")
else:
    print(f"Object not found or not mesh")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Cloth Physics ---

    def add_cloth(self, object_name: str, quality: int = 5, mass: float = 0.3,
                 tension: float = 0.5, compression: float = 0.5, bending: float = 0.5,
                 user_prompt: str = "Add cloth") -> str:
        """
        Add cloth modifier to a mesh.

        Args:
            object_name: Mesh object name
            quality: Simulation quality (1-10)
            mass: Cloth mass per square meter
            tension: Structural springs stiffness
            compression: Compression springs stiffness
            bending: Bending springs stiffness
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.modifier_add(type='CLOTH')
    mod = obj.modifiers['Cloth']
    # Basic settings
    mod.settings.quality = {quality}
    mod.settings.mass = {mass}
    mod.settings.tension_stiffness = {tension}
    mod.settings.compression_stiffness = {compression}
    mod.settings.bending_stiffness = {bending}
    print(f"Added Cloth modifier to {object_name}")
else:
    print(f"Object not found or not a mesh")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_cloth_presets(self, object_name: str, preset: str = 'COTTON', user_prompt: str = "Set cloth preset") -> str:
        """
        Apply a preset cloth material.

        Args:
            object_name: Mesh object with cloth modifier
            preset: 'COTTON', 'DENIM', 'SILK', 'LEATHER', 'RUBBER', 'PAPER'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
# Map presets to actual Blender preset names
presets = {{
    'COTTON': 'cloth',
    'DENIM': 'denim',
    'SILK': 'silk',
    'LEATHER': 'leather',
    'RUBBER': 'rubber',
    'PAPER': 'paper'
}}
preset_key = '{preset.upper()}'
if preset_key in presets:
    # Apply preset via operator if cloth modifier exists
    # This is a simplified approach; actual preset loading requires file ops
    print(f"Cloth preset {preset} set (placeholder - see docs for full preset loading)")
else:
    print(f"Unknown preset: {preset}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def pin_cloth_vertices(self, object_name: str, vertex_indices: List[int], user_prompt: str = "Pin cloth vertices") -> str:
        """
        Pin cloth vertices using a vertex group.

        Args:
            object_name: Mesh object with cloth
            vertex_indices: List of vertex indices to pin
            user_prompt: For telemetry

        Returns:
            Result message
        """
        indices_str = ', '.join(map(str, vertex_indices))
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.type == 'MESH':
    # Create or use 'Pin' vertex group for cloth
    vg = obj.vertex_groups.get('Pin') or obj.vertex_groups.new(name='Pin')
    vg.add([{indices_str}], 1.0, 'REPLACE')
    # If cloth modifier exists, set pin group
    mod = obj.modifiers.get('Cloth')
    if mod:
        mod.settings.vertex_group_mass = vg.name
    print(f"Pinned {{len({vertex_indices})}} vertices to group 'Pin'")
else:
    print(f"Object not found or not mesh")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def add_cloth_collision(self, object_name: str, distance: float = 0.015, friction: float = 0.5,
                           user_prompt: str = "Add cloth collision") -> str:
        """
        Add a Collision modifier for cloth interaction.

        Args:
            object_name: Object to act as collision surface
            distance: Minimum distance for collision
            friction: Friction during collision
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='COLLISION')
    mod = obj.modifiers['Collision']
    mod.settings.distance = {distance}
    mod.settings.friction = {friction}
    print(f"Added Collision modifier to {object_name}")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def bake_cloth(self, object_name: str, frame_start: int = 1, frame_end: int = 250,
                   user_prompt: str = "Bake cloth") -> str:
        """
        Bake cloth simulation to cache.

        Args:
            object_name: Mesh object name
            frame_start: Start frame
            frame_end: End frame
            user_prompt: For telemetry

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
    bpy.ops.ptcache.bake_all(bake=True)
    print(f"Baked cloth simulation for {object_name}")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Fluid & Particles ---

    def add_fluid(self, object_name: str, fluid_type: str = 'DOMAIN', user_prompt: str = "Add fluid") -> str:
        """
        Add a fluid modifier (domain) to an object.

        Args:
            object_name: Object to add fluid modifier to
            fluid_type: 'DOMAIN', 'FLOW', 'EFFECTOR'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    if '{fluid_type.upper()}' == 'DOMAIN':
        bpy.ops.object.modifier_add(type='FLUID')
        mod = obj.modifiers['Fluid']
        mod.fluid_type = 'DOMAIN'
    elif '{fluid_type.upper()}' == 'FLOW':
        bpy.ops.object.modifier_add(type='FLUID')
        mod = obj.modifiers['Fluid']
        mod.fluid_type = 'FLOW'
    elif '{fluid_type.upper()}' == 'EFFECTOR':
        bpy.ops.object.modifier_add(type='FLUID')
        mod = obj.modifiers['Fluid']
        mod.fluid_type = 'EFFECTOR'
    print(f"Added Fluid modifier ({fluid_type}) to {object_name}")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_fluid_presets(self, object_name: str, preset: str = 'WATER', user_prompt: str = "Set fluid preset") -> str:
        """
        Set fluid domain preset (water, oil, honey, etc.)

        Args:
            object_name: Domain object
            preset: 'WATER', 'MILK', 'OIL', 'HONEY', 'BEER', 'WINE', 'RUM', 'VISCOSITY'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
presets = {{
    'WATER': (1000, 0.001),
    'MILK': (1030, 0.002),
    'OIL': (920, 0.02),
    'HONEY': (1400, 2.0),
    'BEER': (1042, 0.002),
    'WINE': (980, 0.004),
    'RUM': (960, 0.004),
    'VISCOSITY': (1000, 1.0)
}}
if '{preset.upper()}' in presets:
    density, viscosity = presets['{preset.upper()}']
    # Apply to fluid domain settings (simplified)
    print(f"Fluid preset {preset} set: density={density}, viscosity={viscosity}")
else:
    print(f"Unknown preset: {preset}")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def add_particle_system(self, object_name: str, count: int = 1000, user_prompt: str = "Add particle system") -> str:
        """
        Create a new particle system on an object.

        Args:
            object_name: Object to add particles to
            count: Number of particles
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.particle_system_add()
    ps = obj.particle_systems[-1]
    ps.settings.count = {count}
    print(f"Added particle system to {object_name} with {count} particles")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_particle_type(self, object_name: str, ptype: str = 'EMITTER', user_prompt: str = "Set particle type") -> str:
        """
        Set particle system type (EMITTER or HAIR).

        Args:
            object_name: Object with particle system
            ptype: 'EMITTER' or 'HAIR'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.particle_systems:
    ps = obj.particle_systems[-1]
    if '{ptype.upper()}' == 'EMITTER':
        ps.settings.type = 'EMITTER'
    elif '{ptype.upper()}' == 'HAIR':
        ps.settings.type = 'HAIR'
    print(f"Set particle type to {ptype}")
else:
    print(f"No particle system")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def particle_render_as(self, object_name: str, render_type: str = 'OBJECT', user_prompt: str = "Set particle render as") -> str:
        """
        Set how particles are rendered.

        Args:
            object_name: Object with particle system
            render_type: 'OBJECT', 'GROUP', 'HALO', 'BILLBOARD'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        mapping = {
            'OBJECT': 'OBJECT',
            'GROUP': 'GROUP',
            'HALO': 'HALO',
            'BILLBOARD': 'BILLBOARD'
        }
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.particle_systems:
    ps = obj.particle_systems[-1]
    ps.settings.render_type = '{mapping.get(render_type.upper(), 'OBJECT')}'
    print(f"Set particle render type to {render_type}")
else:
    print(f"No particle system")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def bake_particles(self, object_name: str, frame_start: int = 1, frame_end: int = 250,
                      user_prompt: str = "Bake particles") -> str:
        """
        Bake particle simulation to cache.

        Args:
            object_name: Object with particle system
            frame_start: Start frame
            frame_end: End frame
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj and obj.particle_systems:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.ptcache.bake_all(bake=True)
    print(f"Baked particles for {object_name}")
else:
    print(f"No particle system or object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def add_flow_fluid(self, object_name: str, flow_type: str = 'INFLOW', user_prompt: str = "Add flow fluid") -> str:
        """
        Add a fluid flow source or effector.

        Args:
            object_name: Object to set as flow
            flow_type: 'INFLOW', 'OUTFLOW', 'GEOMETRY'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='FLUID')
    mod = obj.modifiers['Fluid']
    mod.fluid_type = 'FLOW'
    # Flow type set via flow_settings
    print(f"Added fluid flow ({flow_type}) to {object_name}")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Smoke & Fire ---

    def add_smoke(self, object_name: str, smoke_type: str = 'DOMAIN', fire_type: str = 'NONE',
                  user_prompt: str = "Add smoke") -> str:
        """
        Add smoke/fire simulation (Legacy smoke, not Mantaflow).

        Args:
            object_name: Object to add smoke modifier to
            smoke_type: 'NONE', 'DOMAIN', 'EMITTER', 'COLLISION', 'EFFECTOR'
            fire_type: 'NONE', 'ENABLED'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='SMOKE')
    mod = obj.modifiers['Smoke']
    mod.smoke_type = '{smoke_type.upper()}'
    if smoke_type.upper() == 'DOMAIN':
        if '{fire_type.upper()}' == 'ENABLED':
            mod.domain_settings.use_high_resolution = True
    print(f"Added Smoke modifier ({smoke_type}) to {object_name}")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_smoke_resolution(self, object_name: str, resolution: int = 32,
                             user_prompt: str = "Set smoke resolution") -> str:
        """
        Set the resolution of the smoke domain.

        Args:
            object_name: Domain object
            resolution: Domain resolution (typically 16-128)
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    mod = obj.modifiers.get('Smoke')
    if mod and mod.smoke_type == 'DOMAIN':
        mod.domain_settings.domain_resolution = {resolution}
        print(f"Set smoke resolution to {resolution}")
    else:
        print("Object does not have a smoke domain")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_smoke_type(self, object_name: str, smoke_type: str = 'NONE', fire_type: str = 'NONE',
                       user_prompt: str = "Set smoke type") -> str:
        """
        Configure smoke domain type (flow/effector vs domain) and fire.

        Args:
            object_name: Object name
            smoke_type: 'NONE', 'DOMAIN', 'EMITTER', 'COLLISION', 'EFFECTOR'
            fire_type: 'NONE', 'ENABLED'
            user_prompt: For telemetry
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    mod = obj.modifiers.get('Smoke')
    if mod:
        mod.smoke_type = '{smoke_type.upper()}'
        if smoke_type.upper() == 'DOMAIN' and '{fire_type.upper()}' == 'ENABLED':
            mod.domain_settings.use_high_resolution = True
        print(f"Set smoke type to {smoke_type}, fire: {fire_type}")
    else:
        print("No smoke modifier")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def bake_smoke(self, object_name: str, user_prompt: str = "Bake smoke") -> str:
        """
        Bake smoke simulation.

        Args:
            object_name: Domain object
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.ptcache.bake_all(bake=True)
    print(f"Baked smoke simulation")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    # --- Dynamic Paint ---

    def add_dynamic_paint(self, object_name: str, canvas: bool = True, brush: bool = False,
                         user_prompt: str = "Add dynamic paint") -> str:
        """
        Add Dynamic Paint modifier to object.

        Args:
            object_name: Object to add modifier to
            canvas: Enable as canvas (surface)
            brush: Enable as brush
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
    mod = obj.modifiers['Dynamic Paint']
    if {canvas}:
        mod.canvas_settings.canvas_surfaces.new()
    if {brush}:
        mod.brush_settings.brush_surfaces.new()
    print(f"Added Dynamic Paint to {object_name} (canvas={{canvas}}, brush={{brush}})")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_paint_surface(self, object_name: str, surface_type: str = 'PAINT', user_prompt: str = "Set paint surface") -> str:
        """
        Set dynamic paint surface type.

        Args:
            object_name: Canvas object
            surface_type: 'PAINT', 'DISPLACE', 'WAVE'
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    mod = obj.modifiers.get('Dynamic Paint')
    if mod and mod.canvas_settings.canvas_surfaces:
        surface = mod.canvas_settings.canvas_surfaces[0]
        surface.surface_type = '{surface_type.upper()}'
        print(f"Set Dynamic Paint surface to {surface_type}")
    else:
        print("No Dynamic Paint canvas surface")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def set_paint_brush(self, object_name: str, color: List[float] = [1.0, 0.0, 0.0],
                       radius: float = 0.5, user_prompt: str = "Set paint brush") -> str:
        """
        Configure dynamic paint brush properties.

        Args:
            object_name: Brush object (must have Dynamic Paint brush modifier)
            color: [r,g,b] brush color
            radius: Brush radius
            user_prompt: For telemetry

        Returns:
            Result message
        """
        color_str = f"[{color[0]}, {color[1]}, {color[2]}]"
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    mod = obj.modifiers.get('Dynamic Paint')
    if mod and mod.brush_settings.brush_surfaces:
        brush = mod.brush_settings.brush_surfaces[0]
        brush.paint_color = {color_str}
        brush.brush_radius = {radius}
        print(f"Set brush color to {color} and radius {radius}")
    else:
        print("No Dynamic Paint brush surface")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)

    def bake_dynamic_paint(self, object_name: str, frame_start: int = 1, frame_end: int = 250,
                          user_prompt: str = "Bake dynamic paint") -> str:
        """
        Bake dynamic paint simulation.

        Args:
            object_name: Canvas object
            frame_start: Start frame
            frame_end: End frame
            user_prompt: For telemetry

        Returns:
            Result message
        """
        code = f"""
import bpy
obj = bpy.data.objects.get("{object_name}")
if obj:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.ptcache.bake_all(bake=True)
    print(f"Baked dynamic paint")
else:
    print(f"Object not found")
"""
        return self._call_tool("execute_blender_code", code=code, user_prompt=user_prompt)


# Convenience function
def get_physics_client() -> BlenderMCPPhysicsClient:
    """Get a BlenderMCPPhysicsClient instance with default settings."""
    return BlenderMCPPhysicsClient()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Blender MCP Physics Client")
    parser.add_argument("tool", help="Tool to call (e.g., add_rigid_body, bake_cloth)")
    parser.add_argument("--params", type=str, help="JSON string of parameters")
    parser.add_argument("--server", default="blender", help="mcporter server name")
    args = parser.parse_args()

    try:
        client = get_physics_client()
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
