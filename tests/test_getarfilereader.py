import unittest
import os
import sys
import json

import numpy as np
import glotzformats

try:
    import gtar
except ImportError:
    GTAR = False
else:
    GTAR = True

PYTHON_2 = sys.version_info[0] == 2
if PYTHON_2:
    from tempdir import TemporaryDirectory
else:
    from tempfile import TemporaryDirectory


@unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
class BaseGetarFileReaderTest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = TemporaryDirectory(prefix='glotzformats_getar_tmp')
        self.addCleanup(self.tmp_dir.cleanup)
        self.getar_file_fn = os.path.join(self.tmp_dir.name, 'sample.tar')

    def setup_sample(self, N, dim=3):
        self.positions = np.random.rand(N, 3)
        self.orientations = np.random.rand(N, 4)
        self.velocities = np.random.rand(N, 3)
        self.mass = np.random.rand(N)
        self.charge = np.random.rand(N)
        self.diameter = np.random.rand(N)
        self.moment_inertia = np.random.rand(N, 3)
        self.angmom = np.random.rand(N, 4)
        types = N // 2 * [0] + (N - N // 2) * [1]
        type_names = ['A', 'B']
        self.box = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
        self.types = [type_names[t] for t in types]
        if dim == 2:
            self.positions[:,2]  = 0
            self.velocities[:,2] = 0

        with gtar.GTAR(self.getar_file_fn, 'w') as traj:
            traj.writePath('frames/0/position.f32.ind', self.positions)
            traj.writePath('frames/0/orientation.f32.ind', self.orientations)
            traj.writePath('frames/0/velocity.f32.ind', self.velocities)
            traj.writePath('frames/0/mass.f32.ind', self.mass)
            traj.writePath('frames/0/charge.f32.ind', self.charge)
            traj.writePath('frames/0/diameter.f32.ind', self.diameter)
            traj.writePath('frames/0/moment_inertia.f32.ind', self.moment_inertia)
            traj.writePath('frames/0/angular_momentum_quat.f32.ind', self.angmom)
            traj.writePath('frames/0/box.f32.ind', self.box)
            traj.writePath('type.u32.ind', types)
            traj.writePath('type_names.json', json.dumps(type_names))

    def read_trajectory(self):
        reader = glotzformats.reader.GetarFileReader()
        self.getarfile = open(self.getar_file_fn, 'rb')
        self.addCleanup(self.getarfile.close)
        return reader.read(self.getarfile)

    def test_read_3d(self):
        N = 100
        self.setup_sample(N, dim=3)
        traj = self.read_trajectory()
        self.assertEqual(len(traj), 1)
        frame = traj[0]
        self.assertEqual(len(frame), N)
        self.assertEqual(frame.box, glotzformats.trajectory.Box(1.0, 1.0, 1.0))
        self.assertEqual(frame.box.dimensions, 3)
        np.testing.assert_allclose(frame.positions, self.positions)
        np.testing.assert_allclose(frame.orientations, self.orientations)
        np.testing.assert_allclose(frame.velocities, self.velocities)
        np.testing.assert_allclose(frame.mass, self.mass)
        np.testing.assert_allclose(frame.charge, self.charge)
        np.testing.assert_allclose(frame.diameter, self.diameter)
        np.testing.assert_allclose(frame.moment_inertia, self.moment_inertia)
        np.testing.assert_allclose(frame.angmom, self.angmom)
        self.assertEqual(frame.types, self.types)

    def test_read_2d(self):
        N = 100
        self.setup_sample(N, dim=2)
        traj = self.read_trajectory()
        self.assertEqual(len(traj), 1)
        frame = traj[0]
        self.assertEqual(len(frame), N)
        self.assertEqual(frame.box, glotzformats.trajectory.Box(1.0, 1.0, 1.0, dimensions=2))
        self.assertEqual(frame.box.dimensions, 2)
        np.testing.assert_allclose(frame.positions, self.positions)
        np.testing.assert_allclose(frame.orientations, self.orientations)
        np.testing.assert_allclose(frame.velocities, self.velocities)
        np.testing.assert_allclose(frame.mass, self.mass)
        np.testing.assert_allclose(frame.charge, self.charge)
        np.testing.assert_allclose(frame.diameter, self.diameter)
        np.testing.assert_allclose(frame.moment_inertia, self.moment_inertia)
        np.testing.assert_allclose(frame.angmom, self.angmom)
        self.assertEqual(frame.types, self.types)

@unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
class NoTypesGetarFileReaderTest(BaseGetarFileReaderTest):
    """This test makes sure that when angle (or other non-particle) types
    are stored in a file, they do not get interpreted as particle
    types."""

    def setup_sample(self, N, dim=3):
        self.positions = np.random.rand(N, 3)
        self.orientations = np.random.rand(N, 4)
        self.velocities = np.random.rand(N, 3)
        self.mass = np.random.rand(N)
        self.charge = np.random.rand(N)
        self.diameter = np.random.rand(N)
        self.moment_inertia = np.random.rand(N, 3)
        self.angmom = np.random.rand(N, 4)
        self.box = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
        self.types = N*['A']
        if dim == 2:
            self.positions[:,2]  = 0
            self.velocities[:,2] = 0

        with gtar.GTAR(self.getar_file_fn, 'w') as traj:
            traj.writePath('frames/0/position.f32.ind', self.positions)
            traj.writePath('frames/0/orientation.f32.ind', self.orientations)
            traj.writePath('frames/0/velocity.f32.ind', self.velocities)
            traj.writePath('frames/0/mass.f32.ind', self.mass)
            traj.writePath('frames/0/charge.f32.ind', self.charge)
            traj.writePath('frames/0/diameter.f32.ind', self.diameter)
            traj.writePath('frames/0/moment_inertia.f32.ind', self.moment_inertia)
            traj.writePath('frames/0/angular_momentum_quat.f32.ind', self.angmom)
            traj.writePath('frames/0/box.f32.ind', self.box)
            traj.writePath('angle/type.u32.ind', [0])
            traj.writePath('angle/type_names.json', '["Angle_A"]')


if __name__ == '__main__':
    unittest.main()
