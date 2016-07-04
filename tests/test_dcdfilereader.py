import sys
import io
import unittest
import base64
import tempfile

import numpy as np

import glotzformats
from test_trajectory import TrajectoryTest

PYTHON_2 = sys.version_info[0] == 2


class BaseDCDFileReaderTest(TrajectoryTest):
    reader = glotzformats.reader.DCDFileReader

    def setUp(self):
        self.tmpfiles = []

    def close_tmp(self):
        self.tmpfiles.pop().close()

    def get_sample_file(self):
        tmp = tempfile.TemporaryFile()
        self.tmpfiles.append(tmp)
        self.addCleanup(self.close_tmp)
        tmp.write(base64.b64decode(glotzformats.samples.DCD_BASE64))
        tmp.flush()
        tmp.seek(0)
        return tmp

    def read_top_trajectory(self):
        top_reader = glotzformats.reader.HoomdBlueXMLFileReader()
        if PYTHON_2:
            return top_reader.read(io.StringIO(
                unicode(glotzformats.samples.HOOMD_BLUE_XML)))  # noqa
        else:
            return top_reader.read(
                io.StringIO(glotzformats.samples.HOOMD_BLUE_XML))

    def get_traj(self):
        top_traj = self.read_top_trajectory()
        return self.reader().read(self.get_sample_file(), top_traj[0])

    def test_read(self):
        top_traj = self.read_top_trajectory()
        traj = self.get_traj()
        self.assertEqual(len(traj), 10)
        self.assertEqual(len(traj[0]), 10)
        self.assertEqual(traj[0].types, ['A'] * 10)
        self.assertTrue(np.allclose(
            np.asarray(traj[0].box.get_box_matrix()),
            np.array([
                [4.713492870331, 0, 0],
                [0, 4.713492870331, 0],
                [0, 0, 4.713492870331]])))
        self.assertTrue(np.allclose(traj[-1].positions, np.array([
            [1.0384979248, 2.34347701073, -0.391116261482],
            [-1.75283277035, -2.35620737076, 2.03885579109],
            [-1.66501355171, 2.35222411156, -0.931703925133],
            [-0.487465977669, -1.92150914669, -1.24394273758],
            [-0.7279484272, -0.528331875801, -1.47881031036],
            [2.05291008949, -0.486585855484, 0.800096750259],
            [-0.380876064301, 1.63233399391, 0.182962417603],
            [0.11570763588, 0.873030900955, -0.880133986473],
            [1.78225398064, -0.266534328461, -1.39306223392],
            [0.162209749222, -2.22765517235, -1.27463591099]])))


if __name__ == '__main__':
    unittest.main()
