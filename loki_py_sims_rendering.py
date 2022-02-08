# @author gold24park (loki_py)
import bpy

# 여기에 import된 dae의 이름을 넣어주세요.
# Put the imported dae object's name here.
# - Scene > Collection 아래의 이름입니다.
object_name="rig" 

def find_mesh_object(obj_name):
    obj = bpy.data.objects[obj_name]
    for o in bpy.data.objects:
        if o.type == 'MESH' and obj in [m.object for m in o.modifiers if m.type == 'ARMATURE']:
            return o
    return None

mesh = find_mesh_object(object_name).data

if len(mesh.materials) == 0:
    raise Exception("no materials")

# find material nodes 
material = mesh.materials[0]   
nodes = material.node_tree.nodes


nodes_to_remove = []
n_base_color = None
n_specular = None

for node in nodes:
    if "Image Texture" in node.name and "diffuse" in node.image.name:
        n_base_color = node
    elif "Image Texture" in node.name and "specular" in node.image.name:
        n_specular = node
    if node.name == "Mix Shader" or node.name == "Transparent BSDF":
        nodes_to_remove.append(node)

# clear existing nodes
for node in nodes_to_remove:
    material.node_tree.nodes.remove(node)


n_principled_BSDF = nodes.get("Principled BSDF")
n_material_output = nodes.get("Material Output")
n_material_output.location = [500, n_material_output.location[1]]

# =================================
# [1] Specular
# =================================
# connect specular color to BSDF
specular_output = None
for output in n_specular.outputs:
    if output.name == "Color":
        specular_output = output
# link specular
material.node_tree.links.new(
    specular_output,
    n_principled_BSDF.inputs["Specular"]
)


# =================================
# [2] Mix shader
# =================================
# create mix shader
mix_shader = material.node_tree.nodes.new(type="ShaderNodeMixShader")
mix_shader_input = None

for input in mix_shader.inputs:
    # use last one
    if input.name == "Shader":
        mix_shader_input = input
    
# link mix shader
material.node_tree.links.new(
    n_principled_BSDF.outputs["BSDF"],
    mix_shader_input
)
material.node_tree.links.new(
    mix_shader.outputs["Shader"],
    n_material_output.inputs["Surface"]
)

# adjust location of mix shader
mix_shader.location = [300, n_material_output.location[1]]

# =================================
# [3] Transparent BSDF
# =================================
# create tbsdf
transparentBSDF = material.node_tree.nodes.new(type="ShaderNodeBsdfTransparent")
# link tbsdf
material.node_tree.links.new(
    transparentBSDF.outputs["BSDF"],
    mix_shader.inputs["Shader"]
)
transparentBSDF.location = [100, 400]

# =================================
# [4] Base Color
# =================================
material.node_tree.links.new(
    n_base_color.outputs["Alpha"],
    mix_shader.inputs["Fac"]
)

# set blend mode to hashed.
material.blend_method = 'HASHED'