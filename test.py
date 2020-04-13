import sys
sys.path.append('.')  

import bpy
# from node.expression import Vector, import_group, import_nodes

from node.expression import build_group, Vector, Color


if __name__ == "__main__":

    
    def foo(a : Vector, b : Vector, test:Color=(1, 0, 0, 1)):
        c =  a + b
        return dict(bar = c + a, baz = c + c)

    group = build_group(foo)
    



