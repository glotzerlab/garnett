import sys
import io
import unittest

import numpy as np

import garnett


PYTHON_2 = sys.version_info[0] == 2


class BaseHOOMDXMLFileReaderTest(unittest.TestCase):

    def read_trajectory(self, sample_file):
        reader = garnett.reader.HOOMDXMLFileReader()
        if PYTHON_2:
            return reader.read(io.StringIO(unicode(sample_file)))  # noqa
        else:
            return reader.read(
                io.StringIO(sample_file))

    def test_read_3d(self):
        traj = self.read_trajectory(garnett.samples.HOOMD_BLUE_XML)
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

        self.assertTrue(np.all([frame.box.dimensions == 3 for frame in traj]))

    def test_read_2d(self):
        traj = self.read_trajectory(garnett.samples.HOOMD_BLUE_XML_2D)
        self.assertEqual(len(traj), 1)
        self.assertEqual(len(traj[0]), 10)
        self.assertTrue(np.allclose(traj[0].positions, np.array([
               [-0.391116261482, 2.34347701073, 0],
               [2.03885579109, -2.35620737076, 0],
               [-0.931703925133, 2.35222411156, 0],
               [-1.24394273758, -1.92150914669, 0],
               [-1.47881031036, -0.528331875801, 0],
               [0.800096750259, -0.486585855484, 0],
               [0.182962417603, 1.63233399391, 0],
               [-0.880133986473, 0.873030900955, 0],
               [-1.39306223392, -0.266534328461, 0],
               [-1.27463591099, -2.22765517235, 0],
           ])))
        self.assertTrue(np.allclose(traj[0].velocities, np.array([
               [-0.391116261482, 2.34347701073, 0],
               [2.03885579109, -2.35620737076, 0],
               [-0.931703925133, 2.35222411156, 0],
               [-1.24394273758, -1.92150914669, 0],
               [-1.47881031036, -0.528331875801, 0],
               [0.800096750259, -0.486585855484, 0],
               [0.182962417603, 1.63233399391, 0],
               [-0.880133986473, 0.873030900955, 0],
               [-1.39306223392, -0.266534328461, 0],
               [-1.27463591099, -2.22765517235, 0],
           ])))
        self.assertTrue(np.allclose(
               np.asarray(traj[0].box.get_box_matrix()),
               np.array([
                   [4.713492870331, 0, 0],
                   [0, 4.713492870331, 0],
                   [0, 0, 1.0]])))

        self.assertTrue(np.all([frame.box.dimensions == 2 for frame in traj]))


if __name__ == '__main__':
    unittest.main()
