import bpy

def make_plane(name, size, material=None):
    bpy.ops.mesh.primitive_plane_add(size=size)
    plane = bpy.context.active_object
    plane.name = name

    if material is not None:
        plane.data.materials.append(material)

    return plane

def make_grid(name, size, subdivisions=(256, 256), material=None):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=subdivisions[0],
    y_subdivisions=subdivisions[1], size=size)
    grid = bpy.context.active_object
    grid.name = name

    if material is not None:
        grid.data.materials.append(material)

    return grid

def adaptive_plane(name, size, material):
    plane = make_plane(name, size, material)

    subsurf = plane.modifiers.new("subdivision", type="SUBSURF")
    subsurf.subdivision_type = 'SIMPLE'
    plane.cycles.use_adaptive_subdivision = True
    plane.cycles.dicing_rate = 1.5

    return plane


def node_material(name, displacement='BOTH'):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True

    material.cycles.displacement_method = displacement

    for node in material.node_tree.nodes:
        material.node_tree.nodes.remove(node)

    return material