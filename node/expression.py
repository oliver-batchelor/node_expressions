from __future__ import annotations

import bpy

import inspect
from numbers import Number
from collections.abc import Sequence
from collections import OrderedDict

from structs.struct import struct
from node.arrange import arrange_nodes

from typing import List, Callable, Tuple, Any



def converts_vector(v):
    return isinstance(v, Vector) or isinstance(v, Vector) \
        or isinstance(v, Number) or isinstance(v, tuple)




class NodeTree:
    current = None

    def __init__(self, tree):
        self.tree = tree

    def __enter__(self):
        self.previous = current
        self.current = self.tree

    def __exit__(self):
        self.current = self.previous

def node_tree(node_tree):
    return NodeTree(node_tree)

    
def vector_math(op):
        
    node = current_tree.nodes.new('ShaderNodeVectorMath')
    node.operation = op




#         lhs, rhs = [value.connect(ctx) for value in (self.lhs, self.rhs)]
  
#         ctx.node_tree.links.new(lhs, node.inputs[0])
#         ctx.node_tree.links.new(rhs, node.inputs[1])

#         return node.outputs[0]


#     def __repr__(self):
#         return "vector-{}".format(self.op)


def wrap_node(node):
    inputs = wrap_input(input) for input in node.inputs

    outputs = Outputs(node)  




def wrap_output(socket):
    value = value_types[socket.type]
    return value(socket)


class Outputs:
    def __init__(self, node):
        self._node = node

        self._outputs = [wrap_output(output) for output in node.outputs 
            if output.type in value_types] 

        self._named = {value.socket.name: value for value in self._outputs}

    def __getattr__(self, index):
        return self._named[index]

    def __getitem__(self, key):
        return self._named[key] 

    def __iter__(self):
        return self._outputs.__iter__()

    def __repr__(self):
        return self._named.__repr__()


class Value:
    def __init__(self, socket=0):
        super().__init__()
        self.socket = socket
    
    @property
    def type(self):
        return NotImplementedError
       
    def __repr__(self):
        return self.type


class Vector(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Vector'

    def __add__(self, other):
        return vector_math('ADD')(self, other)

    def __radd__(self, other):
        return vector_math('ADD')(other, self)


class Float(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Float'

class Int(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Int'


class Bool(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Bool'


class String(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         



class Color(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Color'


value_types = {
    'VALUE':Float, 
    'INT':Int, 
    'BOOLEAN':Bool, 
    'VECTOR':Vector, 
    'STRING':String, 
    'RGBA':Color
}

socket_type = {
    'Vector':'NodeSocketVector', 
    'Int':'NodeSocketInt', 
    'Bool':'NodeSocketBool', 
    'String':'NodeSocketString', 
    'Color':'NodeSocketColor'
}
    

def make_param(group_inputs, param:inspect.Parameter):
    assert param.annotation is not None, "expected type annotation on input parameters"
    assert issubclass(param.annotation, Value), "unsupported input type: " + str(param.annotation.type)

    param_type = socket_type[param.annotation.type]
    return group_inputs.inputs.new(param_type, param.name)



def build_group(f:Callable, name:str='Group', nodes_type:str='ShaderNodeTree'):
    node_tree = bpy.data.node_groups.new(name, nodes_type)

    sig = inspect.signature(f)
    for param in sig.parameters.values():
        param = make_param(node_tree, param)

    node_inputs = node_tree.nodes.new('NodeGroupInput')
    node_outputs = node_tree.nodes.new('NodeGroupOutput')

    input_node = Node(node_inputs)
    outputs = f(*input_node)
    print(outputs)


# def generate_group(name:str='Group', nodes_type:str='ShaderNodeTree') -> bpy.types.NodeGroup:
#     group = bpy.data.node_groups.new(name, nodes_type)

#     group_inputs = group.nodes.new('NodeGroupInput')
#     for inp in inputs:
#         group.inputs.new(node_type(inp), inp.node.name)

#     group_outputs = group.nodes.new('NodeGroupOutput')

#     ctx = struct(
#         nodes = {},
#         node_tree = group,
#         inputs = group_inputs.outputs
#     )

 
#     def add_output(output, name='Value'):
#         assert isinstance(output, Value)
#         inp_socket = output.connect(ctx)

#         out_socket = group_outputs.inputs.new(node_type(output), name)
#         group.links.new(inp_socket, out_socket)

#     if isinstance(outputs, Value):
#         add_output(outputs)

#     elif isinstance(outputs, list):
#         for output in outputs:
#             if output is tuple:
#                 add_output(output[1], name=output[0])
#             else:
#                 add_output(output)
#     else:
#         assert False, "unexpected output type {}" + str(type(output))
 
 
#     arrange_nodes(group)
#     return group
        
# def import_group(f : Callable, name:str, node_type:str='ShaderNodeTree') -> bpy.types.NodeGroup:
#     inputs, outputs = build_graph(f)
#     return generate_group(inputs, outputs, name, node_type)
