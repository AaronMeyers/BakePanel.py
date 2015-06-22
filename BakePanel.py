import bpy
import os
import datetime

bpy.types.Object.shouldBake = bpy.props.BoolProperty(name="Should Bake", default=False)
bpy.types.Object.useDefaultSamples = bpy.props.BoolProperty(name="Use Default Samples", default=True)
bpy.types.Object.bakeWidth = bpy.props.IntProperty(name="Bake Width", default=1024)
bpy.types.Object.bakeHeight = bpy.props.IntProperty(name="Bake Height", default=1024)
bpy.types.Object.bakeSamples = bpy.props.IntProperty(name="Bake Samples", default=500)

class BakePanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Baking Properties"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        
        ob = bpy.context.active_object
        
        if ( len(context.selected_objects) > 0 and len(ob.material_slots) > 0 ):

            row = layout.row()
            row.prop( ob, "shouldBake" )
            

            # Create two columns, by using a split layout.
            split = layout.split()

            # First column
            col = split.column(align=True)
            col.label(text="Resolution:")
            col.prop(ob, "bakeWidth")
            col.prop(ob, "bakeHeight")

            # Second column, aligned
            col = split.column(align=True)
            col.label(text="Sampling:")
            col.prop(ob, "useDefaultSamples" )
            if ( not ob.useDefaultSamples ):
                col.prop(ob, "bakeSamples")
            
            row = layout.row()
            row.operator("object.bake_selected")

            # endif ( len(ob.material_slots) > 0 ):
            
        # always show the bake all bakeable button
        row = layout.row()
        row.scale_y = 3.0
        row.operator("object.bake_all_bakeable")


class BakeAllBakeable(bpy.types.Operator):
    bl_idname = "object.bake_all_bakeable"
    bl_label = "Bake All Bakeable"
    
    def invoke(self, context, event):
        bpy.ops.object.select_all(action='DESELECT')
        for ob in context.scene.objects:
            if ob.shouldBake:
                ob.select = True
                bakeObject(ob)
                ob.select = False
        return {"FINISHED"}

class BakeSelected(bpy.types.Operator):
    bl_idname = "object.bake_selected"
    bl_label = "Bake Selected"
    
    def invoke(self, context, event):
        selected = []
        for ob in context.selected_objects:
            selected.append( ob )
            
        bpy.ops.object.select_all(action='DESELECT')
        
        for ob in selected:
            if ( ob.shouldBake ):
                ob.select = True
                bakeObject(ob)
                ob.select = False
        return {"FINISHED"}

class BakeObject(bpy.types.Operator):
    bl_idname = "object.bake_object"
    bl_label = "Bake Object"
    
    def invoke(self, context, event):
        ob = context.active_object
        if ( ob.shouldBake ):
            bakeObject(ob)
        return {"FINISHED"}
    
def bakeObject(ob):
    print("bakeObject:", ob.name)
    export_dir = os.path.relpath( os.path.dirname( bpy.data.filepath ) ) + os.sep + "baked" + os.sep
    if not os.path.exists( export_dir ):
        os.makedirs( export_dir )
#    print( "bpy.data.filepath:", bpy.data.filepath )
#    print( "export_dir:", export_dir )
    # create a temporary image to render to
    if bpy.data.images.get("TEMP_BAKE_IMAGE",0) is not 0:
        bpy.data.images["TEMP_BAKE_IMAGE"].user_clear()
        bpy.data.images.remove(bpy.data.images["TEMP_BAKE_IMAGE"])
        
    bpy.ops.image.new(name="TEMP_BAKE_IMAGE", width=ob.bakeWidth, height=ob.bakeHeight)
    tempImage = bpy.data.images["TEMP_BAKE_IMAGE"]
    # save a reference to whatever image is already being used by the 
    for mat_slot in ob.material_slots:
        mat = mat_slot.material
        node_tree = mat.node_tree
        node = node_tree.nodes.new("ShaderNodeTexImage")
        node.select = True
        node.name = "tempNode"
        node.image = tempImage
        node_tree.nodes.active = node
    
    bakeStart = datetime.datetime.now()
    
    if ( ob.useDefaultSamples ):
        bpy.ops.object.bake(type='COMBINED')
    else:
        cachedSamples = bpy.context.scene.cycles.samples
        bpy.context.scene.cycles.samples = ob.bakeSamples
        bpy.ops.object.bake(type='COMBINED')
        bpy.context.scene.cycles.samples = cachedSamples
        
    
    bakeElapsed = datetime.datetime.now() - bakeStart
    elapsedTime = divmod( bakeElapsed.days * 86400 + bakeElapsed.seconds, 60 )
    print( "baked", ob.name, "in", elapsedTime[0], "minutes and", elapsedTime[1], "seconds" )
    
        
    print( "finished baking", ob.name )
    tempImage.filepath_raw = export_dir + ob.name + '.png'
    tempImage.file_format = 'PNG'
    tempImage.save()
    
    # clean up our temporary texture nodes
    for mat_slot in ob.material_slots:
        mat = mat_slot.material
        node_tree = mat.node_tree
        node = node_tree.nodes["tempNode"]
        node_tree.nodes.remove( node )
    
    # get rid of the temp image we rendered to
    tempImage.user_clear()
    bpy.data.images.remove(tempImage)
    

def register():
    bpy.utils.register_class(BakeAllBakeable)
    bpy.utils.register_class(BakeSelected)
    bpy.utils.register_class(BakeObject)
    bpy.utils.register_class(BakePanel)


def unregister():
    bpy.utils.unregister_class(BakeAllBakeable)
    bpy.utils.register_class(BakeSelected)
    bpy.utils.unregister_class(BakeObject)
    bpy.utils.unregister_class(BakePanel)


if __name__ == "__main__":
    register()



