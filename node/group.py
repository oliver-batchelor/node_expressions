# pylint: disable=E1101,E0401
from __future__ import annotations

import bpy
import inspect
from typing import List, Callable, Tuple, Any, Union, Optional

from .value import value_types, Value
from .util import typename, assert_type
from .expression import NodeTree, NodeSet



socket_types = {
    'Float':'NodeSocketFloat',
    'Int':'NodeSocketInt', 
    'Bool':'NodeSocketBool', 
    'Vector':'NodeSocketVector', 
    'String':'NodeSocketString', 
    'Shader':'NodeSocketShader', 
    'Color':'NodeSocketColor'
}

    

def make_param(node_tree, param:inspect.Parameter):
    if not issubclass(param.annotation, Value):
        raise TypeError("unsupported input type: " + str(param.annotation.type))

    socket_type = socket_types[param.annotation.type]
    socket = node_tree.inputs.new(socket_type, param.name)

    default = param.default
    if default is not inspect.Parameter.empty:
        socket.default_value = default

    return socket



def build_group(f:Callable, name:str='Group', nodes_type:str='ShaderNodeTree'):
    node_tree = bpy.data.node_groups.new(name, nodes_type)

    node_inputs = node_tree.nodes.new('NodeGroupInput')
    node_outputs = node_tree.nodes.new('NodeGroupOutput')

    tree = NodeTree(node_tree)

    sig = inspect.signature(f)
    if len(sig.parameters) == 0:
        raise ValueError("can't build group with no parameters")

    parameters = list(sig.parameters.values())
    for param in parameters: 
        if param.annotation is None:
            raise TypeError("expected type annotation on input parameter: " + str(param.name))

    node_param = [] 
    if parameters[0].annotation is NodeSet:
        node_param = [tree.nodes]
        parameters = parameters[1:]

    for param in parameters:
        param = make_param(node_tree, param)

    input_node = tree.import_node(node_inputs)
    outputs = f(*node_param, *input_node)

    def add_output(value, name='value'):
        node_tree.outputs.new(socket_types[value.type], name)
        tree.connect(value, node_outputs.inputs[name])

    if isinstance(outputs, dict):
        for k, value in outputs.items():
            add_output(value, k)
    elif isinstance(outputs, Value):
        add_output(outputs)
    else:
        raise TypeError("build_group: invalid output type")

    return node_tree
 