import sys
import io
import unittest
import base64
import tempfile

import numpy as np

import glotzformats
from test_trajectory import TrajectoryTest

PYTHON_2 = sys.version_info[0] == 2


class BaseGSDHOOMDFileReaderTest(TrajectoryTest):
    reader = glotzformats.reader.GSDHOOMDFileReader

    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.addCleanup(self.tmpfile.close)

    def get_sample_file(self):
        return io.BytesIO(base64.b64decode(glotzformats.samples.GSD_BASE64))

    def read_top_trajectory(self):
        top_reader = glotzformats.reader.HOOMDXMLFileReader()
        if PYTHON_2:
            return top_reader.read(io.StringIO(
                unicode(glotzformats.samples.HOOMD_BLUE_XML)))  # noqa
        else:
            return top_reader.read(
                io.StringIO(glotzformats.samples.HOOMD_BLUE_XML))

    def get_traj(self):
        top_traj = self.read_top_trajectory()
        gsd_reader = self.reader()
        gsdfile = io.BytesIO(base64.b64decode(glotzformats.samples.GSD_BASE64))
        return gsd_reader.read(gsdfile, top_traj[0])

    def test_read(self):
        traj = self.get_traj()
        self.assertEqual(len(traj), 10)
        self.assertEqual(len(traj[0]), 100)
        self.assertTrue(np.allclose(
            np.asarray(traj[0].box.get_box_matrix()),
            np.array([[8.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]])))
        self.assertTrue(np.allclose(traj[0].positions, np.array([
         [-3., -4., -4.],
         [-3., -4., -2.],
         [-3., -4.,  0.],
         [-3., -4.,  2.],
         [-3., -4.,  4.],
         [-3., -2., -4.],
         [-3., -2., -2.],
         [-3., -2.,  0.],
         [-3., -2.,  2.],
         [-3., -2.,  4.],
         [-3.,  0., -4.],
         [-3.,  0., -2.],
         [-3.,  0.,  0.],
         [-3.,  0.,  2.],
         [-3.,  0.,  4.],
         [-3.,  2., -4.],
         [-3.,  2., -2.],
         [-3.,  2.,  0.],
         [-3.,  2.,  2.],
         [-3.,  2.,  4.],
         [-3.,  4., -4.],
         [-3.,  4., -2.],
         [-3.,  4.,  0.],
         [-3.,  4.,  2.],
         [-3.,  4.,  4.],
         [-1., -4., -4.],
         [-1., -4., -2.],
         [-1., -4.,  0.],
         [-1., -4.,  2.],
         [-1., -4.,  4.],
         [-1., -2., -4.],
         [-1., -2., -2.],
         [-1., -2.,  0.],
         [-1., -2.,  2.],
         [-1., -2.,  4.],
         [-1.,  0., -4.],
         [-1.,  0., -2.],
         [-1.,  0.,  0.],
         [-1.,  0.,  2.],
         [-1.,  0.,  4.],
         [-1.,  2., -4.],
         [-1.,  2., -2.],
         [-1.,  2.,  0.],
         [-1.,  2.,  2.],
         [-1.,  2.,  4.],
         [-1.,  4., -4.],
         [-1.,  4., -2.],
         [-1.,  4.,  0.],
         [-1.,  4.,  2.],
         [-1.,  4.,  4.],
         [1., -4., -4.],
         [1., -4., -2.],
         [1., -4.,  0.],
         [1., -4.,  2.],
         [1., -4.,  4.],
         [1., -2., -4.],
         [1., -2., -2.],
         [1., -2.,  0.],
         [1., -2.,  2.],
         [1., -2.,  4.],
         [1.,  0., -4.],
         [1.,  0., -2.],
         [1.,  0.,  0.],
         [1.,  0.,  2.],
         [1.,  0.,  4.],
         [1.,  2., -4.],
         [1.,  2., -2.],
         [1.,  2.,  0.],
         [1.,  2.,  2.],
         [1.,  2.,  4.],
         [1.,  4., -4.],
         [1.,  4., -2.],
         [1.,  4.,  0.],
         [1.,  4.,  2.],
         [1.,  4.,  4.],
         [3., -4., -4.],
         [3., -4., -2.],
         [3., -4.,  0.],
         [3., -4.,  2.],
         [3., -4.,  4.],
         [3., -2., -4.],
         [3., -2., -2.],
         [3., -2.,  0.],
         [3., -2.,  2.],
         [3., -2.,  4.],
         [3.,  0., -4.],
         [3.,  0., -2.],
         [3.,  0.,  0.],
         [3.,  0.,  2.],
         [3.,  0.,  4.],
         [3.,  2., -4.],
         [3.,  2., -2.],
         [3.,  2.,  0.],
         [3.,  2.,  2.],
         [3.,  2.,  4.],
         [3.,  4., -4.],
         [3.,  4., -2.],
         [3.,  4.,  0.],
         [3.,  4.,  2.],
         [3.,  4.,  4.]])))


if __name__ == '__main__':
    unittest.main()
