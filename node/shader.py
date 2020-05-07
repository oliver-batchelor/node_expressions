import sys
from node import expression, value
import node

from .util import staticproperty, classproperty
from cached_property import cached_property
from typing import Callable
from numbers import Number




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

    @staticmethod
    def combine(x, y, z):
        return self.nodes.combine_xyz(x, y, z)

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


    def __add__(self, x): return self.vector_math.add(self, x)
    def __sub__(self, x): return self.vector_math.subtract(self, x)
    def __mul__(self, x): return self.vector_math.multiply(self, x)
    def __truediv__(self, x): return self.vector_math.divide(self, x)
    def __floordiv__(self, x): return self.vector_math.divide(self, x).floor()


    def mod(self, x): return self.vector_math.modulo(self, x)
    def pow(self, x): return self.map(self.math.pow, self, x)

    def __mod__(self, x): return self.map(self.math.modulo, self, x)
    def __pow__(self, x): return self.map(self.math.pow, self, x)
    
    def __radd__(self, x): return self.vector_math.add(x, self)
    def __rsub__(self, x): return self.vector_math.subtract(x, self)
    def __rmul__(self, x): return self.vector_math.multiply(x, self)
    def __rtruediv__(self, x): return self.vector_math.divide(x, self)
    def __rfloordiv__(self, x): return self.vector_math.divide(x, self).floor()

    def abs(self): return self.vector_math.absolute(self)
     
    def __neg__(self): return self.vector_math.multiply(self, -1)
    def __abs__(self): return self.vector_math.absolute(self)
    def __invert__(self): return 1 / self

    def round(self): return self.map(self.math.round)
    def trunc(self): return self.map(self.math.truncate)
    def floor(self): return self.vector_math.floor(self)
    def ceil(self): return self.vector_math.ceil(self)

    def snap(self, x): return self.vector_math.snap(self, x)
    def frac(self): return self.vector_math.fraction(self)

    def min(self, other): return self.vector_math.minimum(self, other)
    def max(self, other): return self.vector_math.maximum(self, other)

    def dot(self, other): return self.vector_math.dot_product(self, other)
    def proj(self, other): return self.vector_math.project(self, other)
    def cross(self, other): return self.vector_math.cross_product(self, other)    




class Color(value.Color):
    def __init__(self, socket):
        super().__init__(socket)


    def vector(self):
        return Vector(self.socket)

    def float(self):
        return Float(self.socket)

    @staticmethod
    def combine_rgb(r, g, b):
        return self.nodes.combine_rgb(r, g, b)


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


expression.add_node_module(sys.modules[__name__], 'SHADER')
