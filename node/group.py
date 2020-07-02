# pylint: disable=E1101,E0401
from __future__ import annotations

import bpy
import inspect
from typing import List, Callable, Tuple, Any, Union, Optional

from .util import typename, assert_type
from .expression import NodeContext, Node, import_group
from .value import Value


socket_types = {
    'Float':'NodeSocketFloat',
    'Int':'NodeSocketInt', 
    'Bool':'NodeSocketBool', 
    'Vector':'NodeSocketVector', 
    'String':'NodeSocketString', 
    'Shader':'NodeSocketShader', 
    'Color':'NodeSocketColor'
}

    

def make_param(context, node_tree, param:inspect.Parameter):
    if param.annotation is inspect.Parameter.empty:
        raise TypeError("{}: required annotation for input parameter")

    if param.annotation not in context.value_types.values():
        raise TypeError("{}: unsupported input type '{}'".format(param.name, param.annotation))

    socket_type = socket_types[param.annotation.type]
    socket = node_tree.inputs.new(socket_type, param.name)

    default = param.default
    if default is not inspect.Parameter.empty:
        socket.default_value = default

    return socket



    
def build(f:Callable, name:str='Group', node_type:str='ShaderNodeTree'):
    node_tree = bpy.data.node_groups.new(name, node_type)

    node_inputs = node_tree.nodes.new('NodeGroupInput')
    node_outputs = node_tree.nodes.new('NodeGroupOutput')

    context = NodeContext(node_tree)

    sig = inspect.signature(f)
    for param in sig.parameters.values(): 
        if param.annotation is None:
            raise TypeError("expected type annotation on input parameter: " + str(param.name))

    for param in sig.parameters.values():
        make_param(context, node_tree, param)

    input_node = Node(context, node_inputs)

    with(context):
        outputs = f(*input_node)

        def add_output(value, name=None):
            if type(value) not in context.value_types.values():
                raise TypeError("output {}:, expected Value, got {}".format(name, typename(value)))

            name = name or typename(value)
            output = node_tree.outputs.new(socket_types[value.type], name)
            value.connect(context, value, node_outputs.inputs[name])

        if isinstance(outputs, dict):
            for k, value in outputs.items():
                add_output(value, k)
        elif isinstance(outputs, tuple):
            for i, value in enumerate(outputs):
                add_output(value, "output_{}".format(i + 1))
        elif isinstance(outputs, Value):
            add_output(outputs, "output")
        else:
            raise TypeError("group.build: invalid output type, expected (dict|Value|tuple), got " + typename(outputs))

    return node_tree
 

def function(f:Callable, name:str='Group', node_type:str='ShaderNodeTree'):
     group = build(f, name, node_type)
     return import_group(group)


def lazy(f:Callable, name, node_type:str='ShaderNodeTree'):
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    else:
        return build(f, name, node_type)

def lazy_function(f:Callable, name, node_type:str='ShaderNodeTree'):
    group = lazy(f, name, node_type)
    return import_group(group)

