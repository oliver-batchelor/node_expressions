from __future__ import annotations

import bpy

import inspect
import re

from numbers import Number
from collections.abc import Sequence
from collections import OrderedDict

from structs.struct import struct
from node.arrange import arrange_nodes

from typing import List, Callable, Tuple, Any, Union, Optional
import itertools



def converts_vector(v):
    return isinstance(v, Vector) or isinstance(v, Vector) \
        or isinstance(v, Number) or isinstance(v, tuple)



class Builder:
    current = None

    def __init__(self, node_tree):
        assert isinstance(node_tree, bpy.types.NodeTree)
        self.node_tree = node_tree
        self.created_nodes = []

    def new(self, node_type):
        node = self.node_tree.nodes.new(node_type)
        self.created_nodes.append(node)
        return node


    def __enter__(self):
        self.previous = Builder.current
        Builder.current = self


    def __exit__(self, type, value, traceback):
        Builder.current = self.previous

def node_builder(node_tree):
    return Builder(node_tree)


def has_builder(f):
    def wrapper(*args, **kwargs):

        assert Builder.current is not None, "no active node environment, please use in 'with(node_builder):' block"
        return f(Builder.current, *args, **kwargs)
    return wrapper



def parameter_name(s):
    s = s.lower().strip()               # lower case, strip whitespace
    s = re.sub('[\\s\\t\\n]+', '_', s)  # spaces to underscores
    s = re.sub('[^0-9a-zA-Z_]', '', s)  # delete invalid characters

    return s

# def socket_parameter(socket):
#     name = parameter_name(socket.identifier)
#     value_type=value_types[socket.type]
    
#     return inspect.Parameter(name, 
#         kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, 
#         default=value_type.default_value(socket.default_value), 
#         annotation=Optional[value_type.annotation()])   


# def template_node(node_type):

#     sockets = [input for input in node.inputs if input.enabled]
#     signature = inspect.Signature(parameters = [socket_parameter(input) for input in sockets])

#     def f(*args, **kwargs):
#         args = signature.bind(args, kwargs)
#         args.apply_defaults()

#         assert len(args.arguments) == len(sockets)
#         for v in zip(sockets, args.arguments.values(), signature.parameters):
#             pass
#             # print(socket, k, v, param)

#     return f


# def template_parameter(template:bpy.types.NodeInternalSocketTemplate):
    
#     name = parameter_name(template.identifier)
#     value_type=value_types[template.type]
    
#     return inspect.Parameter(name, 
#         kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, 
#         default=None, 
#         annotation=Optional[value_type.annotation()])   


# def node_templates(node_type):
#     templates = []
#     for i in itertools.count():
#         template = node_type.input_template(i)
#         if template is None:
#             return templates
#         elif template.type in value_types:
#             templates.append(template)    

# @has_builder
# def template_node(builder, node_type, **node_params):
#     templates = node_templates(node_type)
        
#     input_params = [template_parameter(template) for template in templates]
#     signature = inspect.Signature(input_params)

#     def f(*args, **kwargs):
#         args = signature.bind(*args, **kwargs)
#         args.apply_defaults()

#         node = builder.new(node_type.bl_rna.identifier)
#         for k, v in node_params.items():
#             node[k] = v

#         assert len(args.arguments) == len(templates)
#         for v in zip(templates, args.arguments.values(), signature.parameters):
#             pass
#             # print(socket, k, v, param)

#     return f


def vector_math(op):
    return template_node(bpy.types.ShaderNodeVectorMath, op=op)

class Node:
    def __init__(self, node):
        self._node = node

        self._outputs = [value_types[output.type](output) for output in node.outputs 
            if output.type in value_types and output.enabled] 

        self._named = {value.socket.name: value for value in self._outputs}

    def __getattr__(self, key):
        return self._named[key]

    def __getitem__(self, index):
        return self._outputs[index] 

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


class Float(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Float'

    @staticmethod
    def annotation():
         return Union[float, Float]

    @staticmethod
    def default_value(v):
        return float(v)



class Vector(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Vector'

    @staticmethod
    def annotation():
        scalar = Float.annotation()
        return Union[scalar, Tuple[scalar, scalar, scalar], Vector]

    @staticmethod
    def default_value(v):
        assert len(v) == 3
        return tuple(v)

    def __add__(self, other):
        print("baz")
        return vector_math('ADD')(self, (4, "TURPTLE"))

    def __radd__(self, other):
        return vector_math('ADD')(other, self)




class Int(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Int'

    @staticmethod
    def annotation():
         return Union[int, Int]

    @staticmethod
    def default_value(v):
        return int(v)         


class Bool(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Bool'

    @staticmethod
    def annotation():
         return Union[bool, Bool]    

    @staticmethod
    def default_value(v):
        return bool(v)  

class String(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    @staticmethod
    def annotation():
         return Union[str, String]    

    @staticmethod
    def default_value(v):
        return str(v)  


class Color(Value):
    def __init__(self, socket:int=0):
        super().__init__(socket)
         
    type = 'Color'
    
    @staticmethod
    def annotation():
        scalar = Float.annotation()
        return Union[scalar, Tuple[scalar, scalar, scalar, scalar], Color]

    @staticmethod
    def default_value(v):
        assert len(v) == 4
        return tuple(v)

value_types = {
    'VALUE':Float, 
    'INT':Int, 
    'BOOLEAN':Bool, 
    'VECTOR':Vector, 
    'STRING':String, 
    'RGBA':Color
}

socket_types = {
    'Float':'NodeSocketStandard',
    'Int':'NodeSocketInt', 
    'Bool':'NodeSocketBool', 
    'Vector':'NodeSocketVector', 
    'String':'NodeSocketString', 
    'Color':'NodeSocketColor'
}

    

def make_param(group_inputs, param:inspect.Parameter):
    assert param.annotation is not None, "expected type annotation on input parameters"
    assert issubclass(param.annotation, Value), "unsupported input type: " + str(param.annotation.type)

    socket_type = socket_types[param.annotation.type]
    return group_inputs.inputs.new(socket_type, param.name)



def build_group(f:Callable, name:str='Group', nodes_type:str='ShaderNodeTree'):
    node_tree = bpy.data.node_groups.new(name, nodes_type)
    with(node_builder(node_tree)):

        sig = inspect.signature(f)
        for param in sig.parameters.values():
            param = make_param(node_tree, param)

        node_inputs = node_tree.nodes.new('NodeGroupInput')
        node_outputs = node_tree.nodes.new('NodeGroupOutput')

        input_node = Node(node_inputs)
        outputs = f(*input_node)



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
