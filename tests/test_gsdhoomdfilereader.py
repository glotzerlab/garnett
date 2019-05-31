import os
import sys
import io
import unittest
import base64
import numpy as np
import collections

import glotzformats
from test_trajectory import TrajectoryTest

PYTHON_2 = sys.version_info[0] == 2
if PYTHON_2:
    from tempdir import TemporaryDirectory
else:
    from tempfile import TemporaryDirectory

try:
    import hoomd
except ImportError:
    HOOMD = False
else:
    HOOMD = True
    hoomd.util.quiet_status()

try:
    import hoomd.hpmc
except ImportError:
    HPMC = False
else:
    HPMC = True


class BaseGSDHOOMDFileReaderTest(TrajectoryTest):
    reader = glotzformats.reader.GSDHOOMDFileReader

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.fn_gsd = os.path.join(self.tmp_dir.name, 'test.gsd')

    def get_sample_file(self):
        return io.BytesIO(base64.b64decode(glotzformats.samples.GSD_BASE64))

    def read_top_trajectory(self):
        top_reader = glotzformats.reader.HOOMDXMLFileReader()
        if PYTHON_2:
            return top_reader.read(io.StringIO(
                unicode(glotzformats.samples.HOOMD_BLUE_XML)))  # noqa
        else:
            return top_reader.read(
                io.StringIO(glotzformats.samples.HOOMD_BLUE_XML))

    def get_traj(self):
        top_traj = self.read_top_trajectory()
        gsd_reader = self.reader()
        gsdfile = io.BytesIO(base64.b64decode(glotzformats.samples.GSD_BASE64))
        return gsd_reader.read(gsdfile, top_traj[0])

    def get_gsd_traj_with_pos_frame(self, read_pos):
        if read_pos:
            pos_reader = glotzformats.reader.PosFileReader()
            if PYTHON_2:
                frame = pos_reader.read(io.StringIO(
                        unicode(glotzformats.samples.POS_HPMC)))[0]  # noqa
            else:
                frame = pos_reader.read(
                        io.StringIO(glotzformats.samples.POS_HPMC))[0]
        else:
            frame = None
        gsd_reader = self.reader()
        gsdfile = io.BytesIO(base64.b64decode(glotzformats.samples.GSD_BASE64))
        return frame, gsd_reader.read(gsdfile, frame)

    def del_system(self):
        del self.system

    def del_mc(self):
        del self.mc

    def test_gsd_with_pos_frame(self):
        frame, traj = self.get_gsd_traj_with_pos_frame(read_pos=True)
        assert frame is not None
        self.assertEqual(traj[0].shapedef, frame.shapedef)

    def test_gsd_without_pos_frame(self):
        frame, traj = self.get_gsd_traj_with_pos_frame(read_pos=False)
        assert frame is None
        self.assertEqual(traj[0].shapedef, collections.OrderedDict())

    def test_read(self):
        traj = self.get_traj()
        self.assertEqual(len(traj), 10)
        self.assertEqual(len(traj[0]), 100)
        self.assertTrue(np.allclose(
            np.asarray(traj[0].box.get_box_matrix()),
            np.array([[8.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]])))
        self.assertTrue(np.allclose(traj[0].positions, np.array([
         [-3., -4., -4.],
         [-3., -4., -2.],
         [-3., -4.,  0.],
         [-3., -4.,  2.],
         [-3., -4.,  4.],
         [-3., -2., -4.],
         [-3., -2., -2.],
         [-3., -2.,  0.],
         [-3., -2.,  2.],
         [-3., -2.,  4.],
         [-3.,  0., -4.],
         [-3.,  0., -2.],
         [-3.,  0.,  0.],
         [-3.,  0.,  2.],
         [-3.,  0.,  4.],
         [-3.,  2., -4.],
         [-3.,  2., -2.],
         [-3.,  2.,  0.],
         [-3.,  2.,  2.],
         [-3.,  2.,  4.],
         [-3.,  4., -4.],
         [-3.,  4., -2.],
         [-3.,  4.,  0.],
         [-3.,  4.,  2.],
         [-3.,  4.,  4.],
         [-1., -4., -4.],
         [-1., -4., -2.],
         [-1., -4.,  0.],
         [-1., -4.,  2.],
         [-1., -4.,  4.],
         [-1., -2., -4.],
         [-1., -2., -2.],
         [-1., -2.,  0.],
         [-1., -2.,  2.],
         [-1., -2.,  4.],
         [-1.,  0., -4.],
         [-1.,  0., -2.],
         [-1.,  0.,  0.],
         [-1.,  0.,  2.],
         [-1.,  0.,  4.],
         [-1.,  2., -4.],
         [-1.,  2., -2.],
         [-1.,  2.,  0.],
         [-1.,  2.,  2.],
         [-1.,  2.,  4.],
         [-1.,  4., -4.],
         [-1.,  4., -2.],
         [-1.,  4.,  0.],
         [-1.,  4.,  2.],
         [-1.,  4.,  4.],
         [1., -4., -4.],
         [1., -4., -2.],
         [1., -4.,  0.],
         [1., -4.,  2.],
         [1., -4.,  4.],
         [1., -2., -4.],
         [1., -2., -2.],
         [1., -2.,  0.],
         [1., -2.,  2.],
         [1., -2.,  4.],
         [1.,  0., -4.],
         [1.,  0., -2.],
         [1.,  0.,  0.],
         [1.,  0.,  2.],
         [1.,  0.,  4.],
         [1.,  2., -4.],
         [1.,  2., -2.],
         [1.,  2.,  0.],
         [1.,  2.,  2.],
         [1.,  2.,  4.],
         [1.,  4., -4.],
         [1.,  4., -2.],
         [1.,  4.,  0.],
         [1.,  4.,  2.],
         [1.,  4.,  4.],
         [3., -4., -4.],
         [3., -4., -2.],
         [3., -4.,  0.],
         [3., -4.,  2.],
         [3., -4.,  4.],
         [3., -2., -4.],
         [3., -2., -2.],
         [3., -2.,  0.],
         [3., -2.,  2.],
         [3., -2.,  4.],
         [3.,  0., -4.],
         [3.,  0., -2.],
         [3.,  0.,  0.],
         [3.,  0.,  2.],
         [3.,  0.,  4.],
         [3.,  2., -4.],
         [3.,  2., -2.],
         [3.,  2.,  0.],
         [3.,  2.,  2.],
         [3.,  2.,  4.],
         [3.,  4., -4.],
         [3.,  4., -2.],
         [3.,  4.,  0.],
         [3.,  4.,  2.],
         [3.,  4.,  4.]])))

    @unittest.skipIf(not HOOMD or not HPMC, 'requires HOOMD and HPMC')
    def test_sphere(self):
        self.system = hoomd.init.create_lattice(
            unitcell=hoomd.lattice.sc(10), n=(2, 1, 1))
        self.addCleanup(hoomd.context.initialize, "--mode=cpu")
        hoomd.option.set_notice_level(0)
        self.addCleanup(self.del_system)
        self.mc = hoomd.hpmc.integrate.sphere(seed=10)
        self.addCleanup(self.del_mc)
        diameter_A = 0.75
        self.mc.shape_param.set("A", diameter=diameter_A, orientable=True)
        self.system.particles[0].position = (0, 0, 0)
        self.system.particles[1].position = (2, 0, 0)
        hoomd.context.current.sorter.set_params(grid=8)
        gsd_writer = hoomd.dump.gsd(filename=self.fn_gsd,
                                    group=hoomd.group.all(),
                                    period=1)
        gsd_writer.dump_state(self.mc)
        hoomd.run(1, quiet=True)
        with open(self.fn_gsd, 'rb') as gsdfile:
            gsd_reader = glotzformats.gsdhoomdfilereader.GSDHOOMDFileReader()
            traj = gsd_reader.read(gsdfile)
            shape = traj[0].shapedef['A']
            assert shape.shape_class == 'sphere'
            assert np.isclose(shape.diameter, diameter_A)
            self.assertEqual(shape.orientable, True)

    @unittest.skipIf(not HOOMD or not HPMC, 'requires HOOMD and HPMC')
    def test_convex_polyhedron(self):
        self.system = hoomd.init.create_lattice(
            unitcell=hoomd.lattice.sc(10), n=(2, 1, 1))
        self.addCleanup(hoomd.context.initialize, "--mode=cpu")
        hoomd.option.set_notice_level(0)
        self.addCleanup(self.del_system)
        self.mc = hoomd.hpmc.integrate.convex_polyhedron(seed=10)
        self.addCleanup(self.del_mc)
        shape_vertices = np.array([[-2, -1, -1],
                                   [-2, -1, 1],
                                   [-2, 1, -1],
                                   [-2, 1, 1],
                                   [2, -1, -1],
                                   [2, -1, 1],
                                   [2, 1, -1],
                                   [2, 1, 1]])
        self.mc.shape_param.set("A", vertices=shape_vertices)
        self.system.particles[0].position = (0, 0, 0)
        self.system.particles[0].orientation = (1, 0, 0, 0)
        self.system.particles[1].position = (2, 0, 0)
        self.system.particles[1].orientation = (1, 0, 0, 0)
        hoomd.context.current.sorter.set_params(grid=8)
        gsd_writer = hoomd.dump.gsd(filename=self.fn_gsd,
                                    group=hoomd.group.all(),
                                    period=1)
        gsd_writer.dump_state(self.mc)
        hoomd.run(1, quiet=True)
        with open(self.fn_gsd, 'rb') as gsdfile:
            gsd_reader = glotzformats.gsdhoomdfilereader.GSDHOOMDFileReader()
            traj = gsd_reader.read(gsdfile)
            shape = traj[0].shapedef['A']
            assert shape.shape_class == 'poly3d'
            assert np.array_equal(shape.vertices, shape_vertices)

    @unittest.skipIf(not HOOMD or not HPMC, 'requires HOOMD and HPMC')
    def test_convex_spheropolyhedron(self):
        self.system = hoomd.init.create_lattice(
            unitcell=hoomd.lattice.sc(10), n=(2, 1, 1))
        self.addCleanup(hoomd.context.initialize, "--mode=cpu")
        hoomd.option.set_notice_level(0)
        self.addCleanup(self.del_system)
        self.mc = hoomd.hpmc.integrate.convex_spheropolyhedron(seed=10)
        self.addCleanup(self.del_mc)
        shape_vertices = np.array([[-2, -1, -1],
                                   [-2, -1, 1],
                                   [-2, 1, -1],
                                   [-2, 1, 1],
                                   [2, -1, -1],
                                   [2, -1, 1],
                                   [2, 1, -1],
                                   [2, 1, 1]])
        shape_sweep_radius = 0.1
        self.mc.shape_param.set("A", vertices=shape_vertices,
                                sweep_radius=shape_sweep_radius)
        self.system.particles[0].position = (0, 0, 0)
        self.system.particles[0].orientation = (1, 0, 0, 0)
        self.system.particles[1].position = (2, 0, 0)
        self.system.particles[1].orientation = (1, 0, 0, 0)
        hoomd.context.current.sorter.set_params(grid=8)
        gsd_writer = hoomd.dump.gsd(filename=self.fn_gsd,
                                    group=hoomd.group.all(),
                                    period=1)
        gsd_writer.dump_state(self.mc)
        hoomd.run(1, quiet=True)
        with open(self.fn_gsd, 'rb') as gsdfile:
            gsd_reader = glotzformats.gsdhoomdfilereader.GSDHOOMDFileReader()
            traj = gsd_reader.read(gsdfile)
            shape = traj[0].shapedef['A']
            assert shape.shape_class == 'spoly3d'
            assert np.array_equal(shape.vertices, shape_vertices)
            assert np.isclose(shape.rounding_radius, shape_sweep_radius)

    @unittest.skipIf(not HOOMD or not HPMC, 'requires HOOMD and HPMC')
    def test_properties(self):
        self.system = hoomd.init.create_lattice(
            unitcell=hoomd.lattice.sc(10), n=(2, 1, 1))
        self.addCleanup(hoomd.context.initialize, "--mode=cpu")
        hoomd.option.set_notice_level(0)
        self.addCleanup(self.del_system)
        self.mc = hoomd.hpmc.integrate.convex_polyhedron(seed=10)
        self.addCleanup(self.del_mc)
        shape_vertices = np.array([[-2, -1, -1],
                                   [-2, -1, 1],
                                   [-2, 1, -1],
                                   [-2, 1, 1],
                                   [2, -1, -1],
                                   [2, -1, 1],
                                   [2, 1, -1],
                                   [2, 1, 1]])
        particle_props = dict(
            position=(1, 1, 1),
            orientation=(0, 1, 0, 0),
            velocity=(1, 2, 3),
            mass=2,
            charge=1,
            diameter=2,
            moment_inertia=(2, 0.5, 1),
            angular_momentum=(1, 2, 3, 4))
        self.mc.shape_param.set("A", vertices=shape_vertices)
        for i in range(len(self.system.particles)):
            for prop in particle_props:
                setattr(self.system.particles[i], prop, particle_props[prop])
        gsd_writer = hoomd.dump.gsd(filename=self.fn_gsd,
                                    group=hoomd.group.all(),
                                    period=None,
                                    dynamic=['attribute', 'property', 'momentum'])
        gsd_writer.dump_state(self.mc)
        gf_prop_map = dict(
            position='positions',
            orientation='orientations',
            velocity='velocities',
            angular_momentum='angmom')
        with open(self.fn_gsd, 'rb') as gsdfile:
            gsd_reader = glotzformats.gsdhoomdfilereader.GSDHOOMDFileReader()
            traj = gsd_reader.read(gsdfile)
            traj.load_arrays()
            for i in range(traj.N[0]):
                for prop in particle_props:
                    gf_prop = gf_prop_map.get(prop, prop)
                    self.assertTrue(
                        (getattr(traj, gf_prop)[0][i] == particle_props[prop]).all())


if __name__ == '__main__':
    unittest.main()
