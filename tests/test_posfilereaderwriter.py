import unittest
import os
import sys
import io
import warnings
import tempfile
import subprocess
from itertools import chain

from ddt import ddt, data

import glotzformats
import numpy as np

PYTHON_2 = sys.version_info[0] == 2

PATH = os.path.join(glotzformats.__path__[0], '..')
IN_PATH = os.path.abspath(PATH) == os.path.abspath(os.getcwd())


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

if HOOMD:
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


class BasePosFileReaderTest(unittest.TestCase):

    def read_trajectory(self, stream, precision=None):
        reader = glotzformats.reader.PosFileReader(precision=precision)
        return reader.read(stream)


class BasePosFileWriterTest(BasePosFileReaderTest):

    def dump_trajectory(self, trajectory):
        writer = glotzformats.writer.PosFileWriter()
        return writer.dump(trajectory)

    def write_trajectory(self, trajectory, file, rotate=False):
        writer = glotzformats.writer.PosFileWriter(rotate=rotate)
        return writer.write(trajectory, file)

    def assert_approximately_equal_frames(self, a, b,
                                          decimals=6, atol=1e-5, ignore_orientations=False):
        self.assertEqual(a.box.round(decimals), b.box.round(decimals))
        self.assertEqual(a.types, b.types)
        self.assertTrue(np.allclose(a.positions, b.positions, atol=atol))
        self.assertTrue(np.allclose(a.velocities, b.velocities, atol=atol))
        if not ignore_orientations:
            self.assertTrue(np.allclose(a.orientations, b.orientations, atol=atol))
        self.assertEqual(a.data, b.data)
        for key in chain(a.shapedef, b.shapedef):
            self.assertEqual(a.shapedef[key], b.shapedef[key])


class PosFileReaderTest(BasePosFileReaderTest):

    def test_read_empty(self):
        if PYTHON_2:
            empty_sample = io.StringIO(unicode(''))  # noqa
        else:
            empty_sample = io.StringIO("")
        with self.assertRaises(glotzformats.errors.ParserError):
            self.read_trajectory(empty_sample)

    @unittest.skipIf(PYTHON_2, 'requires python 3')
    def test_read_garbage(self):
        garbage_sample = io.StringIO(str(os.urandom(1024 * 100)))
        with self.assertRaises(glotzformats.errors.ParserError):
            self.read_trajectory(garbage_sample)

    def test_hpmc_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_HPMC))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_HPMC)
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'] * N)
            self.assertEqual(frame.box, box_expected)

    def test_incsim_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INCSIM))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_INCSIM)
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'] * N)
            self.assertEqual(frame.box, box_expected)

    def test_monotype_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_MONOTYPE))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_MONOTYPE)
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'] * N)
            self.assertEqual(frame.box, box_expected)

    def test_injavis_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INJAVIS))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'] * N)
            self.assertEqual(frame.box, box_expected)


@unittest.skipIf(not HPMC, 'requires HPMC')
class HPMCPosFileReaderTest(BasePosFileReaderTest):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.fn_pos = os.path.join(self.tmp_dir.name, 'test.pos')

    def del_system(self):
        del self.system

    def del_mc(self):
        del self.mc

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
        self.system.particles[0].position = (0, 0, 0)
        self.system.particles[0].orientation = (1, 0, 0, 0)
        self.system.particles[1].position = (2, 0, 0)
        self.system.particles[1].orientation = (1, 0, 0, 0)
        if HOOMD_v1:
            sorter.set_params(grid=8)
        else:
            context.current.sorter.set_params(grid=8)
        dump.pos(filename=self.fn_pos, period=1)
        run(10, quiet=True)
        with open(self.fn_pos, 'r', encoding='utf-8') as posfile:
            self.read_trajectory(posfile)

    def test_convex_polyhedron(self):
        if HOOMD_v1:
            from hoomd_script import init, sorter, data, dump, run
            from hoomd_plugins import hpmc
            self.system = init.create_empty(N=2, box=data.boxdim(
                L=10, dimensions=2), particle_types=['A'])
            self.addCleanup(init.reset)
        else:
            from hoomd import init, data, run, hpmc, context, lattice
            from hoomd.update import sort as sorter
            from hoomd.deprecated import dump
            self.system = init.create_lattice(
                unitcell=lattice.sq(10), n=(2, 1))
            self.addCleanup(context.initialize, "--mode=cpu")
        self.addCleanup(self.del_system)
        self.mc = hpmc.integrate.convex_polygon(seed=10)
        self.addCleanup(self.del_mc)
        self.mc.shape_param.set("A", vertices=[(-2, -1, -1),
                                               (-2, 1, -1),
                                               (-2, -1, 1),
                                               (-2, 1, 1),
                                               (2, -1, -1),
                                               (2, 1, -1),
                                               (2, -1, 1),
                                               (2, 1, 1)])
        self.system.particles[0].position = (0, 0, 0)
        self.system.particles[0].orientation = (1, 0, 0, 0)
        self.system.particles[1].position = (2, 0, 0)
        self.system.particles[1].orientation = (1, 0, 0, 0)
        if HOOMD_v1:
            sorter.set_params(grid=8)
        else:
            context.current.sorter.set_params(grid=8)
        pos_writer = dump.pos(filename=self.fn_pos, period=1)
        self.mc.setup_pos_writer(pos_writer)
        run(10, quiet=True)
        with open(self.fn_pos, 'r', encoding='utf-8') as posfile:
            self.read_trajectory(posfile)


@ddt
class PosFileWriterTest(BasePosFileWriterTest):

    def test_hpmc_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_HPMC))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_HPMC)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_incsim_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INCSIM))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_INCSIM)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_monotype_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_MONOTYPE))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_MONOTYPE)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_injavis_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INJAVIS))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_arrows(self):
        from glotzformats.trajectory import ArrowShapeDefinition
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INJAVIS))  # noqa
        else:
            sample = io.StringIO(glotzformats.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        traj.load()
        for frame in traj:
            frame.shapedef['A'] = ArrowShapeDefinition()
            frame.orientations.T[3] = 0
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)
        for frame in traj_cmp:
            self.assertTrue(isinstance(
                frame.shapedef['A'], ArrowShapeDefinition))

    @unittest.skipIf(not IN_PATH, 'tests not executed from repository root')
    @data(
        'hpmc_sphere',
        'hpmc_sphere_rotated',
        'FeSiUC',
        'Henzie_lithium_cubic_uc',
        'Henzie_lithium_triclinic',
        'cubic_onep',
        'cubic_twop',
        #'hex_onep',    # These tests are deactivated, because we currently
        #'hex_twop',    # do not have a solution to keep the reference orientation
        #'rand_test',   # the same. The systems are otherwise identical.
        'scc',
        'switch_FeSiUC',
        'switch_scc')
    def test_read_write_read(self, name):
        fn = os.path.join(PATH, 'samples', name + '.pos')
        with open(fn) as samplefile:
            traj0 = self.read_trajectory(samplefile)
            with tempfile.NamedTemporaryFile('w', suffix='.pos') as tmpfile:
                self.write_trajectory(traj0, tmpfile, rotate=False)
                tmpfile.flush()
                with open(tmpfile.name) as tmpfile_read:
                    traj1 = self.read_trajectory(tmpfile_read)
                    for f0, f1 in zip(traj0, traj1):
                        self.assert_approximately_equal_frames(f0, f1)

    @unittest.skipIf(not IN_PATH, 'tests not executed from repository root')
    @data(
        'hpmc_sphere',
        'hpmc_sphere_rotated',
        'xtalslice3_small',
        'FeSiUC',
        # For the following two, the box has a different sign...
        #'xtalslice3_small_rotated',
        #'switch_FeSiUC',
        )
    def test_read_write_read_rotated(self, name):
        fn = os.path.join(PATH, 'samples', name + '.pos')
        with open(fn) as samplefile:
            traj0 = self.read_trajectory(samplefile)
            with tempfile.NamedTemporaryFile('w', suffix='.pos') as tmpfile:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    self.write_trajectory(traj0, tmpfile, rotate=True)
                tmpfile.flush()
                with open(tmpfile.name) as tmpfile_read:
                    traj1 = self.read_trajectory(tmpfile_read)
                    for f0, f1 in zip(traj0, traj1):
                        self.assert_approximately_equal_frames(
                            f0, f1, decimals=4, atol=1e-6,
                            ignore_orientations=True # The shapes themselves are differently oriented
                            )


@unittest.skip("injavis is currently not starting correctly.")
class InjavisReadWriteTest(BasePosFileWriterTest):

    def read_write_injavis(self, sample):
        if PYTHON_2:
            sample_file = io.StringIO(unicode(glotzformats.samples.POS_HPMC))  # noqa
        else:
            sample_file = io.StringIO(glotzformats.samples.POS_HPMC)
        # account for low injavis precision
        traj0 = self.read_trajectory(sample_file, precision=7)
        with tempfile.NamedTemporaryFile('w', suffix='.pos') as tmpfile0:
            with tempfile.NamedTemporaryFile('r', suffix='.pos') as tmpfile1:
                self.write_trajectory(traj0, tmpfile0)
                tmpfile0.flush()
                subprocess.check_call(
                    ['injavis', tmpfile0.name, '-o', tmpfile1.name])
                traj1 = self.read_trajectory(tmpfile1)
        # Injavis only writes last frame
        frame0 = traj0[-1]
        frame1 = traj1[-1]
        # Injavis apparently ignores the color specification when writing
        for frame in (frame0, frame1):
            for name, shapedef in frame.shapedef.items():
                shapedef.color = None
        self.assertEqual(frame0, frame1)

    def test_hpmc_dialect(self):
        self.read_write_injavis(glotzformats.samples.POS_HPMC)

    def test_incsim_dialect(self):
        self.read_write_injavis(glotzformats.samples.POS_INCSIM)

    def test_monotype_dialect(self):
        self.read_write_injavis(glotzformats.samples.POS_MONOTYPE)

    def test_injavis_dialect(self):
        self.read_write_injavis(glotzformats.samples.POS_INJAVIS)


if __name__ == '__main__':
    context.initialize("--mode=cpu")
    unittest.main()
