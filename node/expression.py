# pylint: disable=E1101,E0401
from __future__ import annotations

import bpy

import inspect
import re
import types
import sys

from collections.abc import Sequence
from collections import OrderedDict

from cached_property import cached_property

from numbers import Number
from typing import List, Callable, Tuple, Any, Union, Optional
import itertools
from functools import partial

from .util import typename, assert_type, namespace

import importlib


value_types = ['VALUE', 'INT', 'BOOLEAN', 'VECTOR', 'STRING', 'SHADER', 'RGBA']

def node_template(node_type, property='input_template'):
    inputs = {}
    for i in itertools.count():
        template = getattr(node_type, property)(i)
        if template is None:
            return inputs
        elif template.type in value_types:
            k = parameter_name(template.name)
            inputs[k] = namespace(property,
                index = i,
                name = template.name,
                type = template.type
            )



def node_properties(node_type, common = {}):
    def prop(p):
        name = parameter_name(p.identifier)

        return namespace("property",
            property_name = p.name,
            name = name,
            type = p.type,
            options = [(item.name, item.identifier) for item in p.enum_items]\
                if isinstance(p, bpy.types.EnumProperty) else [],
            is_common = name in common
        )

    rna = node_type.bl_rna
    properties = [prop(p) for p in rna.properties 
        if not p.is_readonly]

    return {p.name:p for p in properties}


def node_subclasses(base_node, types=bpy.types):
    d = {}
    prefix = base_node.__name__
    common_properties = node_properties(base_node)

    def node_desc(node_type):
        return namespace("node description",
            name = type_name[len(prefix):],
            type=node_type, 
            inputs = node_template(node_type, 'input_template'), 
            outputs = node_template(node_type, 'output_template'), 
            properties=node_properties(node_type, common_properties),
        )    

    for type_name in dir(types):
        t = getattr(types, type_name)
        
        has_sockets = hasattr(t, 'input_template') or hasattr(t, 'output_template')
        if issubclass(t, base_node) and has_sockets:
              desc = node_desc(t)
              d[desc.name] = desc

    return d


def make_submodule(module, name):
    submodule = types.ModuleType(name)
    sys.modules[module.__name__ + "." + name] = submodule

    return submodule

def add_node_module(module, node_type):
    tree_type = node_tree_descs[node_type]
    
    def make_enumerations(node_builder, key):
        options = node_builder.properties[key].options

        submodule = make_submodule(module, key)
        for name, identifier in options:
            builder = node_builder.set(**{key:identifier.upper()})
            setattr(submodule, parameter_name(name), builder)

        return submodule
  
    def make_builder(k, desc):
        node_builder = NodeBuilder(desc)
        for k in ['operation', 'blend_type']:
           if k in desc.properties:
                return make_enumerations(node_builder, k)
        return node_builder

    for k, desc in tree_type.node_descriptions.items():
        setattr(module, parameter_name(k), make_builder(k, desc))

    return module

  

class TreeDesc:
    def __init__(self, type, module, tree_type):
        self.type = type
        self.module = module
        self.tree_type = tree_type

    @cached_property
    def node_descriptions(self):
        return node_subclasses(self.type)

    @property
    def name(self):
        return parameter_name(typename(self.type))

    @cached_property
    def nodes(self):
        return importlib.import_module(self.module)
        

node_tree_descs = dict(
    SHADER=TreeDesc(bpy.types.ShaderNode, 'node.shader', 'ShaderNodeTree'),   
    COMPOSITING=TreeDesc(bpy.types.CompositorNode, 'node.compositor', 'CompositorNodeTree'),
    TEXTURE=TreeDesc(bpy.types.TextureNode, 'node.texture', 'TextureNodeTree'),
)


class NodeContext:
    current = None

    def __init__(self, node_tree):
        assert isinstance(node_tree, bpy.types.NodeTree)
        self.node_tree = node_tree
        self.created_nodes = []     
        self.desc = node_tree_descs[node_tree.type]

        self.previous = None

    def __enter__(self):
        self.previous = NodeContext.current
        NodeContext.current = self

    def __exit__(self, type, value, traceback):
        NodeContext.current = self.previous
        self.previous = None

    @staticmethod
    def active():
        if NodeContext.current is None:
            raise AttributeError("no active node context, use 'with(node_tree(mat.node_tree))' or create a node group")
        
        return NodeContext.current

    def import_group(self, group):
        assert isinstance(group, type(self.node_tree))
        return self.nodes.group.set(node_tree=group)

    @property
    def nodes(self):
        return self.desc.nodes

    @property
    def value_types(self):
        return self.nodes._value_types

    def value_type(self, type_name):
        return self.value_types[type_name]
       
    def _new_node(self, node_type, bound_properties):
        node = self.node_tree.nodes.new(node_type)           

        for k, v in bound_properties.items():
            assert hasattr(node, k), "node {} has no property {}".format(node.type, k)
            setattr(node, k, v)

        self.created_nodes.append(node)
        return node


    def _new_link(self, value, input):
        return self.node_tree.links.new(value.socket, input)

    def import_node(self, node):
        return Node(self, node)

    def remove(self, node):
        assert isinstance(node, Node)
        self.node_tree.nodes.remove(node._node)

    def activate(self, node):
        assert isinstance(node, Node)
        self.node_tree.nodes.active = node._node

def node_context():
    return NodeContext.active()
    
def import_group(group):
    return node_context().import_group(group)

def activate_node(node):
    return node_context().activate(node)

def node_tree(tree):
    return NodeContext(tree)

def remove_node(node):
    return node_context().remove(node)





    

def camel_to_snake(name):
  name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def parameter_name(s):
    s = s.strip()               # lower case, strip whitespace
    s = re.sub('[\\s\\t\\n]+', '', s)  # spaces to underscores
    s = re.sub('[^0-9a-zA-Z_]', '', s)  # delete invalid characters

    return camel_to_snake(s)

def socket_parameter(context, socket, name):
    value_type = context.value_type(socket.type)

    default = getattr(socket, 'default_value', None)
    
    return inspect.Parameter(name, 
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, 
        default=value_type.default_value(default), 
        annotation=value_type)   


class Node:
    def __init__(self, context, node):
        assert isinstance(node, bpy.types.Node)
        self._node = node

        value_types = context.value_types

        self._outputs = [value_types[output.type](output) for output in node.outputs 
            if output.type in value_types and output.enabled] 

        self._named = {parameter_name(value.socket.name): value for value in self._outputs}


    def mute(self, on):
        self._node.mute = on

    def items(self):
        return self._named.items()

    def __getattr__(self, key):
        return self._named[key]

    def __getitem__(self, index):
        return self._outputs[index] 

    def __iter__(self):
        return self._outputs.__iter__()

    def __repr__(self):
        return self._node.type + " " + self._named.__repr__()

    def __len__(self):
        return len(self._outputs)

def wrap_node(context, node):
    assert isinstance(node, bpy.types.Node)
    wrapper = Node(context, node)
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


def comma_sep(xs):
    return ", ".join(xs)


class NodeBuilder:
    def __init__(self, node_desc, bound_properties={}):
        self.desc = node_desc
        self.bound_properties = bound_properties

    def properties_help(self):
       return comma_sep(["{}:{}".format(k, p.type) 
            for k, p in self.desc.properties.items() if not p.is_common])        

    def __str__(self):      
        properties_set = comma_sep(["{}={}".format(k, v) for k, v in self.bound_properties.items()])

        inputs = comma_sep(["{}:{}".format(k, inp.type) 
            for k, inp in self.desc.inputs.items()])

        outputs = comma_sep(["{}:{}".format(k, output.type) 
            for k, output in self.desc.outputs.items()])

        return "{}({}):\n properties({})\n inputs({})\n outputs({})\n"\
            .format(self.desc.name, properties_set, self.properties_help(), inputs, outputs)

    def __repr__(self):
        return "NodeBuilder({})".format(self.desc.name)

    @property
    def properties(self):
        return self.desc.properties

    @property
    def inputs(self):
        return self.desc.inputs

    @property
    def outputs(self):
        return self.desc.outputs

    @property
    def node_type(self):
        return self.desc.type.__name__

    def set(self, **properties):
        updated = self.bound_properties.copy()

        for k, v in properties.items():
            if k not in self.desc.properties:
                help = self.properties_help()
                raise TypeError('node {} has no property {}\n{}'.format(self.node_type, k, help))

            prop = self.desc.properties[k]    
            updated[k] = v
        return NodeBuilder(self.desc, updated)


    def __call__(self, *args, **kwargs):
        try:
            context = node_context()
            node = context._new_node(self.node_type, self.bound_properties)
            return call_node(context, parameter_name(self.desc.name), node, *args, **kwargs)
        except TypeError as e:
            error = e.args[0]
            raise TypeError(error) from None
        

def numbered(name, names):
    i = 1
    modified = name
    while modified in names:
        modified = name + str(i)
        i += 1
    return modified

def number_duplicates(names):
    result = []
    for name in names:
        result.append(numbered(name, result))
    return result


def describe_arg(i, param):
    return "({}) {}:{} = {}".format(i, param.name, param.annotation.__name__, param.default)

def call_node(context, node_name, node, *args, **kwargs):
    context = node_context()

    sockets = [input for input in node.inputs if input.enabled]
    names = number_duplicates([parameter_name(input.name) for input in sockets])

    signature = inspect.Signature(parameters = 
        [socket_parameter(context, input, name) for name, input in zip(names, sockets)])

    try:
        args = signature.bind(*args, **kwargs)
        args.apply_defaults()

        assert len(args.arguments) == len(sockets)
        for i, socket, (param_name, value) in zip(itertools.count(), sockets, args.arguments.items()): 
            try:
                context.value_type(socket.type).connect(context, value, socket)
            except TypeError as e:
                raise TypeError("argument {} '{}': {}".format(i + 1,  param_name, e.args[0]))
        return wrap_node(context, node)

    except TypeError as e:
        arg_help = [describe_arg(i + 1, param) for i, param in enumerate(signature.parameters.values())]
        func_help = "{}({})".format(node_name, ", ".join(names))
        raise TypeError("{}\n{}\n{}".format(e.args[0], func_help, "\n".join(arg_help)))  



