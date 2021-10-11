import bpy
import sys

sys.path.append('.')  

from node import group, expression, shader, properties
from node.properties import custom_properties, float_prop, vector_prop, color_prop, unit_prop
from node.shader import Vector, Float

import util

from math import pi
from numbers import Number


def mosaic_rotation(uv : Vector, edge_peturb:Vector=(0, 0, 0), scale:Float=1.0, rotation_inc:Float=0, rotation_var:Float=1):
    cell = (uv / scale + edge_peturb).floor()
    frac = uv - cell

    angle = rotation_inc * (cell.x + cell.y + cell.z)
    noise = rotation_var * (shader.tex_white_noise(cell).value - 0.5) * 360
    return shader.vector_rotate(vector=frac, center=scale / 2, angle=(angle + noise) * (pi / 180))


def sum_weighted(samples, weights):
    total = sum(weights)

    weights = [x / total for x in weights]
    return sum([sample * weight for sample, weight in zip(samples, weights)])

def mosaic_sampling( uv, edge_peturb=0, scale=1, overlap=0.125, rotation_inc=0, rotation_var=1):
    vector_math = shader.vector_math
    def make_patch(uv : shader.Vector):       
        frac = vector_math.fraction((uv + edge_peturb) / scale - 0.25)
        
        b = overlap / scale
        uv_grad = (b + vector_math.minimum(frac - 0.25, 0.75 - frac)) / overlap
    
        rotated_uv = mosaic_rotation(uv - 0.5, edge_peturb / 4, scale=scale * 2, 
            rotation_inc=rotation_inc, rotation_var=rotation_var)
        weight = (uv_grad.x.clamp() * uv_grad.y.clamp()) 

        return (rotated_uv, weight)

    # For readability on the node editor
    # make_patch = group.function(make_patch, "make_patch") 
    patches = [
        make_patch(uv), 
        make_patch(uv + (1, 0, 1)),  
        make_patch(uv + (0, 1, 2)), 
        make_patch(uv + (1, 1, 3))
    ]
    uvs, weights = zip(*patches)
    return uvs, weights


def show_sampling(uvs, weights):
    colors = [
        (1, 0, 0),
        (1, 1, 0),
        (0, 1, 0),
        (0, 0, 1),
    ]
    
    samples = [(shader.tex_checker(uv).fac + 0.4) * shader.Vector(color)
        for uv, color in zip (uvs, colors)]

    return sum_weighted(samples, weights)


def sine_pattern(uv, frequency=8, amplitude=0.025):
    geom = shader.new_geometry()

    x = (uv.y * frequency * pi).sin()
    y = (uv.x * frequency * pi).sin()
    return shader.Vector.combine(x, y, 0) * amplitude


def mask_vector(v, x=None, y=None, z=None):
    return shader.Vector.combine(
        x if x is not None else v.x, 
        y if y is not None else v.y, 
        z if z is not None else v.z, 
    )


def edge_noise(uv, props):

    noise_2d = shader.tex_noise.set(noise_dimensions='2D')
    noise = noise_2d(uv, scale=props.edge_scale/props.scale, 
        detail=props.edge_detail).color.vector() - 0.5

    return props.edge_magnitude * mask_vector(noise, z=0)    




def main():
    mat = util.node_material("checker")
    plane = util.adaptive_plane(name="terrain", size=10, material=mat)  

    custom_properties(plane, 
        scale=float_prop(2, min=0),
        overlap=float_prop(0.1, min=0.0001),
        rotation_inc = float_prop(7),
        rotation_var = unit_prop(0.1),

        edge_magnitude=float_prop(0.0, min=0),        
        edge_scale=float_prop(2, min=0),
        edge_detail=float_prop(1, min=0),
    )
    

    with expression.node_tree(mat.node_tree):
        geom = shader.new_geometry()
        props = shader.property_drivers(plane)

        # edge_peturb = sine_pattern(geom.position, frequency=props.edge_scale/props.scale, amplitude=props.edge_magnitude)
        edge_peturb = edge_noise(geom.position, props)

        # uv = mosaic_rotation(geom.position, edge_peturb, scale=props.scale, 
        #     rotation_inc=props.rotation_inc, rotation_var=props.rotation_var)
        # color = shader.tex_voronoi(uv).color

        # shader.output_material(shader.Color(color))

        uvs, weights = mosaic_sampling(geom.position, edge_peturb, scale=props.scale, overlap=props.overlap, 
            rotation_inc=props.rotation_inc, rotation_var=props.rotation_var)

        color = show_sampling(uvs, weights)
        shader.output_material(shader.Color(color))  


if __name__ == '__main__':   
    main()
    

    
    
    