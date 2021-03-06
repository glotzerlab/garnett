# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import os
import io
import unittest
import base64
import tempfile

import numpy as np

import garnett

try:
    import gsd  # noqa: F401
    import gsd.hoomd  # noqa: F401
except ImportError:
    GSD = False
else:
    GSD = True


TESTDATA_PATH = os.path.join(os.path.dirname(__file__), 'files/')


def get_filename(filename):
    return os.path.join(TESTDATA_PATH, filename)


class ColorlessShape(garnett.shapes.Shape):
    """Shape without colors, for comparing formats.

    :param other: Another Shape object.
    :type other: :py:class:`garnett.shapes.Shape`
    """

    def __init__(self, other):
        for key in vars(other):
            if key != 'color':
                setattr(self, key, getattr(other, key))

    def __str__(self):
        return str(self.shape_class)


def assertEqualShapedefs(first, second):
    assert set(first.keys()) == set(second.keys())
    for key in first:
        assert ColorlessShape(first[key]) == ColorlessShape(second[key])


@unittest.skipIf(not GSD, 'GSDHOOMDFileWriter requires the gsd module.')
class BaseGSDHOOMDFileWriterTest(unittest.TestCase):
    reader_class = garnett.reader.GSDHOOMDFileReader
    writer_class = garnett.writer.GSDHOOMDFileWriter

    def setUp(self):
        self.reader = type(self).reader_class()
        self.writer = type(self).writer_class()

    def test_write(self):
        # Note that this test assumes that the reader is working, and therefore
        # could fail if the reader is broken even if the writer is fine.
        gsdfile = io.BytesIO(base64.b64decode(garnett.samples.GSD_BASE64))

        traj = self.reader.read(gsdfile)
        traj.load_arrays()
        len_orig = len(traj)
        readwrite_props = ['N', 'types', 'typeid',
                           'position', 'orientation', 'velocity',
                           'mass', 'charge', 'diameter',
                           'moment_inertia', 'angmom', 'image']
        original_data = {}
        for prop in readwrite_props:
            original_data[prop] = getattr(traj, prop)
        box_orig = traj[0].box.get_box_matrix()  # Just checking one frame

        # Write to a temp file
        tmpfile = tempfile.NamedTemporaryFile(mode='wb')
        with tmpfile as f:
            self.writer.write(traj, f)

            # Read back the file and check if it is the same as the original read
            traj = self.reader.read(f)
            traj.load_arrays()
            self.assertEqual(len(traj), len_orig)
            for prop in readwrite_props:
                self.assertTrue(np.array_equal(
                    getattr(traj, prop), original_data[prop]))
            self.assertTrue(np.allclose(traj[0].box.get_box_matrix(), box_orig))

    def test_write_sphere_shapedef(self):
        # Write to / read from a temp file
        tmpfile = tempfile.NamedTemporaryFile(mode='wb')

        with tmpfile:
            with garnett.read(get_filename('FeSiUC.pos')) as traj:
                self.writer.write(traj, tmpfile)
                written_traj = self.reader.read(tmpfile)
                assertEqualShapedefs(written_traj[0].shapedef, traj[0].shapedef)

    def test_write_ellipsoid_shapedef(self):
        # Write to / read from a temp file
        tmpfile = tempfile.NamedTemporaryFile(mode='wb')

        with tmpfile:
            with garnett.read(get_filename('shapes/ellipsoid_3d.pos')) as traj:
                self.writer.write(traj, tmpfile)
                written_traj = self.reader.read(tmpfile)
                assertEqualShapedefs(written_traj[0].shapedef, traj[0].shapedef)

    def test_write_defaults(self):
        tmpfile = tempfile.NamedTemporaryFile(mode='wb')
        with tmpfile:
            with garnett.read(get_filename('shapes/ellipsoid_3d.pos')) as traj:
                self.writer.write(traj, tmpfile)
                written_traj = self.reader.read(tmpfile)
                assert np.array_equal(written_traj[0].mass, np.ones(27).astype(float))
                assert np.array_equal(written_traj[0].velocity, np.zeros([27, 3]).astype(float))
                assert np.array_equal(written_traj[0].diameter, np.ones(27).astype(float))
                assert np.array_equal(written_traj[0].moment_inertia, np.zeros([27, 3]).astype(float))
                assert np.array_equal(written_traj[0].angmom, np.zeros([27, 4]).astype(float))
                assert np.array_equal(written_traj[0].charge, np.zeros([27]).astype(float))
                assert np.array_equal(written_traj[0].image, np.zeros([27, 3]).astype(np.int32))


if __name__ == '__main__':
    unittest.main()
