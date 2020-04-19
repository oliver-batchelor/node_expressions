# pylint: disable=E1101,E0401
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
from .util import typename, assert_type

class Namespace:
    def __init__(self, d, name=None):
        self._name = name or "Namespace"
        self._values = d

    def __str__(self):
        attrs = ["{}:{}".format(k, v) for k, v in self._values.items()]
        return "{}: <{}>".format(self._name, ', '.join(attrs))

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, attr):
        value = self._values.get(attr)
        if value is None:
            raise AttributeError("{} has no attribute '{}'".format(self._name, attr))
        return value

    def keys(self):
        return self._values.keys()
       
def namespace(**d):
    return Namespace(d)


def node_template(node_type, property='input_template'):
    inputs = {}
    for i in itertools.count():
        template = getattr(node_type, property)(i)
        if template is None:
            return inputs
        elif template.type in value_types:
            k = parameter_name(template.identifier)
            inputs[k] = namespace(
                index = i,
                identifier = template.identifier,
                type = value_types[template.type]
            )


def node_properties(node_type, common = {}):
    def prop(p):

        name = parameter_name(p.name)
        return namespace(
            property_name = p.name,
            name = name,
            type = p.type,
            options = [item.name for item in p.enum_items]\
                if isinstance(p, bpy.types.EnumProperty) else [],
            is_common = name in common
        )

    rna = node_type.bl_rna
    properties = [prop(p) for p in rna.properties 
        if not p.is_readonly]

    return {p.name:p for p in properties}


def node_subclasses(base_node):
    d = {}
    prefix = base_node.__name__
    common_properties = node_properties(base_node)

    def node_desc(node_type):
        return namespace(
            name = type_name[len(prefix):],
            type=node_type, 
            inputs = node_template(node_type, 'input_template'), 
            outputs = node_template(node_type, 'output_template'), 
            properties=node_properties(node_type, common_properties),
        )    

    for type_name in dir(bpy.types):
        t = getattr(bpy.types, type_name)
        
        has_sockets = hasattr(t, 'input_template') or hasattr(t, 'output_template')
        if issubclass(t, base_node) and has_sockets:
              desc = node_desc(t)
              d[desc.name] = desc

    return d




class NodeSet:
    def __init__(self, tree, descs, name):
        self._tree = tree
        self._name = name
        
        self._descs = {parameter_name(k):desc for k, desc in descs.items()}
        self._builders = {}

    def _node_builder(self, k, desc):
        node_builder = NodeBuilder(self._tree, desc)
        operations = desc.properties['operation'].options \
                if 'operation' in desc.properties else []
        
        if len(operations) > 1:
            # if the node type has many operations, present them as a Namespace to the user
            ops = {parameter_name(operation):node_builder.set(operation=operation.upper()) 
                for operation in operations}
            node_builder = Namespace(ops, name=self._name + "." + k) 
            
        return node_builder
        
    def __getattr__(self, k):
        builder = self._builders.get(k)
        if builder is not None:
            return builder

        desc = self._descs.get(k)
        if desc is None:
            raise AttributeError("node set {} has no attribute '{}'".format(self._name, k))
              
        builder = self._node_builder(k, desc)
        self._builders[k] = builder
        return builder

    def __str__(self):
        return "{}: <{}>".format(self._name, ', '.join(self._descs.keys()))

    def __repr__(self):
        return self.__str__()

    def keys(self):
        return self._descs.keys()



class TreeType:
    def __init__(self, type):
        self.type = type

    @cached_property
    def nodes(self):
        return node_subclasses(self.type)

    @property
    def name(self):
        return parameter_name(typename(self.type))

        

node_tree_types = dict(
    SHADER=TreeType(bpy.types.ShaderNode),   
    COMPOSITOR=TreeType(bpy.types.CompositorNode),
    TEXTURE=TreeType(bpy.types.TextureNode),
)
 
class NodeTree:

    def __init__(self, node_tree):
        assert isinstance(node_tree, bpy.types.NodeTree)
        self.node_tree = node_tree
        self.created_nodes = []

        self.tree_type = node_tree_types[node_tree.type]

        self.name = parameter_name(self.tree_type.type.__name__)
        self.nodes = NodeSet(self, self.tree_type.nodes, name = self.name)


    def connect(self, value, socket):
        return value_types[socket.type].connect(self, value, socket)

    
    def import_node(self, node):
        assert isinstance(node, bpy.types.Node)
        return Node(self, node)
        
    def _new_node(self, node_type, properties):
        node = self.node_tree.nodes.new(node_type)

        for k, v in properties.items():
            assert getattr(node, k) is not None, "node {} has no property {}".format(node.type, k)
            setattr(node, k, v)

        self.created_nodes.append(node)
        return node

    def _new_link(self, value, input):
        assert value.tree is self, ""
        return self.node_tree.links.new(value.socket, input)



def camel_to_snake(name):
  name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def parameter_name(s):
    s = s.strip()               # lower case, strip whitespace
    s = re.sub('[\\s\\t\\n]+', '', s)  # spaces to underscores
    s = re.sub('[^0-9a-zA-Z_]', '', s)  # delete invalid characters

    return camel_to_snake(s)

def socket_parameter(socket):
    name = parameter_name(socket.identifier)
    value_type=value_types[socket.type]
    
    return inspect.Parameter(name, 
        kind=inspect.Parameter.POSITIONAL_OR_KEYWORD, 
        default=value_type.default_value(socket.default_value), 
        annotation=value_type.annotation())   

class Node:
    def __init__(self, tree, node):
        self._node = node

        self._outputs = [value_types[output.type](tree, output) for output in node.outputs 
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
    def connect(tree, v, socket):
        raise NotImplementedError


def wrap_node(tree, node):
    assert isinstance(node, bpy.types.Node)
    wrapper = tree.import_node(node)

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
    def __init__(self, tree, node_desc, properties={}):
        self.tree = tree
        self.desc = node_desc
        self.properties = properties

    def __str__(self):      
        properties_set = comma_sep(["{}={}".format(k, v) for k, v in self.properties.items()])
        properties = comma_sep(["{}:{}".format(k, p.type) 
            for k, p in self.desc.properties.items() if not p.is_common])

        inputs = comma_sep(["{}:{}".format(k, inp.type.__name__) 
            for k, inp in self.desc.inputs.items()])
        outputs = comma_sep(["{}:{}".format(k, output.type.__name__) 
            for k, output in self.desc.outputs.items()])

        return "{}({}):\n properties({})\n inputs({})\n outputs({})\n"\
            .format(self.desc.name, properties_set, properties, inputs, outputs)

    def __repr__(self):
        return "NodeBuilder({})".format(self.desc.name)

    @property
    def node_type(self):
        return self.desc.type.__name__

    def set(self, **properties):
        updated = self.properties.copy()

        for k, v in properties.items():
            if k not in self.desc.properties:
                raise TypeError('node {} has no property {}'.format(self.node_type, k))

            updated[k] = v
        return NodeBuilder(self.tree, self.desc, updated)


    def __call__(self, *args, **kwargs):
        try:
            node = self.tree._new_node(self.node_type, self.properties)

            sockets = [input for input in node.inputs if input.enabled]
            signature = inspect.Signature(parameters = [socket_parameter(input) for input in sockets])

            args = signature.bind(*args, **kwargs)
            args.apply_defaults()

            assert len(args.arguments) == len(sockets)
            for socket, (param_name, value) in zip(sockets, args.arguments.items()): 
                try:
                    self.tree.connect(value, socket)
                except TypeError as e:
                    raise TypeError("{}.{} - {}"\
                        .format(self.node_type,  param_name, e.args[0]))  

            return wrap_node(self.tree, node)
        
        except TypeError as e:
            raise TypeError(e.args[0]) from None



