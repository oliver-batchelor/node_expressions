import bpy

from functools import partial
from node.util import Namespace

from numbers import Number


def custom_property(obj, name, value, min=None, max=None, description=None):
    rna_ui = obj.get('_RNA_UI')
    if rna_ui is None:
        obj['_RNA_UI'] = {}
        rna_ui = obj['_RNA_UI']

    obj[name] = value
    options = {}
    
    if min is not None:
        options["min"] = min
        options["soft_min"] = min

    if max is not None:
        options["max"] = max
        options["soft_max"] = max
    
    if not (max is None and min is None):
        options["use_soft_limits"] = 1

    if description is not None:
        options["max"] = description

    rna_ui[name] = options


def float_prop(value, min=None, max=None, description=None):
    assert isinstance(value, Number)
    assert min is None or isinstance(min, Number)
    assert max is None or isinstance(max, Number)
    return partial(custom_property, value=float(value), min=min, max=max, description=description)

def unit_prop(value, description=None):
    assert isinstance(value, Number)
    return partial(custom_property, value=value, min=0.0, max=1.0, description=description)

def vector_prop(x, y, z, min=None, max=None, description=None):
    assert isinstance(x, Number) and isinstance(y, Number) and isinstance(z, Number)
    assert min is None or isinstance(min, Number)
    assert max is None or isinstance(max, Number)

    value = [float(x), float(y), float(z)]
    return partial(custom_property, value=value, min=min, max=max, description=description)

def color_prop(r, g, b, a=1.0, description=None):
    assert isinstance(x, Number) and isinstance(y, Number) and isinstance(z, Number)
    
    value = [float(x), float(y), float(z), float(a)]
    return partial(custom_property, value=value, min=0.0, max=1.0, description=description)



def custom_properties(obj, **values):
    for k, create in values.items():
        create(obj, k)

