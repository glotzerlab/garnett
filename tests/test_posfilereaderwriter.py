# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import unittest
import os
import io
import warnings
import tempfile
import subprocess
from itertools import chain
from ddt import ddt, data
import garnett
import numpy as np
from tempfile import TemporaryDirectory
import base64
from garnett.posfilewriter import DEFAULT_SHAPE_DEFINITION

PATH = os.path.join(garnett.__path__[0], '..')
IN_PATH = os.path.abspath(PATH) == os.path.abspath(os.getcwd())


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
        reader = garnett.reader.PosFileReader(precision=precision)
        return reader.read(stream)

    def assert_raise_attribute_error(self, frame):
        with self.assertRaises(AttributeError):
            frame.velocity
        with self.assertRaises(AttributeError):
            frame.charge
        with self.assertRaises(AttributeError):
            frame.diameter
        with self.assertRaises(AttributeError):
            frame.moment_inertia
        with self.assertRaises(AttributeError):
            frame.angmom
        with self.assertRaises(AttributeError):
            frame.image


class BasePosFileWriterTest(BasePosFileReaderTest):

    def dump_trajectory(self, trajectory):
        writer = garnett.writer.PosFileWriter()
        return writer.dump(trajectory)

    def write_trajectory(self, trajectory, file, rotate=False):
        writer = garnett.writer.PosFileWriter(rotate=rotate)
        return writer.write(trajectory, file)

    def assert_approximately_equal_frames(self, a, b,
                                          decimals=6, atol=1e-5,
                                          ignore_orientation=False):
        self.assertEqual(a.box.round(decimals), b.box.round(decimals))
        self.assertEqual(a.types, b.types)
        print(a.position, b.position)
        self.assertTrue(np.allclose(a.position, b.position, atol=atol))
        try:
            self.assertTrue(np.allclose(a.velocity, b.velocity, atol=atol))
        except AttributeError:
            pass
        if not ignore_orientation:
            try:
                self.assertTrue(np.allclose(a.orientation, b.orientation, atol=atol))
            except AttributeError:
                pass
        self.assertEqual(a.data, b.data)
        for key in chain(a.shapedef, b.shapedef):
            self.assertEqual(a.shapedef[key], b.shapedef[key])


class PosFileReaderTest(BasePosFileReaderTest):

    def test_read_empty(self):
        empty_sample = io.StringIO("")
        with self.assertRaises(garnett.errors.ParserError):
            self.read_trajectory(empty_sample)

    def test_read_garbage(self):
        garbage_sample = io.StringIO(str(os.urandom(1024 * 100)))
        with self.assertRaises(garnett.errors.ParserError):
            self.read_trajectory(garbage_sample)

    def test_hpmc_dialect(self):
        sample = io.StringIO(garnett.samples.POS_HPMC)
        traj = self.read_trajectory(sample)
        box_expected = garnett.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'])
            self.assertTrue(all(frame.typeid == [0] * N))
            self.assertEqual(frame.box, box_expected)
            self.assert_raise_attribute_error(frame)

        traj.load_arrays()
        self.assert_raise_attribute_error(traj)

    def test_incsim_dialect(self):
        sample = io.StringIO(garnett.samples.POS_INCSIM)
        traj = self.read_trajectory(sample)
        box_expected = garnett.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'])
            self.assertTrue(all(frame.typeid == [0] * N))
            self.assertEqual(frame.box, box_expected)
            self.assert_raise_attribute_error(frame)

        traj.load_arrays()
        self.assert_raise_attribute_error(traj)

    def test_monotype_dialect(self):
        sample = io.StringIO(garnett.samples.POS_MONOTYPE)
        traj = self.read_trajectory(sample)
        box_expected = garnett.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'])
            self.assertTrue(all(frame.typeid == [0] * N))
            self.assertEqual(frame.box, box_expected)
            self.assert_raise_attribute_error(frame)

        traj.load_arrays()
        self.assert_raise_attribute_error(traj)

    def test_injavis_dialect(self):
        sample = io.StringIO(garnett.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        box_expected = garnett.trajectory.Box(Lx=10, Ly=10, Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'])
            self.assertTrue(all(frame.typeid == [0] * N))
            self.assertEqual(frame.box, box_expected)
            self.assert_raise_attribute_error(frame)

        traj.load_arrays()
        self.assert_raise_attribute_error(traj)

    def test_default(self):
        with TemporaryDirectory() as tmp_dir:
            gsdfile = os.path.join(tmp_dir, 'testfile.gsd')
            posfile = os.path.join(tmp_dir, 'testfile.pos')
            with open(gsdfile, "wb") as f:
                f.write(base64.b64decode(garnett.samples.GSD_BASE64))
            with garnett.read(gsdfile) as traj:
                with self.assertRaises(AttributeError):
                    traj[-1].shapedef
                garnett.write(traj, posfile)
            with garnett.read(posfile) as traj:
                for frame in traj:
                    for name in frame.shapedef.keys():
                        self.assertEqual(frame.shapedef[name],
                                         DEFAULT_SHAPE_DEFINITION)


@unittest.skipIf(not HPMC, 'requires HPMC')
class HPMCPosFileReaderTest(BasePosFileReaderTest):

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
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
            hoomd.option.set_notice_level(0)
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
        with io.open(self.fn_pos, 'r', encoding='utf-8') as posfile:
            traj = self.read_trajectory(posfile)
            shape = traj[0].shapedef['A']
            assert shape.shape_class == 'sphere'
            assert np.isclose(shape.diameter, float(1.0))

    def test_ellipsoid(self):
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
            hoomd.option.set_notice_level(0)
        self.addCleanup(self.del_system)
        self.mc = hpmc.integrate.ellipsoid(seed=10)
        a = 0.5
        b = 0.25
        c = 0.125
        self.mc.shape_param.set("A", a=a, b=b, c=c)
        self.addCleanup(self.del_mc)
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
        with io.open(self.fn_pos, 'r', encoding='utf-8') as posfile:
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
            hoomd.option.set_notice_level(0)
        self.addCleanup(self.del_system)
        self.mc = hpmc.integrate.convex_polyhedron(seed=10)
        self.addCleanup(self.del_mc)
        shape_vertices = np.array([[-2, -1, -1], [-2, 1, -1], [-2, -1, 1],
                                   [-2, 1, 1], [2, -1, -1], [2, 1, -1],
                                   [2, -1, 1], [2, 1, 1]])
        self.mc.shape_param.set("A", vertices=shape_vertices)
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
        with io.open(self.fn_pos, 'r', encoding='utf-8') as posfile:
            traj = self.read_trajectory(posfile)
            shape = traj[0].shapedef['A']
            assert shape.shape_class == 'poly3d'
            assert np.array_equal(shape.vertices, shape_vertices)


@ddt
class PosFileWriterTest(BasePosFileWriterTest):

    def test_hpmc_dialect(self):
        sample = io.StringIO(garnett.samples.POS_HPMC)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_incsim_dialect(self):
        sample = io.StringIO(garnett.samples.POS_INCSIM)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_monotype_dialect(self):
        sample = io.StringIO(garnett.samples.POS_MONOTYPE)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_injavis_dialect(self):
        sample = io.StringIO(garnett.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

    def test_arrows(self):
        from garnett.shapes import ArrowShape
        sample = io.StringIO(garnett.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        traj.load_arrays()
        for frame in traj:
            frame.shapedef = {'A': ArrowShape()}
            frame.orientation.T[3] = 0
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)
        for frame in traj_cmp:
            self.assertTrue(isinstance(
                frame.shapedef['A'], ArrowShape))

    def test_ellipsoid(self):
        from garnett.shapes import EllipsoidShape
        sample = io.StringIO(garnett.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        traj.load_arrays()
        a = 0.5
        b = 0.25
        c = 0.125
        for frame in traj:
            frame.shapedef = {'A': EllipsoidShape(a=a, b=b, c=c)}
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)
        for frame in traj_cmp:
            self.assertTrue(isinstance(
                frame.shapedef['A'], EllipsoidShape))

    @unittest.skipIf(not IN_PATH, 'tests not executed from repository root')
    @data(
        'hpmc_sphere',
        'hpmc_sphere_rotated',
        'FeSiUC',
        'Henzie_lithium_cubic_uc',
        'Henzie_lithium_triclinic',
        'cubic_onep',
        'cubic_twop',
        # 'hex_onep',    # These tests are deactivated, because we currently
        # 'hex_twop',    # do not have a solution to keep the reference orientation
        # 'rand_test',   # the same. The systems are otherwise identical.
        'scc',
        'switch_FeSiUC',
        'switch_scc',
        'pos_2d')
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
        # 'xtalslice3_small_rotated',
        # 'switch_FeSiUC',
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
                            ignore_orientation=True  # The shapes themselves are differently oriented
                            )


@unittest.skip("injavis is currently not starting correctly.")
class InjavisReadWriteTest(BasePosFileWriterTest):

    def read_write_injavis(self, sample_file):
        sample_file = io.StringIO(sample_file)
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
        self.read_write_injavis(garnett.samples.POS_HPMC)

    def test_incsim_dialect(self):
        self.read_write_injavis(garnett.samples.POS_INCSIM)

    def test_monotype_dialect(self):
        self.read_write_injavis(garnett.samples.POS_MONOTYPE)

    def test_injavis_dialect(self):
        self.read_write_injavis(garnett.samples.POS_INJAVIS)

    def test_hpmc_dialect_2d(self):
        self.read_write_injavis(garnett.samples.POS_HPMC_2D)

    def test_incsim_dialect_2d(self):
        self.read_write_injavis(garnett.samples.POS_INCSIM_2D)

    def test_monotype_dialect_2d(self):
        self.read_write_injavis(garnett.samples.POS_MONOTYPE_2D)


if __name__ == '__main__':
    context.initialize("--mode=cpu")
    hoomd.option.set_notice_level(0)
    unittest.main()
