import bpy
import sys
from operator import itemgetter

sys.path.append('.')  

import node.expression as exp
from node.shader import math, tex_coord, Vector, Color

import node


def open_nodes(context):
    screen = context.screen
    areas = [(area, area.width * area.height) for area in screen.areas
                if area != context.area]
    if len(areas):
        maxarea, a = max(areas, key=itemgetter(1))
        maxarea.type = 'NODE_EDITOR'
    else:
        #split areas
        direction = 'HORIZONTAL' if context.area.width < context.area.height else 'VERTICAL'
        bpy.ops.screen.area_split(direction=direction)
        screen.areas[-1].type = 'NODE_EDITOR'


def node_material(name):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True

    for node in material.node_tree.nodes:
        material.node_tree.nodes.remove(node)

    return material


def make_plane(name, size, material=None):
    bpy.ops.mesh.primitive_plane_add(size=size)
    plane = bpy.context.active_object
    plane.name = name

    if material is not None:
        plane.data.materials.append(material)

    return plane


def example(): 
    def foo(a : Vector, b : Vector, test:Color=(1, 0, 0, 1)):
        k = a.x + a.y

        c = b.map(math.sine)
        uv = tex_coord().uv
        
        return dict(bar = -k // 3, baz = c + uv)

    group = node.group.build(foo)
    open_nodes(bpy.context)



if __name__ == "__main__":
    example()







