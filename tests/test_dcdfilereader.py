import sys
import io
import unittest
import base64
import tempfile

import numpy as np

import glotzformats

try:
    import mdtraj  # noqa
except ImportError:
    DCD = False
else:
    DCD = True

PYTHON_2 = sys.version_info[0] == 2


@unittest.skipIf(not DCD, 'requires mdtraj')
class BaseDCDFileReaderTest(unittest.TestCase):

    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.addCleanup(self.tmpfile.close)

    def read_top_trajectory(self):
        top_reader = glotzformats.reader.HoomdBlueXMLFileReader()
        if PYTHON_2:
            return top_reader.read(io.StringIO(
                unicode(glotzformats.samples.HOOMD_BLUE_XML)))  # noqa
        else:
            return top_reader.read(
                io.StringIO(glotzformats.samples.HOOMD_BLUE_XML))

    def test_read(self):
        top_traj = self.read_top_trajectory()
        dcd_reader = glotzformats.reader.DCDFileReader()
        with tempfile.NamedTemporaryFile('wb') as file:
            file.write(base64.b64decode(glotzformats.samples.DCD_BASE64))
            file.flush()
            with open(file.name, 'rb') as dcdfile:
                traj = dcd_reader.read(dcdfile, top_traj[0])

                self.assertEqual(len(traj), 10)
                self.assertEqual(len(traj[0]), 10)
                self.assertTrue(np.allclose(traj[-1].positions, np.array([
                        [0.9789905,   2.20919244, -0.36870473],
                        [-1.65239301, -2.22119333,  1.9220265],
                        [-1.56960593,  2.21743834, -0.878316],
                        [-0.45953348, -1.81140399, -1.17266306],
                        [-0.68623599, -0.49805771, -1.39407237],
                        [1.9352755, -0.45870381,  0.75425008],
                        [-0.35905132,  1.53879893,  0.17247841],
                        [0.10907743,  0.82300503, -0.8297011],
                        [1.68012829, -0.25126153, -1.31323787],
                        [0.15291491, -2.10000738, -1.20159748]
                    ])))
                self.assertTrue(np.allclose(
                    np.asarray(traj[0].box.get_box_matrix()),
                    np.array([
                        [4.713492870331, 0, 0],
                        [0, 4.713492870331, 0],
                        [0, 0, 4.713492870331]])))


if __name__ == '__main__':
    unittest.main()
