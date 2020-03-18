# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
from ddt import ddt, data
import json
import os
import unittest

import garnett
from garnett.shapes import SpheropolygonShape, ConvexSpheropolyhedronShape

try:
    import gtar  # noqa: F401
except ImportError:
    GTAR = False
else:
    GTAR = True

try:
    import plato  # noqa: F401
except ImportError:
    PLATO = False
else:
    PLATO = True

SHAPE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'files', 'shapes')


def get_shape_classes():
    jsonpath = os.path.join(SHAPE_DATA_PATH, 'shape_data.json')
    with open(jsonpath, 'r') as jsonfile:
        shape_classes = json.load(jsonfile)
    return shape_classes


class ShapeTestData(dict):
    pass


def annotate_shape_test(test_class, shape_classes):
    for s in shape_classes:
        s = ShapeTestData(s)
        setattr(s, '__name__', '{}_{}'.format(test_class, s['name']))
        yield s


@unittest.skipIf(not PLATO, 'The plato module is required.')
@ddt
class ShapeTest(unittest.TestCase):
    reader = garnett.reader.GSDHOOMDFileReader
    extension = 'gsd'
    mode = 'rb'

    def get_filename(self, shape_name):
        return os.path.join(SHAPE_DATA_PATH,
                            '{}.{}'.format(shape_name, self.extension))

    def render_shape_class(self, shape_class, suffix=None):
        shape_name = shape_class['name']
        if suffix is not None:
            shape_name += suffix
        filename = self.get_filename(shape_name)
        with open(filename, self.mode) as f:
            traj = self.reader().read(f)
            dimensions = traj[-1].box.dimensions

            valid_shapes = True
            for shape in traj[-1].type_shapes:
                # Ignore convex spheropolyhedra because they're not well supported by plato backends
                if isinstance(shape, ConvexSpheropolyhedronShape):
                    valid_shapes = False

                # Ignore improper sphero-shapes with too few vertices
                if isinstance(shape, ConvexSpheropolyhedronShape) or \
                        isinstance(shape, SpheropolygonShape):
                    if len(shape.vertices) < dimensions + 1:
                        valid_shapes = False

            if valid_shapes:
                for backend in ('fresnel', 'povray', 'vispy', 'matplotlib'):
                    try:
                        scene = traj[-1].to_plato_scene(backend=backend)
                        if dimensions == 3:
                            scene.rotation = [9.9774611e-01, 2.3801494e-02, -6.2734932e-02, 5.5756618e-04]
                        scene.enable('antialiasing')
                        scene.save('{}.png'.format(self.get_filename(shape_name)))
                    except Exception:
                        continue
                    else:
                        break
                else:
                    raise RuntimeError('No available backend could render the scene: {}'.format(filename))


@ddt
class GSDShapeTest(ShapeTest):
    reader = garnett.reader.GSDHOOMDFileReader
    extension = 'gsd'
    mode = 'rb'

    @data(*annotate_shape_test('GSDHOOMDFileReader', get_shape_classes()))
    def test_shape(self, shape_class):
        self.render_shape_class(shape_class, suffix='_shape')

    @data(*annotate_shape_test('GSDHOOMDFileReader', get_shape_classes()))
    def test_state(self, shape_class):
        self.render_shape_class(shape_class, suffix='_state')


@unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
@ddt
class GetarShapeTest(ShapeTest):
    reader = garnett.reader.GetarFileReader
    extension = 'zip'
    mode = 'r'

    @data(*annotate_shape_test('GetarFileReader', get_shape_classes()))
    def test_shape(self, shape_class):
        self.render_shape_class(shape_class)


@ddt
class POSShapeTest(ShapeTest):
    reader = garnett.reader.PosFileReader
    extension = 'pos'
    mode = 'r'

    @data(*annotate_shape_test('PosFileReader', get_shape_classes()))
    def test_shape(self, shape_class):
        if shape_class['dimensions'] == 3 or shape_class['cls'] == 'convex_polygon':
            self.render_shape_class(shape_class)


if __name__ == '__main__':
    unittest.main()
