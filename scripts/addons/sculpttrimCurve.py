# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""
Author:
    script by Alex Telford | CG Cookie | www.blendercookie.com | www.metalix.co.nz
Description:
    This script will create a panel in the sculpt menu that will all triming objects by creating a boolean based on a grease pencil stroke or a curve.
Warning:
    This script is currently in a public Beta release, there are bugs and I recommend you take a backup of your work, I take no responsibility in any part either direct or in-direct at the loss of any work. Use at your own risk.
KNOWN BUGS:
    On line 421-ish I extrude away from the camera, this needs to be reworked as it is un-predictable.
"""

import bpy
from bpy.props import *
from mathutils import *


bl_info = {
    "name": "Sculpt trim curve",
    "author": "Alex Telford",
    "version": (0, 7),
    "blender": (2, 6, 6),
    "location": "View3D > Toolshelf",
    "description": "Trims mesh based on curve or grease pencil stroke",
    "warning": "Public Beta",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"}


class TrimCurvesPanel(bpy.types.Panel):

    """
    Creates the 'Trim Mesh with Curve' panel, which will appear in the
    toolshelf of the 3D view when in Object, Edit, or Sculpt mode if there is
    at least one mesh object in the current scene.
    """

    bl_idname = "VIEW3D_PT_trim_curves"
    bl_label = "Trim Mesh with Curve"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    @classmethod
    def poll(cls, context):
        """Returns True, indicating that the panel should be displayed, if the
        current context is appropriate for this tool and there is at least one
        trimmable object in the current scene.
        """

        def scene_has_mesh_objects():
            """Helper function that looks for mesh objects in the current
            scene.
            """
            result = False
            for obj in context.scene.objects:
                if "MESH" == obj.type:
                    result = True
                    break
            return result

        return (context.mode in ["OBJECT", "SCULPT", "EDIT_MESH"] and
                scene_has_mesh_objects())

    def draw(self, context):
        """
        Lays out and draws the panel.
        """

        # The Toolshelf region makes a column-based layout most appropriate.
        layout = self.layout
        col = layout.column()

        # The operator's properties extend the Object and Scene data.
        obj = context.object
        scn = context.scene

        # Although text="" is repeating the default value for the parameter,
        # this must be defined explicitly in properties calls to avoid a second
        # label being drawn alongside the property value, in addition to the
        # label we set above it.

        col.label("Object:")
        col.prop_search(obj, "TCinitObject",
                        scn, "objects",
                        text="",
                        icon="MESH_DATA")

        col.label("Curve Type:")
        col.prop(scn, "TCinitCurveType",
                 text="")

        if scn.TCinitCurveType == "TC_CURVETYPE_CURVE":
            col.label("Curve:")
            col.prop_search(obj, "TCinitCurve",
                            scn, "objects",
                            text="",
                            icon="CURVE_DATA")

        col.prop(scn, "TCinitCyclic")

        col.label("Cut Depth:")
        col.prop(scn, "TCinitDepth",
                 text="")

        col.label("Division Spacing:")
        col.prop(scn, "TCinitDivision",
                 text="")

        if scn.TCinitCyclic == False:
            col.label("Extrusion Depth:")
            col.prop(scn, "TCinitExtrusion",
                     text="")

            col.label("Axis:")
            col.prop(scn, "TCinitAxis",
                     text="")

        col.separator()
        col.prop(scn, "TCinitApplyMod")
        col.prop(scn, "TCinitReverseDir")
        col.prop(scn, "TCinitReverseDepth")
        col.prop(scn, "TCinitReverseTrim")

        col.label("Return Mode:")
        col.prop(scn, "TCinitReturnMode",
                 text="")

        col.separator()
        layout.operator("trim.curves",
                        text="Trim")


class OBJECT_OT_trimCurve(bpy.types.Operator):

    """
    This class will execute our script, options will be taken from props
    """

    bl_idname = "trim.curves"
    bl_label = "Trim Curve"
    bl_description = "Extrude the curve and use it to trim the mesh object"

    def propCalls():
        """
        create props for layout
        a prop is an input field
        this is not required to be in a function, but I like to keep the code clean.
        """

        # In each EnumProperty, name="" is used to suppress the property name
        # that would otherwise appear in the panel's dropdown boxes.

        # create object and curve slot for dropdown
        bpy.types.Object.TCinitObject = bpy.props.StringProperty(
            description="Mesh object to trim")
        bpy.types.Object.TCinitCurve = bpy.props.StringProperty(
            description="Curve object used to trim the mesh object")
        # curve or grease pencil enum
        bpy.types.Scene.TCinitCurveType = bpy.props.EnumProperty(
            items=[("TC_CURVETYPE_GREASE", "Grease Pencil",
                    "Use a grease pencil stroke to trim the mesh object"),
                   ("TC_CURVETYPE_CURVE", "Curve",
                    "Use a curve object to trim the mesh object")],
            name="")
        # create initial value boxes
        bpy.types.Scene.TCinitDepth = FloatProperty(
            name="Depth",
            description="Depth from view",  # FIXME More informative tooltip
            default=5.00,
            min=-100, max=100)
        bpy.types.Scene.TCinitDivision = FloatProperty(
            name="Division",
            description="Division spacing",  # FIXME More informative tooltip
            default=0.5,
            min=-100, max=100)
        bpy.types.Scene.TCinitExtrusion = FloatProperty(
            name="Extrusion",
            description="Extrusion depth",  # FIXME More informative tooltip
            default=5,
            min=-100, max=100)
        # axis enum
        bpy.types.Scene.TCinitAxis = bpy.props.EnumProperty(
            items=[("TC_AXIS_CURSOR", "3D Cursor", "cursor"),  # FIXME More informative tooltip
                   ("TC_AXIS_X", "X", "x"),  # FIXME More informative tooltip
                   ("TC_AXIS_Y", "Y", "y")],  # FIXME More informative tooltip
            name="")
        # apply modifier
        bpy.types.Scene.TCinitApplyMod = BoolProperty(
            name="Apply Boolean Modifier",
            description="Apply the Boolean Modifier used to trim the mesh",
            default=True)
        # is cyclic or extrude
        bpy.types.Scene.TCinitCyclic = BoolProperty(
            name="Cyclic",
            description="Disable extrusion and enable cyclic hole",  # FIXME More informative tooltip
            default=False)
        # reverse direction
        bpy.types.Scene.TCinitReverseDir = BoolProperty(
            name="Reverse Direction",
            description="Reverse the direction of the extrusion",  # FIXME More informative tooltip
            default=False)
        # reverse depth
        bpy.types.Scene.TCinitReverseDepth = BoolProperty(
            name="Reverse Depth",
            description="Reverse the depth of the extrusion",  # FIXME More informative tooltip
            default=False)
        # reverse trim
        bpy.types.Scene.TCinitReverseTrim = BoolProperty(
            name="Reverse Trim",
            description="Keep only the parts of the mesh that intersect with the extruded curve",
            default=False)
        # return to mode enum
        bpy.types.Scene.TCinitReturnMode = bpy.props.EnumProperty(
            items=[("TC_RETURN_SCULPT", "Sculpt Mode",
                    "After trimming the mesh, return to Sculpt Mode"),
                   ("TC_RETURN_OBJECT", "Object Mode",
                    "After trimming the mesh, return to Object Mode"),
                   ("TC_RETURN_EDIT", "Edit Mode",
                    "After trimming the mesh, return to Edit Mode")],
            name="")

    # Initiate prop calls
    propCalls()

    def execute(self, context):
        """
        Trims the mesh object specified by Object.TCinitObject using an
        extruded version of the curve named by Object.TCinitCurve, applied with
        a Boolean modifier.
        """

        def select_exclusively_and_activate(object_to_select):
            """Helper function that ensures only the passed object is selected
            and activated.
            """
            bpy.ops.object.select_all(action="DESELECT")
            object_to_select.select = True
            context.scene.objects.active = object_to_select

        def convert_curve_to_mesh(curve_object):
            """Helper function to convert the curve to a mesh, making it cyclic
            if required.
            """
            select_exclusively_and_activate(curve_object)

            if scn.TCinitCyclic:
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.curve.select_all(action="SELECT")

                for spline in curve_object.data.splines:
                    spline.use_cyclic_u = True

                bpy.ops.object.mode_set(mode="OBJECT")

            bpy.ops.object.convert(target="MESH", keep_original=False)

        def add_boolean_modifier(target_object, modifying_object):
            """Helper function to add a Boolean modifier to the target object.
            If Scene.TCinitReverseTrim is True, the result will be the
            intersection with the modifying object; if False, it will be the
            difference.
            """
            select_exclusively_and_activate(target_object)

            # NOTE Here we assume the target object has no Boolean modifiers
            # already, as "Boolean" is the name given to the first one.
            bpy.ops.object.modifier_add(type="BOOLEAN")
            bpy.context.object.modifiers["Boolean"].object = modifying_object

            boolean_mode = "DIFFERENCE"
            if scn.TCinitReverseTrim:
                boolean_mode = "INTERSECT"
            bpy.context.object.modifiers["Boolean"].operation = boolean_mode

        def apply_boolean_modifier(target_object, modifying_object):
            """Helper function to apply all Boolean modifiers belonging to the
            target object, and to delete the modifying object.
            """
            select_exclusively_and_activate(target_object)

            # NOTE Here we assume that the target object has no user-set
            # Boolean modifiers they want to keep. This is in keeping with the
            # assumption made in creating the modifier.
            for mod in bpy.context.object.modifiers:
                if mod.type == "BOOLEAN":
                    bpy.ops.object.modifier_apply(apply_as="DATA",
                                                  modifier=mod.name)

            # NOTE The following lines cannot be replaced by
            # select_exclusively_and_activate(modifying_object) as the
            # activation causes an error.
            bpy.ops.object.select_all(action="DESELECT")
            modifying_object.select = True

            bpy.ops.object.delete(use_global=False)

        def set_return_mode(return_enum_value):
            """Helper function to set the return mode."""
            modes = {"TC_RETURN_EDIT": "EDIT",
                     "TC_RETURN_OBJECT": "OBJECT",
                     "TC_RETURN_SCULPT": "SCULPT"}

            if return_enum_value not in modes:
                self.report({"DEBUG"},
                            'Unknown value: ' + return_enum_value)
            else:
                bpy.ops.object.mode_set(mode=modes[return_enum_value])

        # The operator's properties extend the Object and Scene data.
        obj = context.object
        scn = context.scene

        # Trim function #
        bpy.ops.object.mode_set(mode='OBJECT')

        # check if mesh exists
        try:
            # create mesh variable
            mesh = bpy.data.objects[obj.TCinitObject]
        except:
            print('mesh does not exist')
            self.report({'WARNING'}, "No mesh selected.")
            return{'FINISHED'}

        # convert pencil to curve or return curve
        if scn.TCinitCurveType == "TC_CURVETYPE_GREASE":
            # check if stroke exists
            try:
                bpy.ops.gpencil.convert(type='PATH')
            except:
                print('Stroke does not exist')
                self.report({'WARNING'}, "No strokes found.")
                return{'FINISHED'}
            # loop through strokes
            for ob in bpy.context.selected_objects:
                    # all strokes start with GP_Layer
                    if (ob != bpy.context.scene.objects.active and
                        ob.name.startswith("GP_Layer")):
                        # create curve variable
                        curve = ob
                        select_exclusively_and_activate(curve)
                        # set curve resolution from default 12 to 1
                        bpy.context.object.data.resolution_u = 1
        else:
            # check if curve exists
            try:
                # create curve variable
                curve = bpy.data.objects[obj.TCinitCurve]
            except:
                print('curve does not exist')
                self.report({'WARNING'}, "No curve selected.")
                return{'FINISHED'}

        convert_curve_to_mesh(curve)

        # rotate curve pivot to view for local transformations #

        select_exclusively_and_activate(curve)
        # center origin
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        # get cursor location, set to vector to break link
        cursorInit = Vector(bpy.context.scene.cursor_location)
        # add temporary empty
        bpy.ops.object.empty_add(type='PLAIN_AXES', view_align=True)
        # assign the emtpy to a variable
        for ob in bpy.context.selected_objects:
                if ob.name.startswith("Empty"):
                    empty = ob

        # get pivot
        pivotPoint = context.space_data.pivot_point
        # set cursor location to curve
        bpy.context.scene.cursor_location = curve.location
        # rotate around cursor
        context.space_data.pivot_point = "CURSOR"
        select_exclusively_and_activate(curve)
        # apply rotation
        bpy.ops.object.transform_apply(location=False, rotation=True,
                                       scale=False)
        # rotate pivot of curve to rotation of empty
        rotatePivot(empty.rotation_euler)
        # set pivot point back to original
        context.space_data.pivot_point = pivotPoint
        # set cursor location back to original
        bpy.context.scene.cursor_location = cursorInit

        # delete empty
        select_exclusively_and_activate(empty)
        bpy.ops.object.delete(use_global=False)

        select_exclusively_and_activate(curve)

        # move curve towards camera #
        # calculate correct xyz values based on view angle #

        # enter edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # get initial curve location
        Ci = Vector(curve.location)

        # Create transformation matrix
        localTranslationForward = Matrix.Translation((0, 0, scn.TCinitDepth/2))
        # move along local coordinates
        curve.matrix_world = curve.matrix_world * localTranslationForward

        # extrude from camera enough times to make divisions #
        # fill first face if cyclic
        if scn.TCinitCyclic == True:
           bpy.ops.mesh.fill(use_beauty=True)
        # calculate number of extrusions required, minimum 1
        extrusions = max(1, round(scn.TCinitDepth/scn.TCinitDivision))
        # get depth of each extrusion
        extrusionDepth = scn.TCinitDepth/extrusions

        # calculate translation for edit mode #
        # new curve location
        Co = Vector(curve.location)
        # BUG option to reverse depth if required
        if scn.TCinitReverseDepth == True:
            # get local space transformations
            distVecCam = world2local(Ci, Co, extrusionDepth)
        else:
            # get invertes local space transformations
            distVecCam = world2local(Ci, Co, -extrusionDepth)
        # extrude for each extrusion
        i = 1
        while i <= extrusions:
            bpy.ops.mesh.extrude_region_move(
                MESH_OT_extrude_region={"mirror":False},
                TRANSFORM_OT_translate={"value":distVecCam,
                                        "constraint_axis":(False, False, True),
                                        "constraint_orientation":'LOCAL'})
            i += 1
            # fill end cap if it is cyclic to retain whole mesh
            if i == extrusions and scn.TCinitCyclic == True:
                bpy.ops.mesh.fill(use_beauty=True)
        # select all mesh
        bpy.ops.mesh.select_all(action='SELECT')
        # calculate extrusion depth from point
        extrusions = max(1, round(scn.TCinitExtrusion/extrusionDepth))

        # Where are we extruding from #
        i = 1
        # are we reversing direction
        if scn.TCinitReverseDir == True:
            dir = -1
        else:
            dir = 1
        # only do this if cyclic is false
        if scn.TCinitCyclic == False:
            if scn.TCinitAxis == "TC_AXIS_CURSOR":
                # cursor #
                # calculate local transforms
                distVecCursor = world2local(curve.location, cursorInit,
                                            extrusionDepth) * dir
                # set pivot to cursor
                context.space_data.pivot_point = "CURSOR"
                # extrude until extrusion depth
                while i <= extrusions:
                    bpy.ops.mesh.extrude_region_move(
                        MESH_OT_extrude_region={"mirror":False},
                        TRANSFORM_OT_translate={"value":(0, 0, 0)})
                    bpy.ops.transform.translate(
                        value=distVecCursor,
                        constraint_axis=(True, True, True),
                        constraint_orientation='LOCAL')
                    i += 1
                # set pivot to original
                context.space_data.pivot_point = pivotPoint
            elif scn.TCinitAxis == "TC_AXIS_X":
                # X #
                # Create transformation matrices
                localTranslationX = Matrix.Translation((10, 0, 0))
                localTranslationXi = Matrix.Translation((-10, 0, 0))
                # move to new location
                curve.matrix_world = curve.matrix_world * localTranslationX
                # store new location
                localTargetX = Vector(curve.location)
                # move back
                curve.matrix_world = curve.matrix_world * localTranslationXi
                # get local transform direction
                distX = world2local(Ci, localTargetX, extrusionDepth) * dir
                # extrude in this new direction
                while i <= extrusions:
                    bpy.ops.mesh.extrude_region_move(
                        MESH_OT_extrude_region={"mirror":False},
                        TRANSFORM_OT_translate={"value":(0, 0, 0)})
                    bpy.ops.transform.translate(
                        value=distX, constraint_axis=(True, False, False),
                        constraint_orientation='LOCAL')
                    i += 1
            elif scn.TCinitAxis == "TC_AXIS_Y":
                # Y #
                # Create transformation matrix
                localTranslationY = Matrix.Translation((0, 10, 0))
                localTranslationYi = Matrix.Translation((0, -10, 0))
                # move to new location
                curve.matrix_world = curve.matrix_world * localTranslationY
                # store new location
                localTargetY = Vector(curve.location)
                # move back
                curve.matrix_world = curve.matrix_world * localTranslationYi
                # extrude in this new direction
                distY = world2local(Ci, localTargetY, extrusionDepth) * dir
                while i <= extrusions:
                    bpy.ops.mesh.extrude_region_move(
                        MESH_OT_extrude_region={"mirror":False},
                        TRANSFORM_OT_translate={"value":(0, 0, 0)})
                    bpy.ops.transform.translate(
                        value=distY, constraint_axis=(False, True, False),
                        constraint_orientation='LOCAL')
                    i += 1
        # set object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        add_boolean_modifier(mesh, curve)
        if scn.TCinitApplyMod:
            apply_boolean_modifier(mesh, curve)

        set_return_mode(scn.TCinitReturnMode)

        # set pivot to cursor
        context.space_data.pivot_point = "BOUNDING_BOX_CENTER"

        return{'FINISHED'}


# functions #
def rotatePivot(rotation):
    """
    rotatePivot(Vector rotation)
    This function will take a vector rotation and rotate the curently selected objects pivot to match without affecting their physical display
    Make sure that you rotate around the cursor and have the entire mesh selected or this will not work.
    This operates on an xyz euler.
    """
    # Rotate in object mode X
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.transform.rotate(value=rotation.x, axis=(1, 0, 0),
                             constraint_orientation='GLOBAL')
    # rotate in edit mode X
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.rotate(value=-rotation.x, axis=(1, 0, 0),
                             constraint_orientation='GLOBAL')
    # Rotate in object mode Y
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.transform.rotate(value=rotation.y, axis=(0, 1, 0),
                             constraint_orientation='GLOBAL')
    # rotate in edit mode Y
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.rotate(value=-rotation.y, axis=(0, 1, 0),
                             constraint_orientation='GLOBAL')
    # Rotate in object mode Z
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.transform.rotate(value=rotation.z, axis=(0, 0, 1),
                             constraint_orientation='GLOBAL')
    # rotate in edit mode Z
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.transform.rotate(value=-rotation.z, axis=(0, 0, 1),
                             constraint_orientation='GLOBAL')
    # return to object mode
    bpy.ops.object.mode_set(mode='OBJECT')


def world2local(a, b, depth):
    """
    Returns a scaled transformation vector between the given vectors.

    This is calculated as the reflection along the z-axis of the normalized vector pointing from a to b, scaled by the given depth.

    Parameters:
    a -- Vector used as the origin for the transformation;
    b -- Vector used as the target for the transformation;
    depth -- float value used to scale the normalized transformation vector.

    Returns:
    Vector indicating transformation from a to b, scaled by depth.

    """
    r = (b - a).normalized() * depth
    return r.reflect(Vector([0, 0, 1]))


# Register functions #
def register():
    # initialize classes #
    bpy.utils.register_class(OBJECT_OT_trimCurve)
    bpy.utils.register_class(TrimCurvesPanel)


def unregister():
    # uninitialize classes #
    bpy.utils.unregister_class(TrimCurvesPanel)
    bpy.utils.register_class(OBJECT_OT_trimCurve)
