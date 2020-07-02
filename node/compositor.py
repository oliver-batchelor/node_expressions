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
   
    def color(self):
        return Color(self.socket)




class Color(value.Color):
    def __init__(self, socket):
        super().__init__(socket)


    def vector(self):
        return Vector(self.socket)

    def float(self):
        return Float(self.socket)

    @staticmethod
    def combine_rgba(r, g, b, a=1):
        return self.nodes.combine_rgb(r, g, b, a)


    @cached_property
    def rgba(self):
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

    @property 
    def a(self):
        return self.rgb.a

    @cached_property
    def hsva(self):
        return self.nodes.separate_hsv(self)

    @property 
    def h(self):
        return self.hsva.h

    @property 
    def s(self):
        return self.hsva.s

    @property 
    def v(self):
        return self.hsva.v



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


add_node_module(sys.modules[__name__], 'COMPOSITING')



