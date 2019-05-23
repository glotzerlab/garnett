#!/usr/bin/env python

import hoomd
import hoomd.hpmc
import hoomd.deprecated
import json

point_2d_vert = [(0, 0)]
point_3d_vert = [(0, 0, 0)]
line_2d_verts = [(-0.5, 0), (0.5, 0)]
line_3d_verts = [(-0.5, 0, 0), (0.5, 0, 0)]
square_verts = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
tetrahedron_verts = [(0.5, 0.5, 0.5), (0.5, -0.5, -0.5),
                     (-0.5, 0.5, -0.5), (-0.5, -0.5, 0.5)]

shape_classes = [
    {
        'name': 'convex_polygon',
        'cls': 'convex_polygon',
        'dimensions': 2,
        'params': {
            'vertices': square_verts,
        },
    },
    {
        'name': 'convex_polyhedron',
        'cls': 'convex_polyhedron',
        'dimensions': 3,
        'params': {
            'vertices': tetrahedron_verts,
        },
    },
    {
        'name': 'convex_spheropolygon',
        'cls': 'convex_spheropolygon',
        'dimensions': 2,
        'params': {
            'vertices': square_verts,
            'sweep_radius': 0.1,
        },
    },
    {
        'name': 'convex_spheropolyhedron',
        'cls': 'convex_spheropolyhedron',
        'dimensions': 3,
        'params': {
            'vertices': tetrahedron_verts,
            'sweep_radius': 0.1,
        },
    },
    {
        'name': 'disk',
        'cls': 'sphere',
        'dimensions': 2,
        'params': {
            'diameter': 1,
        },
    },
    {
        'name': 'sphere',
        'cls': 'sphere',
        'dimensions': 3,
        'params': {
            'diameter': 1,
        },
    },
    {
        'name': 'disk_as_point_spheropolygon',
        'cls': 'convex_spheropolygon',
        'dimensions': 2,
        'params': {
            'vertices': point_2d_vert,
            'sweep_radius': 0.5,
        },
    },
    {
        'name': 'sphere_as_point_spheropolyhedron',
        'cls': 'convex_spheropolyhedron',
        'dimensions': 3,
        'params': {
            'vertices': point_3d_vert,
            'sweep_radius': 0.5,
        },
    },
    {
        'name': 'spherocylinder_2d',
        'cls': 'convex_spheropolygon',
        'dimensions': 2,
        'params': {
            'vertices': line_2d_verts,
            'sweep_radius': 0.2,
        },
    },
    {
        'name': 'spherocylinder_3d',
        'cls': 'convex_spheropolyhedron',
        'dimensions': 3,
        'params': {
            'vertices': line_3d_verts,
            'sweep_radius': 0.2,
        },
    },
    {
        'name': 'ellipsoid_3d',
        'cls': 'ellipsoid',
        'dimensions': 3,
        'params': {
            'a': float(0.5),
            'b': float(0.25),
            'c': float(0.125),
        },
    },
]

if __name__ == '__main__':
    for shape_class in shape_classes:
        shape_name = shape_class['name']
        print(shape_name)
        with hoomd.context.initialize() as context:
            if shape_class['dimensions'] == 2:
                uc = hoomd.lattice.sq(a=5.0)
            else:
                uc = hoomd.lattice.sc(a=5.0)
            hoomd.init.create_lattice(uc, n=3)
            mc = getattr(hoomd.hpmc.integrate, shape_class['cls'])(seed=42)
            mc.shape_param.set('A', **shape_class['params'])

            try:
                gsd_dump = hoomd.dump.gsd(
                    '{}.gsd'.format(shape_name), period=1,
                    group=hoomd.group.all(), overwrite=True)
                gsd_dump.dump_state(mc)
            except NotImplementedError:
                print("%s not implimented for gsd files." % shape_name)

            try:
                getar_dump = hoomd.dump.getar(
                    '{}.zip'.format(shape_name), mode='w',
                    static=['viz_static'], dynamic={'viz_aniso_dynamic': 1})
                getar_dump.writeJSON('type_shapes.json', mc.get_type_shapes(),
                                     dynamic=False)
            except NotImplementedError:
                print("%s not implimented for getar files." % shape_name)

            try:
                pos_dump = hoomd.deprecated.dump.pos(
                    '{}.pos'.format(shape_name), period=1)
                mc.setup_pos_writer(pos_dump)
            except NotImplementedError:
                print("%s not implimented for pos files." % shape_name)

            hoomd.run(10)

    with open('shape_data.json', 'w') as jsonfile:
        json.dump(shape_classes, jsonfile)
