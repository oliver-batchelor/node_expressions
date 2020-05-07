import bpy

from numbers import Number
from cached_property import cached_property
from typing import List, Callable, Tuple, Any, Union, Optional

from .expression import node_context
from .util import typename, assert_type, staticproperty, classproperty

import math



def converts_vector(v):
    return isinstance(v, Vector) or isinstance(v, Vector) \
        or isinstance(v, Number) or isinstance(v, tuple)


class Value:
    def __init__(self, socket):
        super().__init__()

        self.socket = socket.socket if isinstance(socket, Value)\
            else socket

        assert_type(socket, bpy.types.NodeSocket)
    

    @property
    def node(self):
        return self.socket.node

    @staticproperty
    def nodes():
        return node_context().nodes
    
    @staticproperty
    def math():
        return Value.nodes.math



    @property
    def type(self):
        raise NotImplementedError
       
    def __repr__(self):
        return self.type


class Float(Value):
    def __init__(self, socket):
        super().__init__(socket)
         
    type = 'Float'

    @staticmethod
    def annotation():
         return Union[float, Float]

    @staticmethod
    def default_value(v):
        return float(v)

    @classmethod
    def constant(cls, x):
        value = cls.nodes.value()
        value.socket.default_value = x
        return value

    @staticmethod
    def connect(context, v, socket):
        if isinstance(v, Float):
            return context._new_link(v, socket)
        elif isinstance(v, Number):
            socket.default_value = v
            return None
        else:
            raise TypeError("expected scalar (float|Float), got " + type(v).__name__)

    def __add__(self, x): return self.math.add(self, x)
    def __sub__(self, x): return self.math.subtract(self, x)
    def __mul__(self, x): return self.math.multiply(self, x)
    def __truediv__(self, x): return self.math.divide(self, x)
    def __floordiv__(self, x): return self.math.floor(self.math.divide(self, x))

    def mod(self, x): return self.math.modulo(self, x)
    def pow(self, x): return self.math.power(self, x)

    def __mod__(self, x): return self.math.modulo(self, x)
    def __pow__(self, x): return self.math.power(self, x)
    
    def __radd__(self, x): return self.math.add(x, self)
    def __rsub__(self, x): return self.math.subtract(x, self)
    def __rmul__(self, x): return self.math.multiply(x, self)
    def __rtruediv__(self, x): return self.math.divide(x, self)
    def __rfloordiv__(self, x): return self.math.divide(x, self).floor()
    def __rmod__(self, x): return self.math.mod(x, self)
    def __rpow__(self, x): return self.math.power(x, self)
  
    def __neg__(self): return self.math.multiply(self, -1)

    def abs(self): return self.math.absolute(self)
    def __abs__(self): return self.math.absolute(self)
    def __invert__(self): return 1 / self

    def round(self): return self.math.round(self)
    def trunc(self): return self.math.trunc(self)
    def floor(self): return self.math.floor(self)
    def ceil(self): return self.math.ceil(self)

    def frac(self): return self.math.fraction(self)

    def __lt__(self, x): return self.math.less_than(self, x)
    def __gt__(self, x): return self.math.greater_than(self,x)


    def log(self, base=10): return self.math.logarithm(self, base)
    def ln(self, base=math.e): return self.math.logarithm(self, base)

    def pow(self, x): return self.math.power(self, x)
    def sqrt(self): return self.math.square_root(self)
    def inv_sqrt(self): return self.math.inverse_square_root(self)

    def abs(self): return self.math.absolute(self)
    def exp(self): return self.math.exponent(self)

    def sin(self): return self.math.sine(self)
    def cos(self): return self.math.cosine(self)
    def tan(self): return self.math.tangent(self)

    def asin(self): return self.math.arcsine(self)
    def acos(self): return self.math.arccosine(self)
    def atan(self): return self.math.arctangent(self)
    def atan2(self, x): return self.math.arctan2(self, x)

    def sinh(self): return self.math.hyperbolic_sine(self)
    def cosh(self): return self.math.hyperbolic_cosine(self)
    def tanh(self): return self.math.hyperbolic_tangent(self)

    def min(self, other): return self.math.minimum(self, other)
    def max(self, other): return self.math.maximum(self, other)

    def clamp(self, min=0.0, max=1.0):
        return self.nodes.clamp(self, min, max)



class Vector(Value):
    def __init__(self, socket):
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
    def connect(context, v, socket):
        if isinstance(v, Float) or  isinstance(v, Vector):
            return context._new_link(v, socket)
        elif isinstance(v, tuple):
            if len(v) != 3 or all([isinstance(x, Number) for x in v]): 
                raise TypeError("expected literals of length 3")
            socket.default_value = v            
        raise TypeError("expected float|tuple[float, float, float]|Vector, got " + type(v).__name__)     

class Int(Value):
    def __init__(self, socket):
        super().__init__(socket)
         
    type = 'Int'

    @staticmethod
    def annotation():
         return Union[int, Int]

    @staticmethod
    def default_value(v):
        return int(v)         

    @staticmethod
    def connect(context, v, socket):
        if isinstance(v, Int):
            return context._new_link(v, socket)
        elif isinstance(v, Number):
            socket.default_value = int(v)
            return None
        else:
            raise TypeError("expected int|Int, got " + type(v).__name__)     


class Bool(Value):
    def __init__(self, socket):
        super().__init__(socket)
         
    type = 'Bool'

    @staticmethod
    def annotation():
         return Union[bool, Bool]    

    @staticmethod
    def default_value(v):
        return bool(v)  


    @staticmethod
    def connect(context, v, socket):
        if isinstance(v, Bool):
            return context._new_link(v, socket)
        elif isinstance(v, bool):
            socket.default_value = v
            return None
        else:
            raise TypeError("expected bool|Bool, got " + type(v).__name__)     



class String(Value):
    def __init__(self, socket):
        super().__init__(socket)
         
    @staticmethod
    def annotation():
         return Union[str, String]    

    @staticmethod
    def default_value(v):
        return str(v)  

    @staticmethod
    def connect(context, v, socket):
        if isinstance(v, String):
            return context._new_link(v, socket)
        elif isinstance(v, str):
            socket.default_value = v
            return None
        else:
            raise TypeError("expected str|String, got " + type(v).__name__)     


class Shader(Value):
    def __init__(self,  socket):
        super().__init__(socket)

    type = 'Shader'

    @staticmethod
    def annotation():
         return Shader

    @staticmethod
    def default_value(v):
        return None 

    @staticmethod
    def connect(context, v, socket):
        if isinstance(v, Shader):
            return context._new_link(v, socket)
        elif v is not None:
            raise TypeError("expected Shader, got " + type(v).__name__) 

class Color(Value):
    def __init__(self,  socket):
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


    @staticmethod
    def connect(context, v, socket):
        if isinstance(v, Color) or isinstance(v, Float):
            context._new_link(v, socket)

        elif isinstance(v, Number):
            socket.default_value = (v, v, v, 1)
        elif isinstance(v, tuple):
            if len(v) != 4 or not all([isinstance(x, Number) for x in v]): 
                raise TypeError("expected literals of length 4")
                socket.default_value = v            
        else:
            raise TypeError("expected tuple[scalar x4]|Color, got " + type(v).__name__)

    @classproperty
    def mix(cls):
        return cls.nodes.mix_rgb
 
    def __add__(self, x): return self.mix.add(1.0, self, x)
    def __sub__(self, x): return self.mix.subtract(1.0, self, x)
    def __mul__(self, x): return self.mix.multiply(1.0, self, x)
        
    
    def __radd__(self, x): return self.mix.add(1.0, x, self)
    def __rsub__(self, x): return self.mix.subtract(1.0, x, self)
    def __rmul__(self, x): return self.mix.multiply(1.0, x, self)

    
    



