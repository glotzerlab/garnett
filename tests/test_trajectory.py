import sys
import io
import unittest
import tempfile

import garnett
import numpy as np

PYTHON_2 = sys.version_info[0] == 2


try:
    try:
        from hoomd import context
        import hoomd
    except ImportError:
        from hoomd_script import context
        HOOMD_v1 = True
    else:
        HOOMD_v1 = False
        hoomd.util.quiet_status()
except ImportError:
    HOOMD = False
else:
    HOOMD = True


if HOOMD:
    context.initialize('--mode=cpu')
    if not HOOMD_v1:
        hoomd.option.set_notice_level(0)
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
    sample = garnett.samples.POS_HPMC
    reader = garnett.reader.PosFileReader

    def read_trajectory(self, stream, precision=None):
        reader = garnett.reader.PosFileReader(precision=precision)
        return reader.read(stream)

    def get_trajectory(self, sample=garnett.samples.POS_HPMC):
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
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        str(traj)

    def test_frame_inheritance(self):
        from garnett.trajectory import Frame
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
                            garnett.trajectory.DEFAULT_DTYPE)
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
        if traj.positions is not None and None not in traj.positions:
            self.assertTrue(np.issubdtype(
                traj.positions.dtype, garnett.trajectory.DEFAULT_DTYPE))
            self.assertEqual(traj.positions.shape, (len(traj), len(traj[0]), 3))
            self.assertTrue((traj.positions[0] == traj[0].positions).all())
            with self.assertRaises(ValueError):
                traj[0].positions = 'hello'
            with self.assertRaises(ValueError):
                # This should fail since it's using 2d positions
                traj[0].positions = [[0, 0], [0, 0]]

    def test_orientations(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.orientations
        traj.load_arrays()
        if traj.orientations is not None and None not in traj.orientations:
            if len(traj.orientations.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.orientations.dtype, garnett.trajectory.DEFAULT_DTYPE))
                self.assertEqual(traj.orientations.shape,
                                 (len(traj), len(traj[0]), 4))
                self.assertTrue((traj.orientations[0] == traj[0].orientations).all())
            with self.assertRaises(ValueError):
                traj[0].orientations = 'hello'
            with self.assertRaises(ValueError):
                # This should fail since it's using 2d positions
                traj[0].orientations = [[0, 0], [0, 0]]

    def test_velocities(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.velocities
        traj.load_arrays()
        if traj.velocities is not None and None not in traj.velocities:
            if len(traj.velocities.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.velocities.dtype, garnett.trajectory.DEFAULT_DTYPE))
                self.assertEqual(traj.velocities.shape,
                                 (len(traj), len(traj[0]), 3))
                self.assertTrue((traj.velocities[0] == traj[0].velocities).all())
            with self.assertRaises(ValueError):
                traj[0].velocities = 'hello'
            with self.assertRaises(ValueError):
                # This should fail since it's using 2d velocities
                traj[0].velocities = [[0, 0], [0, 0]]

    def test_mass(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.mass
        traj.load_arrays()
        if traj.mass is not None and None not in traj.mass:
            if len(traj.mass.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.mass.dtype, garnett.trajectory.DEFAULT_DTYPE))
                self.assertEqual(traj.mass.shape,
                                 (len(traj), len(traj[0])))
                self.assertTrue((traj.mass[0] == traj[0].mass).all())
            with self.assertRaises(ValueError):
                traj[0].mass = 'hello'
            with self.assertRaises(ValueError):
                # This should fail since the array is not a 1-D list
                traj[0].mass = [[1, 1]]

    def test_charge(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.charge
        traj.load_arrays()
        if traj.charge is not None and None not in traj.charge:
            if len(traj.charge.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.charge.dtype, garnett.trajectory.DEFAULT_DTYPE))
                self.assertEqual(traj.charge.shape,
                                 (len(traj), len(traj[0])))
                self.assertTrue((traj.charge[0] == traj[0].charge).all())
            with self.assertRaises(ValueError):
                traj[0].charge = 'hello'
            with self.assertRaises(ValueError):
                # This should fail since the array is not a 1-D list
                traj[0].charge = [[1, 1]]

    def test_diameter(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.diameter
        traj.load_arrays()
        if traj.diameter is not None and None not in traj.diameter:
            if len(traj.diameter.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.diameter.dtype, garnett.trajectory.DEFAULT_DTYPE))
                self.assertEqual(traj.diameter.shape,
                                 (len(traj), len(traj[0])))
                self.assertTrue((traj.diameter[0] == traj[0].diameter).all())
            with self.assertRaises(ValueError):
                traj[0].diameter = 'hello'
            with self.assertRaises(ValueError):
                # This should fail since the array is not a 1-D list
                traj[0].diameter = [[1, 1]]

    def test_moment_inertia(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.moment_inertia
        traj.load_arrays()
        if traj.moment_inertia is not None and None not in traj.moment_inertia:
            if len(traj.moment_inertia.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.moment_inertia.dtype, garnett.trajectory.DEFAULT_DTYPE))
                self.assertEqual(traj.moment_inertia.shape,
                                 (len(traj), len(traj[0]), 3))
                self.assertTrue((traj.moment_inertia[0] == traj[0].moment_inertia).all())
            with self.assertRaises(ValueError):
                traj[0].moment_inertia = 'hello'

    def test_angmom(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.angmom
        traj.load_arrays()
        if traj.angmom is not None and None not in traj.angmom:
            if len(traj.angmom.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.angmom.dtype, garnett.trajectory.DEFAULT_DTYPE))
                self.assertEqual(traj.angmom.shape,
                                 (len(traj), len(traj[0]), 4))
                self.assertTrue((traj.angmom[0] == traj[0].angmom).all())
            with self.assertRaises(ValueError):
                traj[0].angmom = 'hello'

    def test_image(self):
        sample_file = self.get_sample_file()
        traj = self.reader().read(sample_file)
        with self.assertRaises(RuntimeError):
            traj.image
        traj.load_arrays()
        if traj.image is not None and None not in traj.image:
            if len(traj.image.shape) > 1:
                self.assertTrue(np.issubdtype(
                    traj.image.dtype, np.int32))
                self.assertEqual(traj.image.shape,
                                 (len(traj), len(traj[0]), 3))
                self.assertTrue((traj.image[0] == traj[0].image).all())
            with self.assertRaises(ValueError):
                traj[0].image = 'hello'


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
        snapshot = self.make_snapshot(garnett.samples.POS_HPMC)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 10.0)
        self.assertEqual(snapshot.box.dimensions, 3)
        self.assertEqual(snapshot.particles.types, ['A'])

    def test_incsim_dialect(self):
        snapshot = self.make_snapshot(garnett.samples.POS_INCSIM)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 10.0)
        self.assertEqual(snapshot.box.dimensions, 3)
        self.assertEqual(snapshot.particles.types, ['A'])

    def test_monotype_dialect(self):
        snapshot = self.make_snapshot(garnett.samples.POS_MONOTYPE)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 10.0)
        self.assertEqual(snapshot.box.dimensions, 3)
        self.assertEqual(snapshot.particles.types, ['A'])

    def test_injavis_dialect(self):
        snapshot = self.make_snapshot(garnett.samples.POS_INJAVIS)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 10.0)
        self.assertEqual(snapshot.box.dimensions, 3)
        self.assertEqual(snapshot.particles.types, ['A'])

    def test_hpmc_dialect_2D(self):
        snapshot = self.make_snapshot(garnett.samples.POS_HPMC_2D)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 1.0)
        self.assertEqual(snapshot.box.dimensions, 2)
        self.assertEqual(snapshot.particles.types, ['A'])

    def test_incsim_dialect_2D(self):
        snapshot = self.make_snapshot(garnett.samples.POS_INCSIM_2D)
        self.assertEqual(snapshot.box.Lx, 10.0)
        self.assertEqual(snapshot.box.Ly, 10.0)
        self.assertEqual(snapshot.box.Lz, 1.0)
        self.assertEqual(snapshot.box.dimensions, 2)
        self.assertEqual(snapshot.particles.types, ['A'])

    def test_monotype_dialect_2D(self):
        snapshot = self.make_snapshot(garnett.samples.POS_MONOTYPE_2D)
        self.assertEqual(snapshot.box.Lx, 25.0)
        self.assertEqual(snapshot.box.Ly, 25.0)
        self.assertEqual(snapshot.box.Lz, 1.0)
        self.assertEqual(snapshot.box.dimensions, 2)
        self.assertEqual(snapshot.particles.types, ['A'])


if __name__ == '__main__':
    unittest.main()
