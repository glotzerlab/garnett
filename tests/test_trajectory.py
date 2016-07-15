import sys
import io
import unittest
import tempfile

import glotzformats
import numpy as np

PYTHON_2 = sys.version_info[0] == 2


try:
    try:
        from hoomd import context
    except ImportError:
        from hoomd_script import context
        HOOMD_v1 = True
    else:
        HOOMD_v1 = False
except ImportError:
    HOOMD = False
else:
    HOOMD = True
    HOOMD_v1 = True


if HOOMD:
    context.initialize('--mode=cpu')
    try:
        if HOOMD_v1:
            from hoomd_plugins import hpmc
        else:
            from hoomd import hpmc
    except ImportError:
        HPMC = False
    else:
        HPMC = True
else:
    HPMC = False


class TrajectoryTest(unittest.TestCase):
    sample = glotzformats.samples.POS_HPMC
    reader = glotzformats.reader.PosFileReader

    def read_trajectory(self, stream, precision=None):
        reader = glotzformats.reader.PosFileReader(precision=precision)
        return reader.read(stream)

    def get_trajectory(self, sample=glotzformats.samples.POS_HPMC):
        if PYTHON_2:
            sample_file = io.StringIO(unicode(sample))  # noqa
        else:
            sample_file = io.StringIO(sample)
        # account for low injavis precision
        return self.read_trajectory(sample_file)

    def get_sample_file(self):
        if PYTHON_2:
            return io.StringIO(unicode(self.sample))  # noqa
        else:
            return io.StringIO(self.sample)

    def test_str(self):
        from glotzformats.trajectory import Frame
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        str(traj)

    def test_frame_inheritance(self):
        from glotzformats.trajectory import Frame
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        for frame in traj:
            self.assertTrue(isinstance(frame, Frame))
        for i in range(len(traj)):
            self.assertTrue(isinstance(traj[i], Frame))

    def test_load(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        for i, frame in enumerate(traj):
            frame.load()
        self.assertEqual(len(traj), i + 1)
        sample_file.close()
        with self.assertRaises(ValueError):
            traj[0].load()
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        traj.load()
        sample_file.close()
        for i, frame in enumerate(traj):
            frame.load()
            self.assertTrue(frame.loaded())
        self.assertEqual(len(traj), i + 1)
        for frame in traj:
            self.assertTrue(frame.loaded())
        for i, frame in enumerate(traj):
            frame.load()
        self.assertEqual(len(traj), i + 1)

    def test_data_type_specification(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
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

    def test_N(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.types
        traj.load_arrays()
        self.assertTrue(np.issubdtype(traj.N.dtype, np.int_))
        N = np.array([len(f) for f in traj], dtype=np.int_)
        self.assertTrue((traj.N == N).all())

    def test_type(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.types
        traj.load_arrays()
        self.assertTrue(isinstance(traj.type, list))
        _type = sorted(set((t_ for f in traj for t_ in f.types)))
        self.assertEqual(traj.type, _type)

    def test_types(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.types
        traj.load_arrays()
        self.assertTrue(np.issubdtype(traj.types.dtype, np.str_))
        self.assertEqual(traj.types.shape, (len(traj), len(traj[0])))
        self.assertTrue((traj.types[0] == traj[0].types).all())

    def test_type_ids(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.types
        traj.load_arrays()
        self.assertTrue(np.issubdtype(traj.type_ids.dtype, np.int_))
        self.assertEqual(traj.type_ids.shape, (len(traj), len(traj[0])))
        type_ids_0 = [traj.type.index(t) for t in traj.types[0]]
        self.assertEqual(type_ids_0, traj.type_ids[0].tolist())

    def test_positions(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.positions
        traj.load_arrays()
        self.assertTrue(np.issubdtype(
            traj.positions.dtype, glotzformats.trajectory.DEFAULT_DTYPE))
        self.assertEqual(traj.positions.shape, (len(traj), len(traj[0]), 3))
        self.assertTrue((traj.positions[0] == traj[0].positions).all())

    def test_orientations(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.orientations
        traj.load_arrays()
        self.assertTrue(np.issubdtype(
            traj.orientations.dtype, glotzformats.trajectory.DEFAULT_DTYPE))
        self.assertEqual(traj.orientations.shape, (len(traj), len(traj[0]), 4))
        self.assertTrue((traj.orientations[0] == traj[0].orientations).all())


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

    @unittest.skipIf(not HPMC, 'requires HPMC')
    def test_sphere(self):
        if HOOMD_v1:
            from hoomd_script import init, sorter, data, dump, run
            self.system = init.create_empty(N=2, box=data.boxdim(
                L=10, dimensions=2), particle_types=['A'])
            self.addCleanup(init.reset)
        else:
            from hoomd import init, data, run, context, lattice
            from hoomd.update import sort as sorter
            from hoomd.deprecated import dump
            self.system = init.create_lattice(
                unitcell=lattice.sq(10), n=(2, 1))
            self.addCleanup(context.initialize, "--mode=cpu")
        self.addCleanup(self.del_system)
        self.mc = hpmc.integrate.sphere(seed=10)
        self.mc.shape_param.set("A", diameter=1.0)
        self.addCleanup(self.del_mc)
        self.system.particles[0].position = (1, 0, 0)
        self.system.particles[0].orientation = (1, 0, 0, 0)
        self.system.particles[1].position = (2, 0, 0)
        self.system.particles[1].orientation = (1, 0, 0, 0)
        if HOOMD_v1:
            sorter.set_params(grid=8)
        else:
            context.current.sorter.set_params(grid=8)
        with tempfile.NamedTemporaryFile('r') as tmpfile:
            pos = dump.pos(filename=tmpfile.name, period=1)
            run(10, quiet=True)
            snapshot0 = self.system.take_snapshot()
            run(1, quiet=True)  # the hoomd pos-writer lags by one sweep
            tmpfile.flush()
            traj = self.read_trajectory(tmpfile)
            f_1 = traj[-1]
            # Pos-files don't support box dimensions.
            f_1.box.dimensions = self.system.box.dimensions
            snapshot1 = f_1.make_snapshot()
            self.assert_snapshots_equal(snapshot0, snapshot1)
            self.system.restore_snapshot(snapshot1)
            pos.disable()
            run(1, quiet=True)  # sanity check

    def test_hpmc_dialect(self):
        snapshot = self.make_snapshot(glotzformats.samples.POS_HPMC)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 10.0)
        self.assertEqual(snapshot.particles.types, ['A'])

    def test_incsim_dialect(self):
        self.make_snapshot(glotzformats.samples.POS_INCSIM)

    def test_monotype_dialect(self):
        self.make_snapshot(glotzformats.samples.POS_MONOTYPE)

    def test_injavis_dialect(self):
        self.make_snapshot(glotzformats.samples.POS_INJAVIS)

if __name__ == '__main__':
    unittest.main()
