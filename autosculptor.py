import bpy
import random
from gradio_client import Client

bl_info = {
    "name": "Autosculptor 3D Model Generator",
    "blender": (2, 80, 0),
    "category": "Object",
}

class GeneratorOperator(bpy.types.Operator):
    bl_idname = "object.autosculptor_model_generator"
    bl_label = "Generate 3D Model"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Import properties from context
        autosculptor_props = context.scene.autosculptor_props
        
        prompt = autosculptor_props.prompt
        seed = autosculptor_props.seed
        if autosculptor_props.random_seed:
            seed = random.randint(0, 2147483647)
        guidance_scale = autosculptor_props.guidance_scale
        num_inference_steps = autosculptor_props.num_inference_steps
        model_type = autosculptor_props.model_type
        
        # Shape-E model
        if model_type == "shape-e-text":
            client = Client("hysts/Shap-E")
            result = client.predict(
                prompt=prompt,
                seed=seed,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                api_name="/text-to-3d"
            )
            model_path = result

        else:
            self.report({'ERROR'}, "Invalid model type.")
            return {'CANCELLED'}

        # Load the generated model
        bpy.ops.import_scene.gltf(filepath=model_path)
        
        # Ensure an object has been imported
        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "No object was imported.")
            return {'CANCELLED'}
        
        # Get the imported object (parent)
        parent_obj = bpy.context.selected_objects[0]
        
        # Find mesh object
        obj = None
        if parent_obj.children:
            for child in parent_obj.children:
                if child.type == 'MESH':
                    obj = child
                    break
        
        if obj is None:
            self.report({'ERROR'}, "No mesh object found among imported children.")
            return {'CANCELLED'}
        
        # Create a new material
        material = bpy.data.materials.new(name="ImportedMaterial")
        material.use_nodes = True
        
        # Initialize Principled BSDF node
        bsdf = None
        for node in material.node_tree.nodes:
            if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
                bsdf = node
                break
        if bsdf is None:
            bsdf = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        
        # Create an attribute node
        attribute_node = material.node_tree.nodes.new('ShaderNodeVertexColor')
        if obj.data.vertex_colors:
            attribute_node.layer_name = obj.data.vertex_colors[0].name
        else:
            attribute_node.layer_name = "Color"
        
        # Assign the material to the object
        material.node_tree.links.new(attribute_node.outputs['Color'], bsdf.inputs['Base Color'])
        
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    
        return {'FINISHED'}

class GeneratorPanel(bpy.types.Panel):
    bl_label = "Autosculptor"
    bl_idname = "OBJECT_PT_autosculptor_model_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Autosculptor'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        autosculptor_props = scene.autosculptor_props
        
        layout.prop(autosculptor_props, "prompt")
        layout.prop(autosculptor_props, "seed")
        layout.prop(autosculptor_props, "random_seed")
        layout.prop(autosculptor_props, "guidance_scale")
        layout.prop(autosculptor_props, "num_inference_steps")
        layout.prop(autosculptor_props, "model_type")
        layout.operator("object.autosculptor_model_generator")

class GeneratorProperties(bpy.types.PropertyGroup):
    prompt: bpy.props.StringProperty(name="Prompt")
    seed: bpy.props.IntProperty(name="Seed", default=0, min=0, max=2147483647)
    random_seed: bpy.props.BoolProperty(name="Random Seed", default=True)
    guidance_scale: bpy.props.IntProperty(name="Guidance Scale", default=15, min=1, max=20)
    num_inference_steps: bpy.props.IntProperty(name="Inference Steps", default=64, min=2, max=100)
    model_type: bpy.props.EnumProperty(
        name="Model",
        items=[
            ("shape-e-text", "Shap-E", "hysts/Shap-E")
        ],
        default="shape-e-text"
    )

def register():
    bpy.utils.register_class(GeneratorOperator)
    bpy.utils.register_class(GeneratorPanel)
    bpy.utils.register_class(GeneratorProperties)
    bpy.types.Scene.autosculptor_props = bpy.props.PointerProperty(type=GeneratorProperties)

def unregister():
    bpy.utils.unregister_class(GeneratorOperator)
    bpy.utils.unregister_class(GeneratorPanel)
    bpy.utils.unregister_class(GeneratorProperties)
    del bpy.types.Scene.autosculptor_props

if __name__ == "__main__":
    register()