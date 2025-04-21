bl_info = {
    "name": "Link Editor",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Link Editor",
    "description": "Manage linked files clearly.",
    "category": "Object",
}

import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.app.handlers import persistent

library_order = []
expanded_states = {}
link_active_states = {}
linked_elements = {}
resolution_status = {}

LO_SUFFIXES = ("_Lo.blend", "_lo.blend", "_Low.blend", "_low.blend")

def normalize_filepath(filepath):
    abs_path = bpy.path.abspath(filepath)
    if bpy.context.preferences.filepaths.use_relative_paths:
        return bpy.path.relpath(abs_path).replace("\\", "/")
    return abs_path.replace("\\", "/")

def force_viewport_refresh():
    bpy.context.view_layer.update()
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

def get_linked_item_names(library):
    result = {}
    for dt in ['objects', 'collections']:
        col = getattr(bpy.data, dt)
        names = [item.name for item in col if item.library == library]
        if names:
            result[dt] = names
    return result

def link_collection_force(parent_coll, coll):
    try:
        parent_coll.children.link(coll)
    except:
        pass

def link_object_force(parent_coll, obj):
    try:
        parent_coll.objects.link(obj)
    except:
        pass

class LINKEDITOR_OT_switch_mode(bpy.types.Operator, ImportHelper):
    bl_idname = "linkeditor.switch_mode"
    bl_label = "Switch Mode"
    original_filepath: bpy.props.StringProperty()
    filter_glob: bpy.props.StringProperty(default="*.blend", options={'HIDDEN'})

    def invoke(self, context, event):
        self.filepath = get_hi_res_path(self.original_filepath)
        return self.execute(context)

    def execute(self, context):
        import os
        old_fp = normalize_filepath(self.original_filepath)
        new_fp = normalize_filepath(self.filepath)

        abs_new_fp = bpy.path.abspath(new_fp)
        if not os.path.exists(abs_new_fp):
            self.report({'ERROR'}, f"File not found: {abs_new_fp}")
            return {'CANCELLED'}

        print(f"\nSwitching from: {old_fp} to: {new_fp}")

        old_lib = next((lib for lib in bpy.data.libraries if normalize_filepath(lib.filepath) == old_fp), None)
        if old_lib:
            linked_elements.pop(old_fp, None)
            link_active_states.pop(old_fp, None)
            bpy.data.libraries.remove(old_lib)
            print(f"Removed old library: {old_fp}")

        with bpy.data.libraries.load(new_fp, link=True) as (data_from, data_to):
            data_to.objects = data_from.objects[:]
            data_to.collections = data_from.collections[:]

        active_coll = context.view_layer.active_layer_collection.collection

        for coll in data_to.collections:
            if coll:
                link_collection_force(active_coll, coll)
                print(f"Linked Collection: {coll.name}")

        for obj in data_to.objects:
            if obj:
                link_object_force(active_coll, obj)
                print(f"Linked Object: {obj.name}")

        new_lib = next((lib for lib in bpy.data.libraries if normalize_filepath(lib.filepath) == new_fp), None)
        if new_lib:
            linked_elements[new_fp] = get_linked_item_names(new_lib)
            link_active_states[new_fp] = True
            if new_fp not in library_order:
                library_order.append(new_fp)
            print(f"Library state updated: {linked_elements[new_fp]}")

        force_viewport_refresh()
        self.report({'INFO'}, f"Switched to: {os.path.basename(new_fp)}")
        return {'FINISHED'}

def normalize_filepath(filepath):
    abs_path = bpy.path.abspath(filepath)
    if bpy.context.preferences.filepaths.use_relative_paths:
        return bpy.path.relpath(abs_path).replace("\\", "/")
    return abs_path.replace("\\", "/")

class LINKEDITOR_PT_panel(bpy.types.Panel):
    bl_label = "Link Editor"
    bl_idname = "LINKEDITOR_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Link Editor"

    def draw(self, context):
        layout = self.layout
        layout.operator("linkeditor.switch_mode", text="Switch Mode")

def register():
    bpy.utils.register_class(LINKEDITOR_OT_switch_mode)
    bpy.utils.register_class(LINKEDITOR_PT_panel)

def unregister():
    bpy.utils.unregister_class(LINKEDITOR_OT_switch_mode)
    bpy.utils.unregister_class(LINKEDITOR_PT_panel)

if __name__ == "__main__":
    register()
