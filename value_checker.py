bl_info = {
    "name": "Value Checker",
    "author": "Toto (with Claude)",
    "version": (1, 2, 4),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Value Check",
    "description": "Instant grayscale value check via hotkeys using the Viewport Compositor. Inspired by Photoshop and Rebelle's value check tools.",
    "category": "3D View",
    "doc_url": "https://github.com/audiovisualboy/blender-value-checker",
    "tracker_url": "https://github.com/audiovisualboy/blender-value-checker/issues",
}

import bpy
from bpy.types import AddonPreferences, Operator, Panel
from bpy.props import FloatProperty, EnumProperty, StringProperty, IntProperty

# Node identifiers
BLUR_NODE_NAME     = "VALUE_CHECK_BLUR"
BW_NODE_NAME       = "VALUE_CHECK_BW"
COLORAMP_NODE_NAME = "VALUE_CHECK_COLORAMP"
POSTERIZE_NODE_NAME = "VALUE_CHECK_POSTERIZE"

addon_keymaps = []
KEY_ITEMS = [(f'F{i}', f'F{i}', '') for i in range(1, 19)]


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def get_compositor_tree(context):
    scene = context.scene
    tree = getattr(scene, 'compositing_node_group', None)
    if tree:
        return tree
    return getattr(scene, 'node_tree', None)

def is_node_active(context, node_name):
    tree = get_compositor_tree(context)
    if tree and node_name in tree.nodes:
        return not tree.nodes[node_name].mute
    return False

def is_bw_active(context):
    return is_node_active(context, BW_NODE_NAME)

def is_blur_active(context):
    return is_node_active(context, BLUR_NODE_NAME)

def is_posterize_active(context):
    return is_node_active(context, POSTERIZE_NODE_NAME)

def redraw_all_viewports(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


# ─────────────────────────────────────────
# PREFERENCES CALLBACKS
# ─────────────────────────────────────────

def update_blur_size(self, context):
    tree = get_compositor_tree(context)
    if not tree or BLUR_NODE_NAME not in tree.nodes:
        return
    node = tree.nodes[BLUR_NODE_NAME]
    if 'Size' in node.inputs:
        node.inputs['Size'].default_value = (self.blur_size, self.blur_size)
    else:
        node.size_x = int(self.blur_size)
        node.size_y = int(self.blur_size)

def update_levels(self, context):
    tree = get_compositor_tree(context)
    if not tree or COLORAMP_NODE_NAME not in tree.nodes:
        return
    cr = tree.nodes[COLORAMP_NODE_NAME]
    ramp = cr.color_ramp
    # Clamp so black < mid < white
    black = min(self.levels_black, self.levels_white - 0.02)
    white = max(self.levels_white, self.levels_black + 0.02)
    mid = max(black + 0.01, min(self.levels_mid, white - 0.01))
    ramp.elements[0].position = black
    ramp.elements[1].position = mid
    ramp.elements[2].position = white

def update_posterize_steps(self, context):
    tree = get_compositor_tree(context)
    if not tree or POSTERIZE_NODE_NAME not in tree.nodes:
        return
    node = tree.nodes[POSTERIZE_NODE_NAME]
    if 'Steps' in node.inputs:
        node.inputs['Steps'].default_value = self.posterize_steps


# ─────────────────────────────────────────
# PREFERENCES
# ─────────────────────────────────────────

class ValueCheckPreferences(AddonPreferences):
    bl_idname = __name__

    key_toggle_bw: EnumProperty(
        name="Toggle Value Check",
        description="Hotkey to toggle grayscale value check on/off",
        items=KEY_ITEMS,
        default='F13',
    )
    key_toggle_blur: EnumProperty(
        name="Toggle Blur",
        description="Hotkey to toggle Gaussian blur on/off",
        items=KEY_ITEMS,
        default='F14',
    )
    key_toggle_posterize: EnumProperty(
        name="Toggle Posterize",
        description="Hotkey to toggle posterize on/off",
        items=KEY_ITEMS,
        default='F15',
    )
    blur_size: FloatProperty(
        name="Blur Size",
        description="Gaussian blur strength",
        default=20.0, min=0.0, max=300.0,
        update=update_blur_size,
    )
    levels_black: FloatProperty(
        name="Black Point",
        description="Input black point — like the left triangle in Photoshop Levels",
        default=0.0, min=0.0, max=0.98,
        update=update_levels,
    )
    levels_mid: FloatProperty(
        name="Midtones",
        description="Midtone gamma — like the middle triangle in Photoshop Levels",
        default=0.5, min=0.01, max=0.99,
        update=update_levels,
    )
    levels_white: FloatProperty(
        name="White Point",
        description="Input white point — like the right triangle in Photoshop Levels",
        default=1.0, min=0.02, max=1.0,
        update=update_levels,
    )
    posterize_steps: IntProperty(
        name="Posterize Steps",
        description="Number of value bands for notan/posterize effect",
        default=3, min=2, max=8,
        update=update_posterize_steps,
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Hotkeys (restart Blender after changing):", icon='KEYINGSET')
        col = box.column(align=True)
        col.prop(self, "key_toggle_bw")
        col.prop(self, "key_toggle_blur")
        col.prop(self, "key_toggle_posterize")
        layout.separator()
        layout.operator("view3d.value_check_setup_nodes", text="Re-run Node Setup for Current Scene", icon='FILE_REFRESH')
        layout.label(text="Tip: Run 'Re-run Node Setup' whenever you start a new scene.", icon='INFO')


# ─────────────────────────────────────────
# NODE SETUP
# ─────────────────────────────────────────

def setup_value_check_nodes(context=None, report_fn=None):
    def log(msg):
        print(f"[Value Check] {msg}")
        if report_fn:
            report_fn({'INFO'}, msg)

    if context is None:
        context = bpy.context

    scene = context.scene
    if not scene:
        return False, "No active scene"

    addon_prefs = context.preferences.addons.get(__name__)
    if not addon_prefs:
        return False, "Addon prefs not found"
    prefs = addon_prefs.preferences

    tree = get_compositor_tree(context)
    if not tree:
        return False, "Please click 'New' in the Compositor editor first, then Re-run Setup."

    nodes = tree.nodes
    links = tree.links

    all_node_names = [BLUR_NODE_NAME, BW_NODE_NAME, COLORAMP_NODE_NAME, POSTERIZE_NODE_NAME]

    # If already set up, sync values and bail
    if all(n in nodes for n in all_node_names):
        update_blur_size(prefs, context)
        update_levels(prefs, context)
        update_posterize_steps(prefs, context)
        log("Already set up — synced values")
        return True, "Already set up"

    # Clean up any partial previous setup
    for name in all_node_names:
        if name in nodes:
            nodes.remove(nodes[name])

    # Find or create Render Layers
    render_layers_node = next((n for n in nodes if n.type == 'R_LAYERS'), None)
    if not render_layers_node:
        render_layers_node = nodes.new('CompositorNodeRLayers')
        render_layers_node.location = (-500, 300)
        log("Created Render Layers node")

    # Find Group Output
    composite_node = next((n for n in nodes if n.type == 'GROUP_OUTPUT'), None)
    if not composite_node:
        return False, "No Group Output node found. Please click 'New' in the Compositor first."

    image_socket = next((s for s in composite_node.inputs if s.name == 'Image' and s.type == 'RGBA'), None)
    if not image_socket:
        return False, "Compositor tree looks malformed. Please delete it and click 'New' again."

    # Find or create Viewer node
    viewer_node = next((n for n in nodes if n.type == 'VIEWER'), None)
    if not viewer_node:
        viewer_node = nodes.new('CompositorNodeViewer')
        viewer_node.location = (composite_node.location[0], composite_node.location[1] - 250)
        log("Created Viewer node")

    # Clear all links and reroutes
    for link in list(links):
        links.remove(link)
    for node in list(nodes):
        if node.type == 'REROUTE':
            nodes.remove(node)
    log("Cleared links and reroutes")

    cx, cy = composite_node.location

    # --- Create Blur node (MUTED by default) ---
    blur_node = nodes.new('CompositorNodeBlur')
    blur_node.name = BLUR_NODE_NAME
    blur_node.label = "Value Check Blur"
    blur_node.mute = True
    blur_node.location = (cx - 800, cy - 150)
    if 'Size' in blur_node.inputs:
        blur_node.inputs['Size'].default_value = (prefs.blur_size, prefs.blur_size)
    else:
        blur_node.size_x = int(prefs.blur_size)
        blur_node.size_y = int(prefs.blur_size)

    # --- Create RGB to BW node (proper luminance!) ---
    bw_node = nodes.new('CompositorNodeRGBToBW')
    bw_node.name = BW_NODE_NAME
    bw_node.label = "Value Check BW"
    bw_node.mute = True
    bw_node.location = (cx - 580, cy - 150)
    log("Created RGB to BW node")

    # --- Create Color Ramp node (levels control) ---
    cr_node = nodes.new('ShaderNodeValToRGB')
    cr_node.name = COLORAMP_NODE_NAME
    cr_node.label = "Value Check Levels"
    cr_node.mute = True
    cr_node.location = (cx - 360, cy - 150)
    ramp = cr_node.color_ramp
    # Add a third element for midtones (default 3 elements: black / mid / white)
    ramp.elements[0].position = 0.0    # black point
    ramp.elements[1].position = 1.0    # white point (will become mid after we add third)
    mid_elem = ramp.elements.new(0.5)  # add midtone stop
    # Sort: black=0.0, mid=0.5, white=1.0
    ramp.elements[0].position = prefs.levels_black
    ramp.elements[1].position = prefs.levels_mid
    ramp.elements[2].position = prefs.levels_white
    # Set mid color to grey so it's a smooth ramp
    ramp.elements[1].color = (0.5, 0.5, 0.5, 1.0)
    log("Created Color Ramp node with 3 stops")

    # --- Create Posterize node (MUTED by default) ---
    posterize_node = nodes.new('CompositorNodePosterize')
    posterize_node.name = POSTERIZE_NODE_NAME
    posterize_node.label = "Value Check Posterize"
    posterize_node.mute = True
    posterize_node.location = (cx - 140, cy - 150)
    if 'Steps' in posterize_node.inputs:
        posterize_node.inputs['Steps'].default_value = prefs.posterize_steps
    log("Created Posterize node")

    # --- Wire everything ---
    # Main chain: RL → Blur → BW → ColorRamp → Posterize → Viewer
    links.new(render_layers_node.outputs['Image'], blur_node.inputs['Image'])
    links.new(blur_node.outputs['Image'], bw_node.inputs['Image'])
    links.new(bw_node.outputs['Val'], cr_node.inputs['Factor'])
    links.new(cr_node.outputs['Color'], posterize_node.inputs['Image'])
    links.new(posterize_node.outputs['Image'], viewer_node.inputs['Image'])
    # Final render: RL → Group Output
    links.new(render_layers_node.outputs['Image'], composite_node.inputs['Image'])
    log("All nodes wired! RL → Blur → BW → ColorRamp → Posterize → Viewer")

    return True, "Value Check nodes ready!"


# ─────────────────────────────────────────
# OPERATORS
# ─────────────────────────────────────────

class VIEW3D_OT_value_check_toggle_bw(Operator):
    bl_idname = "view3d.value_check_toggle_bw"
    bl_label = "Toggle Value Check"
    bl_description = "Toggle grayscale value check on/off"

    def execute(self, context):
        tree = get_compositor_tree(context)
        if not tree or BW_NODE_NAME not in tree.nodes:
            self.report({'WARNING'}, "Value Check nodes not found. Run setup first!")
            return {'CANCELLED'}

        bw_node = tree.nodes[BW_NODE_NAME]
        cr_node = tree.nodes.get(COLORAMP_NODE_NAME)
        currently_on = not bw_node.mute

        if currently_on:
            # Turn OFF
            current_mode = context.space_data.shading.use_compositor
            if current_mode != 'DISABLED':
                context.scene['value_check_last_mode'] = current_mode
            bw_node.mute = True
            if cr_node:
                cr_node.mute = True
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.use_compositor = 'DISABLED'
        else:
            # Turn ON — restore last mode
            last_mode = context.scene.get('value_check_last_mode', 'CAMERA')
            bw_node.mute = False
            if cr_node:
                cr_node.mute = False
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.use_compositor = last_mode

        redraw_all_viewports(context)
        return {'FINISHED'}


class VIEW3D_OT_value_check_toggle_blur(Operator):
    bl_idname = "view3d.value_check_toggle_blur"
    bl_label = "Toggle Blur"
    bl_description = "Toggle Gaussian blur on/off"

    def execute(self, context):
        tree = get_compositor_tree(context)
        if not tree or BLUR_NODE_NAME not in tree.nodes:
            self.report({'WARNING'}, "Value Check nodes not found. Run setup first!")
            return {'CANCELLED'}
        currently_on = not tree.nodes[BLUR_NODE_NAME].mute
        tree.nodes[BLUR_NODE_NAME].mute = currently_on
        # If turning blur ON and compositor is disabled, restore last mode
        if not currently_on:
            last_mode = context.scene.get('value_check_last_mode', 'CAMERA')
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            if space.shading.use_compositor == 'DISABLED':
                                space.shading.use_compositor = last_mode
        redraw_all_viewports(context)
        return {'FINISHED'}


class VIEW3D_OT_value_check_toggle_posterize(Operator):
    bl_idname = "view3d.value_check_toggle_posterize"
    bl_label = "Toggle Posterize"
    bl_description = "Toggle posterize/notan effect on/off"

    def execute(self, context):
        tree = get_compositor_tree(context)
        if not tree or POSTERIZE_NODE_NAME not in tree.nodes:
            self.report({'WARNING'}, "Value Check nodes not found. Run setup first!")
            return {'CANCELLED'}
        tree.nodes[POSTERIZE_NODE_NAME].mute = not tree.nodes[POSTERIZE_NODE_NAME].mute
        redraw_all_viewports(context)
        return {'FINISHED'}


class VIEW3D_OT_value_check_set_posterize_steps(Operator):
    bl_idname = "view3d.value_check_set_posterize_steps"
    bl_label = "Set Posterize Steps"
    bl_description = "Set number of posterize value bands"
    steps: IntProperty(default=4)

    def execute(self, context):
        tree = get_compositor_tree(context)
        if not tree or POSTERIZE_NODE_NAME not in tree.nodes:
            return {'CANCELLED'}
        node = tree.nodes[POSTERIZE_NODE_NAME]
        if 'Steps' in node.inputs:
            node.inputs['Steps'].default_value = self.steps
        # Also sync the preference slider
        addon_prefs = context.preferences.addons.get(__name__)
        if addon_prefs:
            addon_prefs.preferences.posterize_steps = self.steps
        redraw_all_viewports(context)
        return {'FINISHED'}


class VIEW3D_OT_value_check_set_mode(Operator):
    bl_idname = "view3d.value_check_set_mode"
    bl_label = "Set Compositor Mode"
    mode: StringProperty(default='CAMERA')

    def execute(self, context):
        # Set mode on ALL 3D viewports to avoid context space issues
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.use_compositor = self.mode
        if self.mode != 'DISABLED':
            context.scene['value_check_last_mode'] = self.mode
        redraw_all_viewports(context)
        return {'FINISHED'}


class VIEW3D_OT_value_check_reset_levels(Operator):
    bl_idname = "view3d.value_check_reset_levels"
    bl_label = "Reset Levels"
    bl_description = "Reset Black, Mid and White points to defaults"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        prefs.levels_white = 1.0
        prefs.levels_mid   = 0.5
        prefs.levels_black = 0.0
        # update_levels fires automatically via property callbacks
        redraw_all_viewports(context)
        return {'FINISHED'}


class VIEW3D_OT_value_check_set_blur_size(Operator):
    bl_idname = "view3d.value_check_set_blur_size"
    bl_label = "Set Blur Size"
    bl_description = "Set blur size to preset value"
    size: FloatProperty(default=30.0)

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        prefs.blur_size = self.size
        # update_blur_size fires automatically via property callback
        redraw_all_viewports(context)
        return {'FINISHED'}


class VIEW3D_OT_value_check_setup_nodes(Operator):
    bl_idname = "view3d.value_check_setup_nodes"
    bl_label = "Setup Value Check Nodes"
    bl_description = "Add Value Check compositor nodes to the current scene"

    def execute(self, context):
        success, msg = setup_value_check_nodes(context=context, report_fn=self.report)
        if success:
            self.report({'INFO'}, f"Value Check: {msg}")
        else:
            self.report({'ERROR'}, f"Value Check: {msg}")
        return {'FINISHED'}


# ─────────────────────────────────────────
# N-PANEL
# ─────────────────────────────────────────

class VIEW3D_PT_value_check(Panel):
    bl_label = "Value Check"
    bl_idname = "VIEW3D_PT_value_check"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Value Check"

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__name__].preferences

        # Get compositor mode from the active 3D viewport
        current_mode = 'DISABLED'
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        current_mode = space.shading.use_compositor
                        break
                break

        bw_on   = is_bw_active(context)
        blur_on = is_blur_active(context)
        post_on = is_posterize_active(context)

        # ── Main toggles ──
        col = layout.column(align=True)
        col.operator(
            "view3d.value_check_toggle_bw",
            text="Value Check: ON" if bw_on else "Value Check: OFF",
            icon='CHECKMARK' if bw_on else 'RADIOBUT_OFF',
            depress=bw_on,
        )
        col.operator(
            "view3d.value_check_toggle_blur",
            text="Blur: ON" if blur_on else "Blur: OFF",
            icon='CHECKMARK' if blur_on else 'RADIOBUT_OFF',
            depress=blur_on,
        )
        col.operator(
            "view3d.value_check_toggle_posterize",
            text="Posterize: ON" if post_on else "Posterize: OFF",
            icon='CHECKMARK' if post_on else 'RADIOBUT_OFF',
            depress=post_on,
        )

        # ── Compositor mode ──
        row = layout.row(align=True)
        op = row.operator("view3d.value_check_set_mode", text="Off", depress=(current_mode == 'DISABLED'))
        op.mode = 'DISABLED'
        op = row.operator("view3d.value_check_set_mode", text="Camera", depress=(current_mode == 'CAMERA'))
        op.mode = 'CAMERA'
        op = row.operator("view3d.value_check_set_mode", text="Always", depress=(current_mode == 'ALWAYS'))
        op.mode = 'ALWAYS'

        layout.separator()

        # ── Blur ──
        layout.prop(prefs, "blur_size", text="Blur Size")
        row = layout.row(align=True)
        for s in [10, 20, 30, 40]:
            op = row.operator(
                "view3d.value_check_set_blur_size",
                text=str(s),
                depress=(prefs.blur_size == s),
            )
            op.size = float(s)

        layout.separator()

        # ── Levels ──
        layout.label(text="Levels:")
        col = layout.column(align=True)
        col.prop(prefs, "levels_white", text="White", slider=True)
        col.prop(prefs, "levels_mid",   text="Mid",   slider=True)
        col.prop(prefs, "levels_black", text="Black", slider=True)
        layout.operator("view3d.value_check_reset_levels", text="Reset Levels", icon='LOOP_BACK')

        layout.separator()

        # ── Posterize steps ──
        layout.label(text="Posterize Steps:")
        layout.prop(prefs, "posterize_steps", text="Steps")
        row = layout.row(align=True)
        for s in [2, 3, 4, 5]:
            op = row.operator(
                "view3d.value_check_set_posterize_steps",
                text=str(s),
                depress=(prefs.posterize_steps == s),
            )
            op.steps = s

        layout.separator()

        # ── Setup ──
        layout.operator("view3d.value_check_setup_nodes", text="Re-run Node Setup", icon='FILE_REFRESH')


# ─────────────────────────────────────────
# KEYMAP
# ─────────────────────────────────────────

def register_keymaps():
    try:
        prefs = bpy.context.preferences.addons[__name__].preferences
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if not kc:
            return
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi_bw   = km.keymap_items.new('view3d.value_check_toggle_bw',        prefs.key_toggle_bw,        'PRESS')
        kmi_blur = km.keymap_items.new('view3d.value_check_toggle_blur',       prefs.key_toggle_blur,      'PRESS')
        kmi_post = km.keymap_items.new('view3d.value_check_toggle_posterize',  prefs.key_toggle_posterize, 'PRESS')
        addon_keymaps.append((km, kmi_bw))
        addon_keymaps.append((km, kmi_blur))
        addon_keymaps.append((km, kmi_post))
    except Exception as e:
        print(f"[Value Check] Keymap registration error: {e}")

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# ─────────────────────────────────────────
# REGISTER / UNREGISTER
# ─────────────────────────────────────────

classes = (
    ValueCheckPreferences,
    VIEW3D_OT_value_check_toggle_bw,
    VIEW3D_OT_value_check_toggle_blur,
    VIEW3D_OT_value_check_toggle_posterize,
    VIEW3D_OT_value_check_set_posterize_steps,
    VIEW3D_OT_value_check_set_mode,
    VIEW3D_OT_value_check_reset_levels,
    VIEW3D_OT_value_check_set_blur_size,
    VIEW3D_OT_value_check_setup_nodes,
    VIEW3D_PT_value_check,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()

def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
