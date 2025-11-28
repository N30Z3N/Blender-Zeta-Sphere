bl_info = {
    "name": "Sculpt Tools",
    "author": "Alfonso Annarumma (Updated for 5.0)",
    "version": (1, 3),
    "blender": (5, 0, 0),
    "location": "View3D > Header > Sculpt Tools",
    "description": "Convert Armatures to Skin/Envelope Meshes for sculpting",
    "warning": "",
    "wiki_url": "",
    "category": "Sculpt",
}

import bpy
import bmesh
import math
import mathutils
from bpy.types import Menu, Panel, UIList, PropertyGroup, Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy.props import (
        StringProperty,
        BoolProperty,
        FloatProperty,
        IntProperty,
        CollectionProperty,
        BoolVectorProperty,
        PointerProperty,
        EnumProperty,
        FloatVectorProperty,
        )

# -------------------------------------------------------------------
#   Properties
# -------------------------------------------------------------------

class SCENE_PG_Sculpt_Tools(PropertyGroup):
    subsurf: IntProperty(
            name="Subdivision",
            default=2,
            min=0, max=6,
            description="Subdivision Surface level"
            )
    
    presub: IntProperty(
            name="PreSubdivision",
            default=0,
            min=0, max=6,
            description="Subdivision Surface first of Skin Modifier (only for skin convertor)"
            )
    
    distance: FloatProperty(
            name="Clean Limit",
            default=0.001,
            precision=4,
            description="Distance from vertices to collapse to clean surface"
            )

# -------------------------------------------------------------------
#   Helper Functions
# -------------------------------------------------------------------

def cone_between(x1, y1, z1, x2, y2, z2, r1, r2):
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1    
    dist = math.sqrt(dx**2 + dy**2 + dz**2)

    bpy.ops.mesh.primitive_cone_add(
        radius1=r1, 
        radius2=r2, 
        depth=dist,
        location=(dx/2 + x1, dy/2 + y1, dz/2 + z1)   
    ) 

    phi = math.atan2(dy, dx) 
    theta = math.acos(dz/dist) 

    # Ensure we are in Euler mode for simple index assignment
    obj = bpy.context.object
    if obj.rotation_mode != 'XYZ':
        obj.rotation_mode = 'XYZ'
        
    obj.rotation_euler[1] = theta 
    obj.rotation_euler[2] = phi


def RemoveDoubles(mesh, distance):
    bm = bmesh.new()   
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    return mesh


def convert_envelope(arm, context):
    coords = []
    obs = []
    prop = context.scene.sculpttools
    
    # Cache cursor location to restore later
    saved_cursor_loc = context.scene.cursor.location.copy()
    
    for bone in arm.data.bones:      
        # Calculate world positions relative to armature location
        x1, y1, z1 = bone.tail_local + arm.location
        r1 = bone.tail_radius
        coord1 = (x1, y1, z1, r1)
        
        if coord1 not in coords:
            coords.append(coord1)
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=r1,
                location=bone.tail_local + arm.location,
            )
            obs.append(context.object.name)

        x2, y2, z2 = bone.head_local + arm.location
        r2 = bone.head_radius
        coord2 = (x2, y2, z2, r2)
        
        if coord2 not in coords:
            coords.append(coord2)
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=r2,
                location=bone.head_local + arm.location
            )
            obs.append(context.object.name)
            
        cone_between(x1, y1, z1, x2, y2, z2, r1, r2)
        obs.append(context.object.name)
 
    # Deselect all first
    bpy.ops.object.select_all(action='DESELECT')
    
    for ob in obs:
        if ob in context.collection.objects:
            context.collection.objects[ob].select_set(True)
    
    # Ensure one is active before joining
    if obs:
        context.view_layer.objects.active = context.collection.objects[obs[0]]
        bpy.ops.object.join()
    
    obj = context.object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    context.scene.cursor.location = arm.location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    
    # Restore cursor
    context.scene.cursor.location = saved_cursor_loc
    
    mesh = obj.data
    obj.data = mesh
    return obj


def convert_skin(context):
    """
    Returns vertex and edge data from the armature for the Skin Modifier.
    """
    verts = []
    edges = []
    arm = context.object
    bones = arm.data.bones
    radius = []
    
    for b in bones:
        v1 = b.head_local
        r1 = b.head_radius
        v2 = b.tail_local
        r2 = b.tail_radius
        
        verts.append(v1)
        verts.append(v2)
        radius.append(r1)
        radius.append(r2)
        
        # Connect the last two added vertices
        edges.append((len(verts)-1, len(verts)-2))

    return verts, edges, radius


# -------------------------------------------------------------------
#   Operators
# -------------------------------------------------------------------

class OBJECT_OT_AddEnvelope(Operator):
    """Add a simple Bone with Envelope view in Edit Mode"""
    bl_idname = "object.addenvelope"
    bl_label = "Add Envelope"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        bpy.ops.object.armature_add()
        ob = context.object
        ob.data.display_type = 'ENVELOPE'
        ob.show_in_front = True
        
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class OBJECT_OT_ConvertEnvelope(Operator):
    """Convert Envelope Armature to Skin Object"""
    bl_idname = "object.convertenvelope"
    bl_label = "Convert Envelope"
    bl_options = {'REGISTER', 'UNDO'}
    
    update: BoolProperty(default=False)
    envelope: BoolProperty(default=False)
    
    # Generic transform props (kept for compatibility with AddObjectHelper)
    align_items = (
        ('WORLD', "World", "Align the new object to the world"),
        ('VIEW', "View", "Align the new object to the view"),
        ('CURSOR', "3D Cursor", "Use the 3D cursor orientation for the new object")
    )
    align: EnumProperty(
        name="Align",
        items=align_items,
        default='WORLD',
        update=AddObjectHelper.align_update_callback,
    )
    location: FloatVectorProperty(
        name="Location",
        subtype='TRANSLATION',
    )
    rotation: FloatVectorProperty(
        name="Rotation",
        subtype='EULER',
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'

    def execute(self, context):
        prop = context.scene.sculpttools
        arm = context.object
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        saved_cursor_loc = context.scene.cursor.location.copy()
        context.scene.cursor.location = context.object.location
        arm.display_type = 'BOUNDS'
        
        if self.envelope:            
            if not self.update:
                convert_envelope(arm, context)
                obj = context.object
                arm.envelope_ID = obj.name
                
                # Modifiers
                bev = obj.modifiers.new("Bevel", 'BEVEL')
                bev.offset_type = 'OFFSET'
                bev.limit_method = 'ANGLE'
                bev.segments = 2
                bev.angle_limit = math.radians(70)
                
                sub = obj.modifiers.new("Subsurf", 'SUBSURF')
                sub.levels = prop.subsurf
            else:
                if 'EDIT' in context.mode:
                    bpy.ops.object.mode_set(mode='OBJECT')
                
                obj = convert_envelope(arm, context)
                
                # Check if old object still exists
                if arm.envelope_ID in context.collection.objects:
                    _obj = context.collection.objects[arm.envelope_ID]
                    _mesh = _obj.data
                    
                    _obj.data = obj.data
                    
                    context.collection.objects.unlink(obj)
                    bpy.data.meshes.remove(_mesh)
                    
                    context.view_layer.objects.active = arm
                    bpy.ops.object.mode_set(mode='EDIT')
                else:
                    self.report({'WARNING'}, "Original envelope object not found. Created new.")
                    arm.envelope_ID = obj.name

            context.scene.cursor.location = saved_cursor_loc
            return {'FINISHED'}
        
        else:
            # Skin Method
            verts_loc, edges, radius = convert_skin(context)

            mesh = bpy.data.meshes.new("Skin")
            bm = bmesh.new()

            for v_co in verts_loc:
                bm.verts.new(v_co)

            bm.verts.ensure_lookup_table()
            for e_idx in edges:
                try:
                    bm.edges.new([bm.verts[i] for i in e_idx])
                except ValueError:
                    pass # Prevent duplicate edge errors

            bm.to_mesh(mesh)
            mesh.update()
            bm.free()

            if not self.update:
                from bpy_extras import object_utils
                object_utils.object_data_add(context, mesh, operator=self)
                
                context.scene.cursor.location = saved_cursor_loc
                
                obj = context.object
                arm.envelope_ID = obj.name
                
                mod = obj.modifiers.new("Subdiv", 'SUBSURF')
                mod.levels = prop.presub
                obj.modifiers.new("Skin", 'SKIN')
            else:
                if arm.envelope_ID in context.scene.objects:
                    obj = context.scene.objects[arm.envelope_ID]
                    _mesh = obj.data
                    obj.data = mesh
                    bpy.data.meshes.remove(_mesh)
                    context.view_layer.objects.active = obj
                    
                    # Reset skin data
                    bpy.ops.mesh.customdata_skin_add()
                    context.scene.cursor.location = saved_cursor_loc
                    context.view_layer.objects.active = arm
                else:
                    # Fallback if ID is lost
                    from bpy_extras import object_utils
                    object_utils.object_data_add(context, mesh, operator=self)
                    obj = context.object
                    obj.modifiers.new("Skin", 'SKIN')

            # Apply Radius to Skin Vertices
            i = 0
            if obj.type == 'MESH':
                # Ensure we are accessing the skin layer correctly
                skin_vertices = obj.data.skin_vertices
                if not skin_vertices:
                     bpy.ops.mesh.customdata_skin_add()
                
                layer = skin_vertices[0]
                for r in radius:
                    if i < len(layer.data):
                        layer.data[i].radius = (r, r)
                    i += 1        
            
            mesh = obj.data
            mesh_ = RemoveDoubles(mesh, prop.distance)
            obj.data = mesh_
            
            if not self.update:
                mod = obj.modifiers.new("Subdiv", 'SUBSURF')
                mod.levels = prop.subsurf
                return {'FINISHED'}
            else:
                bpy.ops.object.mode_set(mode='EDIT')
            
            return {'FINISHED'}


# -------------------------------------------------------------------
#   UI Panel
# -------------------------------------------------------------------

class SCULPT_PT_Extra_tools(Panel):
    bl_label = "Sculpt Tools"
    bl_idname = "SCULPT_PT_Extra_tools"
    bl_region_type = "WINDOW" # Kept for header popover compatibility
    bl_space_type = "VIEW_3D"

    def draw(self, context):
        prop = context.scene.sculpttools
        obj = context.object
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row(align=True)
        row.operator("object.addenvelope",
                        icon='OUTLINER_OB_ARMATURE',
                        text="Add Envelope")
        
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(prop, "subsurf")
        col.prop(prop, "presub")
        col.prop(prop, "distance")
        
        layout.separator()
        
        if obj and obj.type == 'ARMATURE':
            row = layout.row(align=True)
            
            # Skin Convert
            op_skin = row.operator("object.convertenvelope", icon='MOD_SKIN', text="Skin")
            op_skin.update = False
            op_skin.envelope = False
            
            # Update Skin
            if obj.envelope_ID != "" and obj.envelope_ID in context.scene.objects:
                op_upd_skin = row.operator("object.convertenvelope", icon='FILE_REFRESH', text="")
                op_upd_skin.update = True
                op_upd_skin.envelope = False
            
            row = layout.row(align=True)
            
            # Envelope Convert
            op_env = row.operator("object.convertenvelope", icon='MESH_ICOSPHERE', text="Envelope")
            op_env.envelope = True
            op_env.update = False
                            
            # Update Envelope
            if obj.envelope_ID != "" and obj.envelope_ID in context.scene.objects:
                op_upd_env = row.operator("object.convertenvelope", icon='FILE_REFRESH', text="")
                op_upd_env.update = True
                op_upd_env.envelope = True
        else:
            layout.label(text="Select Armature", icon='INFO')


# -------------------------------------------------------------------
#   Registration
# -------------------------------------------------------------------

classes = (
    SCENE_PG_Sculpt_Tools,
    OBJECT_OT_ConvertEnvelope,
    OBJECT_OT_AddEnvelope,
    SCULPT_PT_Extra_tools,
    )

def menu_func(self, context):
    self.layout.popover("SCULPT_PT_Extra_tools", text="Sculpt Tools")

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    bpy.types.Scene.sculpttools = PointerProperty(type=SCENE_PG_Sculpt_Tools)
    bpy.types.Object.envelope_ID = StringProperty(default="")
    
    # Safely append to header if it exists
    if hasattr(bpy.types, "VIEW3D_HT_tool_header"):
        bpy.types.VIEW3D_HT_tool_header.append(menu_func)

def unregister():
    from bpy.utils import unregister_class
    
    if hasattr(bpy.types, "VIEW3D_HT_tool_header"):
        bpy.types.VIEW3D_HT_tool_header.remove(menu_func)
        
    del bpy.types.Scene.sculpttools
    del bpy.types.Object.envelope_ID
    
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
