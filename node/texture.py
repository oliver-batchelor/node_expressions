import sys
from node.expression import add_node_module

import sys
from node import expression, value
import node

from .util import staticproperty
from cached_property import cached_property
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
     

    def color(self):
        return Color(self.socket)

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




class Color(value.Color):
    def __init__(self, socket):
        super().__init__(socket)


    def vector(self):
        return Vector(self.socket)

    def float(self):
        return Float(self.socket)

    @staticmethod
    def combine(r, g, b, a=1):
        return self.nodes.compose(x, y, z)

    @cached_property
    def rgba(self):
        return self.nodes.decompose(self)   

    @property
    def r(self):
        return self.rgba.red

    @property
    def g(self):
        return self.rgba.green

    @property
    def b(self):
        return self.rgba.blue

    @property
    def a(self):
        return self.rgba.alpha

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


add_node_module(sys.modules[__name__], 'TEXTURE')



