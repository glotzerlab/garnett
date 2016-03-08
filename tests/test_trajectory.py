import sys
import io
import unittest
import tempfile

import glotzformats
import numpy as np

PYTHON_2 = sys.version_info[0] == 2

try:
    from hoomd_script import context
except ImportError:
    HOOMD = False
else:
    HOOMD = True


class TrajectoryTest(unittest.TestCase):

    def read_trajectory(self, stream, precision=None):
        reader = glotzformats.reader.PosFileReader(precision=precision)
        return reader.read(stream)

    def get_trajectory(self, sample):
        if PYTHON_2:
            sample_file = io.StringIO(unicode(sample))  # noqa
        else:
            sample_file = io.StringIO(sample)
        # account for low injavis precision
        return self.read_trajectory(sample_file)

    def test_load(self):
        sample = glotzformats.samples.POS_HPMC
        if PYTHON_2:
            sample_file = io.StringIO(unicode(sample))  # noqa
        else:
            sample_file = io.StringIO(sample)
        traj = glotzformats.reader.PosFileReader().read(sample_file)
        for i, frame in enumerate(traj):
            frame.load()
        self.assertEqual(len(traj), i + 1)
        sample_file.close()
        with self.assertRaises(ValueError):
            traj[0].load()
        if PYTHON_2:
            sample_file = io.StringIO(unicode(sample))  # noqa
        else:
            sample_file = io.StringIO(sample)
        traj = glotzformats.reader.PosFileReader().read(sample_file)
        traj.load()
        sample_file.close()
        for i, frame in enumerate(traj):
            frame.load()
        self.assertEqual(len(traj), i + 1)
        for i, frame in enumerate(traj):
            frame.load()
        self.assertEqual(len(traj), i + 1)

    def test_data_type_specification(self):
        sample = glotzformats.samples.POS_HPMC
        if PYTHON_2:
            sample_file = io.StringIO(unicode(sample))  # noqa
        else:
            sample_file = io.StringIO(sample)
        traj = glotzformats.reader.PosFileReader().read(sample_file)
        for frame in traj:
            self.assertTrue(isinstance(frame.positions, np.ndarray))
            self.assertTrue(frame.positions.dtype ==
                            glotzformats.trajectory.DEFAULT_DTYPE)
        for dtype in (np.float32, np.float64):
            traj.set_dtype(dtype)
            for frame in traj:
                self.assertTrue(isinstance(frame.positions, np.ndarray))
                self.assertTrue(frame.positions.dtype == dtype)
        traj.set_dtype(np.float32)
        frame0 = traj[0]
        self.assertTrue(frame0.positions.dtype == np.float32)
        frame0.load()
        self.assertTrue(isinstance(frame0.positions, np.ndarray))
        self.assertTrue(frame0.positions.dtype == np.float32)
        with self.assertRaises(RuntimeError):
            traj.set_dtype(np.float64)
        with self.assertRaises(RuntimeError):
            frame0.dtype = np.float64


@unittest.skipIf(not HOOMD, 'requires hoomd-blue')
class FrameSnapshotExport(TrajectoryTest):

    def make_snapshot(self, sample):
        traj = self.get_trajectory(sample)
        return traj[-1].make_snapshot()

    def del_system(self):
        del self.system

    def del_mc(self):
        del self.mc

    def assert_snapshots_equal(self, s0, s1):
        self.assertEqual(s0.particles.N, s1.particles.N)
        self.assertEqual(s0.box.get_metadata(), s1.box.get_metadata())
        self.assertTrue((s0.particles.position == s1.particles.position).all())
        self.assertTrue((s0.particles.orientation ==
                         s1.particles.orientation).all())

    def test_sphere(self):
        from hoomd_script import init, sorter, data, dump, run
        from hoomd_plugins import hpmc
        self.system = init.create_empty(N=2, box=data.boxdim(
            L=10, dimensions=3), particle_types=['A'])
        self.addCleanup(init.reset)
        self.addCleanup(self.del_system)
        self.mc = hpmc.integrate.sphere(seed=10)
        self.mc.shape_param.set("A", diameter=1.0)
        self.addCleanup(self.del_mc)
        self.system.particles[0].position = (1, 0, 0)
        self.system.particles[0].orientation = (1, 0, 0, 0)
        self.system.particles[1].position = (2, 0, 0)
        self.system.particles[1].orientation = (1, 0, 0, 0)
        sorter.set_params(grid=8)
        with tempfile.NamedTemporaryFile('r') as tmpfile:
            pos = dump.pos(filename=tmpfile.name, period=1)
            run(10, quiet=True)
            snapshot0 = self.system.take_snapshot()
            run(1, quiet=True)  # the hoomd pos-writer lags by one sweep
            tmpfile.flush()
            traj = self.read_trajectory(tmpfile)
            snapshot1 = traj[-1].make_snapshot()
            self.assert_snapshots_equal(snapshot0, snapshot1)
            self.system.restore_snapshot(snapshot1)
            pos.disable()
            run(1, quiet=True)  # sanity check

    def test_hpmc_dialect(self):
        snapshot = self.make_snapshot(glotzformats.samples.POS_HPMC)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 10.0)
        self.assertEqual(snapshot.particles.types, ['A'] * 3)

    def test_incsim_dialect(self):
        self.make_snapshot(glotzformats.samples.POS_INCSIM)

    def test_monotype_dialect(self):
        self.make_snapshot(glotzformats.samples.POS_MONOTYPE)

    def test_injavis_dialect(self):
        self.make_snapshot(glotzformats.samples.POS_INJAVIS)

if __name__ == '__main__':
    if HOOMD:
        context.initialize('--mode=cpu')
    unittest.main()
