import bpy
import sys
from operator import itemgetter

sys.path.append('.')  

# from node.expression import Vector, import_group, import_nodes

from node.group import build_group
from node.value import Float, Bool, Vector, Color
from node.expression import NodeSet


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

if __name__ == "__main__":

    
    def foo(nodes : NodeSet, a : Vector, b : Vector, test:Color=(1, 0, 0, 1)):
        k = a.x + a.y

        c = b.map(nodes.math.sine)

        print(nodes.math.sine)
        
        return dict(bar = -k // 3, baz = c + c)

    group = build_group(foo)
    open_nodes(bpy.context)







