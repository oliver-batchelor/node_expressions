import sys
sys.path.append('.')  

import bpy
# from node.expression import Vector, import_group, import_nodes

from node.expression import build_group, Vector


if __name__ == "__main__":

    
    def foo(a : Vector, b : Vector):
        c =  a + b
        return c + a

    group = build_group(foo)
    



