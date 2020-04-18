from __future__ import annotations

import bpy

import inspect
import re


from collections.abc import Sequence
from collections import OrderedDict

from cached_property import cached_property

from typing import List, Callable, Tuple, Any, Union, Optional
import itertools
from functools import partial

from .value import value_types, Value


class Namespace:
    def __init__(self, d):
        self.__dict__.update(d)

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return self.__dict__.__repr__()

def namespace(**d):
    return Namespace(d)



def node_inputs(node_type):
    inputs = {}
    for i in itertools.count():
        template = node_type.input_template(i)
        if template is None:
            return inputs
        elif template.type in value_types:
            k = parameter_name(template.identifier)
            inputs[k] = namespace(
                index = i,
                identifier = template.identifier,
                type = value_types[template.type]
            )


def node_properties(node_type):
    def prop(p):
        return namespace(
            name = p.name,
            type = p.type,
            options = [item.name for item in p.enum_items]\
                if isinstance(p, bpy.types.EnumProperty) else []
        )


    rna = node_type.bl_rna
    properties = {parameter_name(p.name):prop(p) for p in rna.properties 
        if not p.is_readonly}

    return properties


def node_desc(node_type):
    return namespace(
        type=node_type, 
        inputs = node_inputs(node_type), 
        properties=node_properties(node_type),
    )

def node_subtypes(base_node):
    d = {}
    prefix = base_node.__name__

    for type_name in dir(bpy.types):
        t = getattr(bpy.types, type_name)
        
        has_sockets = hasattr(t, 'input_template') or hasattr(t, 'output_template')
        if issubclass(t, base_node) and has_sockets:
              name = type_name[len(prefix):]
              d[name] = node_desc(t)

    return d

def node_builders(builder, node_descs):
    d = {}
    for k, desc in node_descs.items():

        node_builder = NodeBuilder(builder, desc)
        operations = desc.operations['operation'].options \
             if 'operation' in desc.operations else []

        # if the node type has many operations, present them as a Namespace to the user
        if len(operations) > 1:
            d = {parameter_name(operation):node_builder.set(operation=operation) 
                for operation in desc.operations}
            node_builder = Namespace(d)        

        d[parameter_name(k)] = node_builder

    return Namespace(d)

class TreeType:
    def __init__(self, type):
        self.type = type
        self._node_builders = None

    @cached_property
    def nodes(self):
        return node_subtypes(self.type)

    def node_builders(self, builder):
        if self._node_builders is None: 
            self._node_builders = node_builders(builder, self.nodes)

        return self._node_builders

node_tree_types = dict(
    SHADER=TreeType(bpy.types.ShaderNode),   
    COMPOSITOR=TreeType(bpy.types.CompositorNode),
    TEXTURE=TreeType(bpy.types.TextureNode),
)
 
class TreeBuilder:

    def __init__(self, node_tree):
        assert isinstance(node_tree, bpy.types.NodeTree)
        self.node_tree = node_tree
        self.created_nodes = []

        self.tree_type = node_tree_types[node_tree.type]
        self.nodes = self.tree_type.node_builders(self)


    def connect(self, value, socket):
        return value_types[socket.type].connect(self, value, socket)
        
    def _new_node(self, node_type, properties):
        node = self.node_tree.nodes.new(self.tree_type.prefix + node_type)

        for k, v in properties.items():
            assert getattr(node, k) is not None, "node {} has no property {}".format(node.type, k)
            setattr(node, k, v)

        self.created_nodes.append(node)
        return node

    def _new_link(self, value, input):
        return self.node_tree.links.new(value.socket, input)





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
        return self.node.type + " " + self._named.__repr__()

    def __len__(self):
        return len(self._outputs)

    @staticmethod
    def connect(builder, v, socket):
        raise NotImplementedError


def wrap_node(node):
    assert isinstance(node, bpy.types.Node)
    wrapper = Node(node)

    if len(wrapper) == 1:
        return wrapper[0]
    else:
        return wrapper


def wrap_exceptions(f):

    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except TypeError as e:
            message = e.args[0]
            raise TypeError(message) from None
    
    return inner




class NodeBuilder:

    def __init__(self, builder, node_desc, properties={}):

        self.builder = builder
        self.desc = node_desc
        self.properties = properties

    @property
    def node_type(self):
        return self.desc.type.name

    def set(self, **properties):

        updated = self.properties.copy()
        for k, v in properties.items():
            if k not in self.desc.properties:
                raise TypeError('node {} has no property {}'.format(self.node_type, k))

            updated[k] = v

        return NodeBuilder(self.builder, self.desc, updated)


    def __call__(self, *args, **kwargs):
        try:
            node = self.builder._new_node(self.node_type, self.properties)

            sockets = [input for input in node.inputs if input.enabled]
            signature = inspect.Signature(parameters = [socket_parameter(input) for input in sockets])

            args = signature.bind(*args, **kwargs)
            args.apply_defaults()

            assert len(args.arguments) == len(sockets)
            for socket, (param_name, value) in zip(sockets, args.arguments.items()): 
                try:
                    self.builder.connect(value, socket)
                except TypeError as e:
                    raise TypeError("{}.{} - {}"\
                        .format(self.node_type,  param_name, e.args[0]))  
            return wrap_node(node)
        
        except TypeError as e:
            raise TypeError(e.args[0]) from None





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
    assert param.annotation is not None, "expected type annotation on input parameters"
    assert issubclass(param.annotation, Value), "unsupported input type: " + str(param.annotation.type)

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

    builder = TreeBuilder(node_tree)

    sig = inspect.signature(f)
    for param in sig.parameters.values():
        param = make_param(node_tree, param)

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
        raise TypeError("build_group: invalid output type")

    return node_tree
 
