import sys
import io
import unittest

import numpy as np

import glotzformats


PYTHON_2 = sys.version_info[0] == 2


class BaseHOOMDXMLFileReaderTest(unittest.TestCase):

    def read_trajectory(self):
        reader = glotzformats.reader.HOOMDXMLFileReader()
        if PYTHON_2:
            return reader.read(io.StringIO(
                unicode(glotzformats.samples.HOOMD_BLUE_XML)))  # noqa
        else:
            return reader.read(
                io.StringIO(glotzformats.samples.HOOMD_BLUE_XML))

    def assert_raise_attribute_error(self,frame):
        with self.assertRaises(AttributeError):
            frame.orientations;
        with self.assertRaises(AttributeError):
            frame.moment_inertia;
        with self.assertRaises(AttributeError):
            frame.angmom;
        with self.assertRaises(AttributeError):
            frame.image;
        with self.assertRaises(AttributeError):
            frame.view_rotation;

    def test_read(self):
        traj = self.read_trajectory()
        self.assertEqual(len(traj), 1)
        self.assertEqual(len(traj[0]), 10)
        self.assertTrue(np.allclose(traj[0].positions, np.array([
            [-0.391116261482, 2.34347701073, 1.0384979248],
            [2.03885579109, -2.35620737076, -1.75283277035],
            [-0.931703925133, 2.35222411156, -1.66501355171],
            [-1.24394273758, -1.92150914669, -0.487465977669],
            [-1.47881031036, -0.528331875801, -0.7279484272],
            [0.800096750259, -0.486585855484, 2.05291008949],
            [0.182962417603, 1.63233399391, -0.380876064301],
            [-0.880133986473, 0.873030900955, 0.11570763588],
            [-1.39306223392, -0.266534328461, 1.78225398064],
            [-1.27463591099, -2.22765517235, 0.162209749222],
        ])))
        self.assertTrue(np.allclose(traj[0].velocities, np.array([
            [-0.391116261482, 2.34347701073, 1.0384979248],
            [2.03885579109, -2.35620737076, -1.75283277035],
            [-0.931703925133, 2.35222411156, -1.66501355171],
            [-1.24394273758, -1.92150914669, -0.487465977669],
            [-1.47881031036, -0.528331875801, -0.7279484272],
            [0.800096750259, -0.486585855484, 2.05291008949],
            [0.182962417603, 1.63233399391, -0.380876064301],
            [-0.880133986473, 0.873030900955, 0.11570763588],
            [-1.39306223392, -0.266534328461, 1.78225398064],
            [-1.27463591099, -2.22765517235, 0.162209749222],
        ])))
        self.assertTrue(np.allclose(
            np.asarray(traj[0].box.get_box_matrix()),
            np.array([
                [4.713492870331, 0, 0],
                [0, 4.713492870331, 0],
                [0, 0, 4.713492870331]])))

        self.assert_raise_attribute_error(traj[0]);

if __name__ == '__main__':
    unittest.main()
