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

    def new(self, node_type, **node_params):
        node = self.node_tree.nodes.new(node_type)
        for k, v in node_params.items():
            node[k] = v

        self.created_nodes.append(node)
        return node

    def connect(self, value, socket):
        return value_types[socket.type].connect(self, value, socket)
        
    def link(self, value, input):
        return self.node_tree.links.new(value.socket, input)

    def __enter__(self):
        self.previous = Builder.current
        Builder.current = self

    def __exit__(self, type, value, traceback):
        if traceback:
            for node in self.created_nodes:
                self.node_tree.nodes.remove(node)
        else:
            arrange_nodes(self.node_tree, target_nodes=self.created_nodes)


        Builder.current = self.previous

def graph_builder(node_tree):
    return Builder(node_tree)


def has_builder(f):
    def wrapper(*args, **kwargs):
        assert Builder.current is not None, "no active node environment, please use in 'with(graph_builder):' block"
        return f(Builder.current, *args, **kwargs)
    return wrapper



def parameter_name(s):
    s = s.lower().strip()               # lower case, strip whitespace
    s = re.sub('[\\s\\t\\n]+', '_', s)  # spaces to underscores
    s = re.sub('[^0-9a-zA-Z_]', '', s)  # delete invalid characters

    return s

def socket_parameter(socket):
    name = parameter_name(socket.identifier)
    value_type=value_types[socket.type]
    
    return inspect.Parameter(name, 
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, 
        default=value_type.default_value(socket.default_value), 
        annotation=value_type.annotation())   

@has_builder
def node_builder(builder, node_type, **node_params):
    def f(*args, **kwargs):
        node = builder.new(node_type, **node_params)

        sockets = [input for input in node.inputs if input.enabled]
        signature = inspect.Signature(parameters = [socket_parameter(input) for input in sockets])

        args = signature.bind(*args, **kwargs)
        args.apply_defaults()

        assert len(args.arguments) == len(sockets)
        for socket, value in zip(sockets, args.arguments.values()):
            builder.connect(value, socket)

        return Node(node)

    return f



def vector_math(op):
    return node_builder('ShaderNodeVectorMath', operation=op)


class Node:
    def __init__(self, node):
        self._node = node

        self._outputs = [value_types[output.type](output) for output in node.outputs 
            if output.type in value_types and output.enabled] 

        self._named = {parameter_name(value.socket.identifier): value for value in self._outputs}

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

    @staticmethod
    def connect(builder, v, socket):
        if isinstance(v, Vector):
            builder.link(v, socket)
        else:
            assert False, "Vector.connect: unexpected type: " + str(type(v))

    def __add__(self, other):
        return vector_math('ADD')(self, other).vector

    def __radd__(self, other):
        return vector_math('ADD')(other, self).vector




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

    

def make_param(node_tree, param:inspect.Parameter):
    assert param.annotation is not None, "expected type annotation on input parameters"
    assert issubclass(param.annotation, Value), "unsupported input type: " + str(param.annotation.type)

    socket_type = socket_types[param.annotation.type]
    return node_tree.inputs.new(socket_type, param.name)



def build_group(f:Callable, name:str='Group', nodes_type:str='ShaderNodeTree'):
    node_tree = bpy.data.node_groups.new(name, nodes_type)

    builder = graph_builder(node_tree)
    with(builder):

        sig = inspect.signature(f)
        for param in sig.parameters.values():
            param = make_param(node_tree, param)

        node_inputs = builder.new('NodeGroupInput')
        node_outputs = builder.new('NodeGroupOutput')

        input_node = Node(node_inputs)
        outputs = f(*input_node)
    
        def add_output(value, name='value'):
            node_tree.outputs.new(socket_types[value.type], name)
            builder.connect(value, node_outputs.inputs[name])

        if isinstance(outputs, dict):
            for k, value in outputs.items():
                add_output(value, k)
        elif isinstance(outputs, Value):
            add_output(outputs)
        else:
            assert False, "invalid output type"
 
    return node_tree
 
