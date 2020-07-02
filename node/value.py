import bpy

from numbers import Number
from cached_property import cached_property
from typing import List, Callable, Tuple, Any, Union, Optional

from .expression import node_context
from .util import typename, assert_type, staticproperty, classproperty, Namespace

import math



class Value:
    def __init__(self, socket):
        super().__init__()

        self.socket = socket.socket if isinstance(socket, Value)\
            else socket

        assert_type(self.socket, bpy.types.NodeSocket)
    

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
        if isinstance(socket, Number):
            socket = self.constant(socket)

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
    
    # Allow Vector/Color to handle operators as higher precedence
    def operator(self, name, x):
        if hasattr(type(x), name):
            f = getattr(type(x), name)
            return f(self, x)
        else:
            f = getattr(self, name)
            return f(x)



    def add(self, x): return Float.math.add(self, x)
    def sub(self, x): return Float.math.subtract(self, x)
    def mul(self, x): return Float.math.multiply(self, x)

    def __add__(self, x): return self.operator('add', x)
    def __sub__(self, x): return self.operator('sub', x)
    def __mul__(self, x): return self.operator('mul', x)

    def div(self, x): return Float.math.divide(self, x)

    def __truediv__(self, x):  return self.div(x)
    def __floordiv__(self, x): return self.div(x).floor()

    def mod(self, x): return Float.math.modulo(self, x)
    def pow(self, x): return Float.math.power(self, x)

    def __mod__(self, x): return self.mod(x)
    def __pow__(self, x): return self.pow(x)
    
    def __radd__(self, x): return Float.add(x, self)
    def __rsub__(self, x): return Float.sub(x, self)
    def __rmul__(self, x): return Float.mul(x, self)

    def __rtruediv__(self, x): return Float.div(x, self)
    def __rfloordiv__(self, x): return Float.div(x, self).floor()
    
    def __rmod__(self, x): return Float.math.mod(x, self)
    def __rpow__(self, x): return Float.math.power(x, self)
  
    def __neg__(self): return Float.math.multiply(self, -1)

    def abs(self): return Float.math.absolute(self)
    def __abs__(self): return Float.math.absolute(self)
    def __invert__(self): return 1 / self

    def round(self): return Float.math.round(self)
    def trunc(self): return Float.math.trunc(self)
    def floor(self): return Float.math.floor(self)
    def ceil(self): return Float.math.ceil(self)

    def frac(self): return Float.math.fraction(self)

    def __lt__(self, x): return Float.math.less_than(self, x)
    def __gt__(self, x): return Float.math.greater_than(self,x)


    def log(self, base=10): return Float.math.logarithm(self, base)
    def ln(self, base=math.e): return Float.math.logarithm(self, base)

    def pow(self, x): return Float.math.power(self, x)
    def sqrt(self): return Float.math.square_root(self)
    def inv_sqrt(self): return Float.math.inverse_square_root(self)

    def abs(self): return Float.math.absolute(self)
    def exp(self): return Float.math.exponent(self)

    def sin(self): return Float.math.sine(self)
    def cos(self): return Float.math.cosine(self)
    def tan(self): return Float.math.tangent(self)

    def asin(self): return Float.math.arcsine(self)
    def acos(self): return Float.math.arccosine(self)
    def atan(self): return Float.math.arctangent(self)
    def atan2(self, x): return Float.math.arctan2(self, x)

    def sinh(self): return Float.math.hyperbolic_sine(self)
    def cosh(self): return Float.math.hyperbolic_cosine(self)
    def tanh(self): return Float.math.hyperbolic_tangent(self)

    def min(self, other): return Float.math.minimum(self, other)
    def max(self, other): return Float.math.maximum(self, other)

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

    def add(self, x): return self.mix.add(1.0, self, x)
    def sub(self, x): return self.mix.subtract(1.0, self, x)
    def mul(self, x): return self.mix.multiply(1.0, self, x)       
 
    def __add__(self, x): return self.add(x)
    def __sub__(self, x): return self.sub(x)
    def __mul__(self, x): return self.mul(x)
        
    
    def __radd__(self, x): return Color.add(x, self)
    def __rsub__(self, x): return Color.sub(x, self)
    def __rmul__(self, x): return Color.mul(x, self)

    
    



