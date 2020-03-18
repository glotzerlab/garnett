# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
from ddt import ddt, data
import json
import numpy.testing as npt
import os
import unittest

import garnett

try:
    import gtar  # noqa: F401
except ImportError:
    GTAR = False
else:
    GTAR = True

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


@ddt
class ShapeTest(unittest.TestCase):
    reader = garnett.reader.GSDHOOMDFileReader
    extension = 'gsd'
    mode = 'rb'

    def get_filename(self, shape_name):
        return os.path.join(SHAPE_DATA_PATH,
                            '{}{}'.format(shape_name, self.extension))

    def check_shape_class(self, shape_class):
        shape_name = shape_class['name']
        with open(self.get_filename(shape_name), self.mode) as f:
            traj = self.reader().read(f)
            shapedef = traj[-1].shapedef
        shape_A = shapedef['A']
        type_shape = shape_A.type_shape

        # Check each field of the shape parameters and JSON shape definition
        vertices = shape_class['params'].get('vertices', None)
        if vertices is not None and len(vertices) > 1:
            npt.assert_allclose(shape_A.vertices, vertices)
            npt.assert_allclose(type_shape['vertices'], vertices)
            sweep_radius = shape_class['params'].get('sweep_radius', None)
            if sweep_radius is not None:
                npt.assert_allclose(shape_A.rounding_radius, sweep_radius)
                npt.assert_allclose(type_shape['rounding_radius'], sweep_radius)
        for key in ('diameter', 'a', 'b', 'c'):
            value = shape_class['params'].get(key, None)
            if value is not None:
                npt.assert_almost_equal(getattr(shape_A, key), value)
                npt.assert_almost_equal(type_shape[key], value)


@ddt
class GSDShapeTest(ShapeTest):
    reader = garnett.reader.GSDHOOMDFileReader
    extension = '_shape.gsd'
    mode = 'rb'

    @data(*annotate_shape_test('GSDHOOMDFileReader', get_shape_classes()))
    def test_shapes(self, shape_class):
        self.check_shape_class(shape_class)


@ddt
class GSDStateTest(ShapeTest):
    reader = garnett.reader.GSDHOOMDFileReader
    extension = '_state.gsd'
    mode = 'rb'

    @data(*annotate_shape_test('GSDHOOMDFileReader', get_shape_classes()))
    def test_shapes(self, shape_class):
        self.check_shape_class(shape_class)


@unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
@ddt
class GetarShapeTest(ShapeTest):
    reader = garnett.reader.GetarFileReader
    extension = '.zip'
    mode = 'r'

    @data(*annotate_shape_test('GetarFileReader', get_shape_classes()))
    def test_shapes(self, shape_class):
        self.check_shape_class(shape_class)


@ddt
class POSShapeTest(ShapeTest):
    reader = garnett.reader.PosFileReader
    extension = '.pos'
    mode = 'r'

    @data(*annotate_shape_test('PosFileReader', get_shape_classes()))
    def test_shapes(self, shape_class):
        if shape_class['dimensions'] == 3 or shape_class['cls'] == 'convex_polygon':
            self.check_shape_class(shape_class)


if __name__ == '__main__':
    unittest.main()
