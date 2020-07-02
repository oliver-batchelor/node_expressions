import bpy
import idprop

import sys
from node import expression, value
import node

from .util import staticproperty, classproperty, Namespace
from cached_property import cached_property
from typing import Callable
from numbers import Number

import node.properties as properties


class Float(value.Float):
    def __init__(self, socket):
        super().__init__(socket)

    def color(self):
        return Color(self.socket)

    def vector(self):
        return Vector(self.socket)

    def float(self):
        return self

    
class Vector(value.Vector):
    def __init__(self, socket):
        if isinstance(socket, tuple):
            assert len(socket) == 3
            super().__init__(self.combine(*socket))
        else:
            super().__init__(socket)

    @classproperty
    def vector_math(cls):
        return cls.nodes.vector_math        

    @staticmethod
    def connect(context, v, socket):
        if isinstance(v, Vector) or isinstance(v, Float):
            context._new_link(v, socket)
        elif isinstance(v, Number):
            socket.default_value = (v, v, v)
        elif isinstance(v, tuple):
            if len(v) != 3: raise TypeError("expected literals of length 3")
            literals = [isinstance(x, Number) for x in v]
            if all(literals):
                socket.default_value = v            
            else:
                context._new_link(context.nodes.combine_xyz(*v), socket)
        else:
            raise TypeError("expected tuple[scalar, scalar, scalar]|Vector, got " + type(v).__name__)

    @classmethod
    def combine(cls, x, y, z):
        return cls.nodes.combine_xyz(x, y, z)

    @cached_property
    def xyz(self):
        return self.nodes.separate_xyz(self)   

    @property
    def x(self):
        return self.xyz.x

    @property
    def y(self):
        return self.xyz.y

    @property
    def z(self):
        return self.xyz.z

    def color(self):
        return Color(self.socket)

    def __iter__(self):
        return iter(self.xyz)

    def map(self, f, *args):
        return self.nodes.combine_xyz(*[f(x, *args) for x in self.xyz])

    def map2(self, f, other, *args):
        return self.nodes.combine_xyz(*[f(x, y *args) for x, y in zip(self.xyz, self.nodes.separate_xyz(other))])

    def add(self, x): return vector_math.add(self, x)
    def sub(self, x): return vector_math.subtract(self, x)
    def mul(self, x): return vector_math.multiply(self, x)
    def div(self, x): return vector_math.divide(self, x)


    def __add__(self, x): return self.add(x)
    def __sub__(self, x): return self.sub(x)
    def __mul__(self, x): return self.mul(x)

    def __truediv__(self, x): return self.div(x)
    def __floordiv__(self, x): return self.div(x).floor()


    def mod(self, x): return vector_math.modulo(self, x)
    def pow(self, x): return self.map(self.math.pow, self, x)

    def __mod__(self, x): return self.mod(x)
    def __pow__(self, x): return self.pow(x)
    
    def __radd__(self, x): return Vector.add(x, self)
    def __rsub__(self, x): return Vector.sub(x, self)
    def __rmul__(self, x): return Vector.mul(x, self)

    def __rtruediv__(self, x): return Vector.div(x, self)
    def __rfloordiv__(self, x): return Vector.div(x, self).floor()

    def abs(self): return vector_math.absolute(self)
     
    def __neg__(self): return vector_math.multiply(self, -1)
    def __abs__(self): return vector_math.absolute(self)
    def __invert__(self): return 1 / self

    def round(self): return self.map(self.math.round)
    def trunc(self): return self.map(self.math.truncate)
    def floor(self): return vector_math.floor(self)
    def ceil(self): return vector_math.ceil(self)

    def snap(self, x): return vector_math.snap(self, x)
    def frac(self): return vector_math.fraction(self)

    def min(self, other): return vector_math.minimum(self, other)
    def max(self, other): return vector_math.maximum(self, other)

    def dot(self, other): return vector_math.dot_product(self, other)
    def proj(self, other): return vector_math.project(self, other)
    def cross(self, other): return vector_math.cross_product(self, other)    




class Color(value.Color):
    def __init__(self, socket):
        if isinstance(socket, tuple):
            assert len(socket) == 3            
            super().__init__(self.combine_rgb(*socket))
        else:
            super().__init__(socket)



    def vector(self):
        return Vector(self.socket)

    def float(self):
        return Float(self.socket)

    @classmethod
    def combine_rgb(cls, r, g, b):
        return cls.nodes.combine_rgb(r, g, b)


    @cached_property
    def rgb(self):
        return self.nodes.separate_rgb(self)


    @property 
    def r(self):
        return self.rgb.r

    @property 
    def g(self):
        return self.rgb.g

    @property 
    def b(self):
        return self.rgb.b

    @cached_property
    def hsv(self):
        return self.nodes.separate_hsv(self)

    @property 
    def h(self):
        return self.hsv.h

    @property 
    def s(self):
        return self.hsv.s

    @property 
    def v(self):
        return self.hsv.v




class Int(value.Int):
    def __init__(self, socket):
        super().__init__(socket)

    def float(self):
        return Float(self.socket)


class Bool(value.Bool):
    def __init__(self, socket):
        super().__init__(socket)

    def float(self):
        return Float(self.socket)


class Shader(value.Shader):
    def __init__(self, socket):
        super().__init__(socket)


class String(value.String):
    def __init__(self, socket):
        super().__init__(socket)


_value_types = {
    'VALUE':Float, 
    'INT':Int, 
    'BOOLEAN':Bool, 
    'VECTOR':Vector, 
    'STRING':String, 
    'SHADER':Shader, 
    'RGBA':Color
}


module = sys.modules[__name__]
expression.add_node_module(module, 'SHADER')


def float_driver(obj, prop_name):
    v = obj[prop_name]

    node_value = module.value()
    fcurve = node_value.socket.driver_add("default_value")
    driver = fcurve.driver

    driver.type = 'AVERAGE'
    var = driver.variables.new()
    var.targets[0].id = obj
    var.targets[0].data_path = '["{}"]'.format(prop_name)

    return node_value
    

def property_drivers(obj):
    assert isinstance(obj, bpy.types.bpy_struct)
    drivers = {}

    rna_properties = {prop.identifier for prop in obj.bl_rna.properties if prop.is_runtime}
    rna_ui = obj.get('_RNA_UI', {})

    for k, v in obj.items():
        if k == '_RNA_UI' or k in rna_properties:
            continue
        prop = rna_ui[k]

        if isinstance(v, Number):
            drivers[k] = float_driver(obj, k)

    return Namespace("{} drivers".format(obj.name), drivers)


        
      
