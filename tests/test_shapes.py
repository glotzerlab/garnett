from ddt import ddt, data
import json
import numpy.testing as npt
import os
import unittest

import glotzformats

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
    reader = glotzformats.reader.GSDHOOMDFileReader
    extension = 'gsd'
    mode = 'rb'

    def get_filename(self, shape_name):
        return os.path.join(SHAPE_DATA_PATH,
                            '{}.{}'.format(shape_name, self.extension))

    def check_shape_class(self, shape_class):
        shape_name = shape_class['name']
        with open(self.get_filename(shape_name), self.mode) as f:
            traj = self.reader().read(f)
            shapedef = traj[-1].shapedef
        json_shape = shapedef['A'].json_shape

        # Check each field of the shape parameters and JSON shape definition
        if 'vertices' in shape_class['params']:
            npt.assert_allclose(shapedef['A'].vertices,
                                shape_class['params']['vertices'])
            npt.assert_allclose(json_shape['vertices'],
                                shape_class['params']['vertices'])
        if 'diameter' in shape_class['params']:
            npt.assert_almost_equal(shapedef['A'].diameter,
                                    shape_class['params']['diameter'])
            npt.assert_almost_equal(json_shape['diameter'],
                                    shape_class['params']['diameter'])
        if 'sweep_radius' in shape_class['params']:
            npt.assert_almost_equal(shapedef['A'].rounding_radius,
                                    shape_class['params']['sweep_radius'])
            npt.assert_almost_equal(json_shape['rounding_radius'],
                                    shape_class['params']['sweep_radius'])


@ddt
class GSDShapeTest(ShapeTest):
    reader = glotzformats.reader.GSDHOOMDFileReader
    extension = 'gsd'
    mode = 'rb'

    @data(*annotate_shape_test('GSDHOOMDFileReader', get_shape_classes()))
    def test_shapes(self, shape_class):
        self.check_shape_class(shape_class)


@unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
@ddt
class GetarShapeTest(ShapeTest):
    reader = glotzformats.reader.GetarFileReader
    extension = 'zip'
    mode = 'r'

    @data(*annotate_shape_test('GetarFileReader', get_shape_classes()))
    def test_shapes(self, shape_class):
        self.check_shape_class(shape_class)


@ddt
class POSShapeTest(ShapeTest):
    reader = glotzformats.reader.PosFileReader
    extension = 'pos'
    mode = 'r'

    @data(*annotate_shape_test('PosFileReader', get_shape_classes()))
    def test_shapes(self, shape_class):
        # Ignore 2D shapes because POS files assume everything is 3D
        if shape_class['dimensions'] == 3:
            self.check_shape_class(shape_class)


if __name__ == '__main__':
    unittest.main()