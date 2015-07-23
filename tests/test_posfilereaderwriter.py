import unittest
import os
import sys
import io
import tempfile
import random
import warnings

import glotzformats

PYTHON_3 = sys.version_info[0] == 3

warnings.filterwarnings('error', category=glotzformats.errors.ParserWarning)

try:
    import hoomd_script
except ImportError:
    HOOMD = False
else:
    HOOMD = True

if HOOMD:
    try:
        from hoomd_plugins import hpmc
    except ImportError:
        HPMC = False
    else:
        HPMC = True
else:
    HPMC = False

class BasePosFileReaderTest(unittest.TestCase):

    def read_trajectory(self, stream):
        reader = glotzformats.reader.PosFileReader()
        return reader.read(stream)
        traj = reader.read(io.StringIO(glotzformats.samples.POS_HPMC))

class BasePosFileWriterTest(BasePosFileReaderTest):

    def dump_trajectory(self, trajectory):
        writer = glotzformats.writer.PosFileWriter()
        return writer.dump(trajectory)

    def write_trajectory(self, trajectory, file):
        writer = glotzformats.writer.PosFileWriter()
        return writer.write(trajectory, file)

class PosFileReaderTest(BasePosFileReaderTest):

    def test_read_empty(self):
        empty_sample = io.StringIO("")
        with self.assertRaises(glotzformats.errors.ParserError):
            self.read_trajectory(empty_sample)

    def test_read_garbage(self):
        garbage_sample = io.StringIO(str(os.urandom(1024 * 100)))
        with self.assertRaises(glotzformats.errors.ParserError):
            self.read_trajectory(garbage_sample)

    def test_hpmc_dialect(self):
        if PYTHON_3:
            sample = io.StringIO(glotzformats.samples.POS_HPMC)
        else:
            sample = io.StringIO(unicode(glotzformats.samples.POS_HPMC))
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10,Ly=10,Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'] * N)
            self.assertEqual(frame.box, box_expected)

    def test_incsim_dialect(self):
        if PYTHON_3:
            sample = io.StringIO(glotzformats.samples.POS_INCSIM)
        else:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INCSIM))
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10,Ly=10,Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'] * N)
            self.assertEqual(frame.box, box_expected)

    def test_monotype_dialect(self):
        if PYTHON_3:
            sample = io.StringIO(glotzformats.samples.POS_MONOTYPE)
        else:
            sample = io.StringIO(unicode(glotzformats.samples.POS_MONOTYPE))
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10,Ly=10,Lz=10)
        for frame in traj:
            N = len(frame)
            self.assertEqual(frame.types, ['A'] * N)
            self.assertEqual(frame.box, box_expected)

    def test_injavis_dialect(self):
        if PYTHON_3:
            sample = io.StringIO(glotzformats.samples.POS_INJAVIS)
        else:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INJAVIS))
        traj = self.read_trajectory(sample)
        box_expected = glotzformats.trajectory.Box(Lx=10,Ly=10,Lz=10)
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
        from hoomd_script import init, sorter, data, dump, run
        from hoomd_plugins import hpmc
        self.system = init.create_empty(N=2, box=data.boxdim(L=10, dimensions=2), particle_types=['A'])
        self.addCleanup(init.reset)
        self.addCleanup(self.del_system)
        self.mc = hpmc.integrate.sphere(seed=10);
        self.mc.shape_param.set("A", diameter=1.0)
        self.addCleanup(self.del_mc)
        self.system.particles[0].position = (0,0,0);
        self.system.particles[0].orientation = (1,0,0,0);
        self.system.particles[1].position = (2,0,0);
        self.system.particles[1].orientation = (1,0,0,0);
        sorter.set_params(grid=8)
        dump.pos(filename=self.fn_pos, period = 1)
        run(10, quiet=True)
        with open(self.fn_pos, 'r', encoding='utf-8') as posfile:
            traj = self.read_trajectory(posfile)

    def test_convex_polyhedron(self):
        from hoomd_script import init, sorter, data, dump, run
        from hoomd_plugins import hpmc
        self.system = init.create_empty(N=2, box=data.boxdim(L=10, dimensions=2), particle_types=['A'])
        self.addCleanup(init.reset)
        self.addCleanup(self.del_system)
        self.mc = hpmc.integrate.convex_polygon(seed=10);
        self.addCleanup(self.del_mc)
        self.mc.shape_param.set("A", vertices=[(-2,-1,-1),
                                               (-2,1,-1),
                                               (-2,-1,1),
                                               (-2,1,1),
                                               (2,-1,-1),
                                               (2,1,-1),
                                               (2,-1,1),
                                               (2,1,1)]);
        self.system.particles[0].position = (0,0,0);
        self.system.particles[0].orientation = (1,0,0,0);
        self.system.particles[1].position = (2,0,0);
        self.system.particles[1].orientation = (1,0,0,0);
        sorter.set_params(grid=8)
        pos_writer = dump.pos(filename=self.fn_pos, period = 1)
        self.mc.setup_pos_writer(pos_writer)
        run(10, quiet=True)
        with open(self.fn_pos, 'r', encoding='utf-8') as posfile:
            traj = self.read_trajectory(posfile)

class PosFileWriterTest(BasePosFileWriterTest):

    def test_hpmc_dialect(self):
        if PYTHON_3:
            sample = io.StringIO(glotzformats.samples.POS_HPMC)
        else:
            sample = io.StringIO(unicode(glotzformats.samples.POS_HPMC))
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        dump.seek(0)
        traj_cmp = self.read_trajectory(dump)
        self.assertEqual(traj, traj_cmp)

if __name__ == '__main__':
    unittest.main()
