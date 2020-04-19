import bpy

from numbers import Number
from cached_property import cached_property
from typing import List, Callable, Tuple, Any, Union, Optional

from .util import typename, assert_type

def converts_vector(v):
    return isinstance(v, Vector) or isinstance(v, Vector) \
        or isinstance(v, Number) or isinstance(v, tuple)


class Value:
    def __init__(self, tree, socket):
        super().__init__()

        self.tree = tree
        self.socket = socket.socket if isinstance(socket, Value)\
            else socket

        assert_type(socket, bpy.types.NodeSocket)
    

    @property
    def node(self):
        return self.socket.node

    @property 
    def nodes(self):
        return self.tree.nodes
    
    @property
    def math(self):
        return self.tree.nodes.math

    @property
    def vector_math(self):
        return self.tree.nodes.vector_math
    

    @property
    def type(self):
        raise NotImplementedError
       
    def __repr__(self):
        return self.type


class Float(Value):
    def __init__(self, tree, socket):
        super().__init__(tree, socket)
         
    type = 'Float'

    @staticmethod
    def annotation():
         return Union[float, Float]

    @staticmethod
    def default_value(v):
        return float(v)

    def color(self):
        return Color(self.tree, self.socket)

    def vector(self):
        return Vector(self.tree, self.socket)

    @staticmethod
    def connect(tree, v, socket):
        if isinstance(v, Float):
            return tree._new_link(v, socket)
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
    def __abs__(self): return self.math.absolute(self)
    def __invert__(self): return 1 / self

    def round(self): return self.math.round(self)
    def trunc(self): return self.math.trunc(self)
    def floor(self): return self.math.floor(self)
    def ceil(self): return self.math.ceil(self)

    def __lt__(self, x): return self.math.less_than(self, x)
    def __gt__(self, x): return self.math.greater_than(self,x)

    def clamp(self, min=0.0, max=1.0):
        return self.nodes.clamp(self, min, max)


class Vector(Value):
    def __init__(self, tree, socket):
        super().__init__(tree, socket)
         
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
    def connect(tree, v, socket):
        if isinstance(v, Vector) or isinstance(v, Float):
            tree._new_link(v, socket)
        elif isinstance(v, Number):
            socket.default_value = (v, v, v)
        elif isinstance(v, tuple):
            if len(v) != 3: raise TypeError("expected literals of length 3")
            literals = [isinstance(x, Number) for x in v]
            
            if all(literals):
                socket.default_value = v            
            else:
                tree._new_link(tree.nodes.combine_xyz(*v), socket)

        else:
            raise TypeError("expected tuple[scalar, scalar, scalar]|Vector, got " + type(v).__name__)

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

    def __mod__(self, x): return self.map(self.math.modulo, self, x)
    def __pow__(self, x): return self.map(self.math.pow, self, x)
    
    def __radd__(self, x): return self.vector_math.add(self, x, self)
    def __rsub__(self, x): return self.vector_math.subtract(self, x, self)
    def __rmul__(self, x): return self.vector_math.multiply(self, x, self)
    def __rtruediv__(self, x): return self.vector_math.divide(self, x, self)
    def __rfloordiv__(self, x): return self.vector_math.divide(self, x, self).floor()

  
    def __neg__(self): return self.vector_math.multiply(self, -1)
    def __abs__(self): return self.vector_math.absolute(self)
    def __invert__(self): return 1 / self

    def round(self): return self.map(self.math.round)
    def trunc(self): return self.map(self.math.truncate)
    def floor(self): return self.vector_math.floor(self)
    def ceil(self): return self.vector_math.ceil(self)



class Int(Value):
    def __init__(self, tree, socket):
        super().__init__(tree, socket)
         
    type = 'Int'

    @staticmethod
    def annotation():
         return Union[int, Int]

    @staticmethod
    def default_value(v):
        return int(v)         

    def float(self):
        return Float(self.tree, self.socket)

    @staticmethod
    def connect(tree, v, socket):
        if isinstance(v, Int):
            return tree._new_link(v, socket)
        elif isinstance(v, Number):
            socket.default_value = int(v)
            return None
        else:
            raise TypeError("expected int|Int, got " + type(v).__name__)     


class Bool(Value):
    def __init__(self, tree, socket):
        super().__init__(tree, socket)
         
    type = 'Bool'

    @staticmethod
    def annotation():
         return Union[bool, Bool]    

    @staticmethod
    def default_value(v):
        return bool(v)  

    def float(self):
        return Float(self.tree, self.socket)

    @staticmethod
    def connect(tree, v, socket):
        if isinstance(v, Bool):
            return tree._new_link(v, socket)
        elif isinstance(v, bool):
            socket.default_value = v
            return None
        else:
            raise TypeError("expected bool|Bool, got " + type(v).__name__)     



class String(Value):
    def __init__(self, tree, socket):
        super().__init__(tree, socket)
         
    @staticmethod
    def annotation():
         return Union[str, String]    

    @staticmethod
    def default_value(v):
        return str(v)  

    @staticmethod
    def connect(tree, v, socket):
        if isinstance(v, String):
            return tree._new_link(v, socket)
        elif isinstance(v, str):
            socket.default_value = v
            return None
        else:
            raise TypeError("expected str|String, got " + type(v).__name__)     


class Shader(Value):
    def __init__(self, tree, socket):
        super().__init__(tree, socket)
         
    @staticmethod
    def annotation():
         return Shader

    @staticmethod
    def connect(tree, v, socket):
        if isinstance(v, String):
            return tree._new_link(v, socket)
        else:
            raise TypeError("expected Shader, got " + type(v).__name__) 

class Color(Value):
    def __init__(self, tree, socket):
        super().__init__(tree, socket)
         
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
    def connect(tree, v, socket):
        if isinstance(v, Color) or isinstance(v, Float):
            tree._new_link(v, socket)

        elif isinstance(v, Number):
            socket.default_value = (v, v, v, 1)

        elif isinstance(v, tuple):
            if len(v) != 3: raise TypeError("expected literals of length 4")
            literals = [isinstance(x, Number) for x in v]
            
            if all(literals):
                socket.default_value = v            
            else:
                tree._new_link(tree.nodes.combine_rgb(*v), socket)
        else:
            raise TypeError("expected tuple[scalar x4]|Color, got " + type(v).__name__)

    def vector(self):
        return Vector(self.tree, self.socket)

    @cached_property
    def rgb(self):
        return self.nodes.separate_rgb(self)

    @cached_property
    def hsv(self):
        return self.nodes.separate_hsv(self)



value_types = {
    'VALUE':Float, 
    'INT':Int, 
    'BOOLEAN':Bool, 
    'VECTOR':Vector, 
    'STRING':String, 
    'SHADER':Shader, 
    'RGBA':Color
}