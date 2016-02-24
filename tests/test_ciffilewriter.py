import unittest
import sys
import io

import glotzformats


PYTHON_2 = sys.version_info[0] == 2


class BaseCifFileReaderTest(unittest.TestCase):

    def read_trajectory(self, stream, precision=None):
        reader = glotzformats.reader.PosFileReader(precision=precision)
        return reader.read(stream)


class BaseCifFileWriterTest(BaseCifFileReaderTest):

    def dump_trajectory(self, trajectory):
        writer = glotzformats.writer.CifFileWriter()
        return writer.dump(trajectory)

    def write_trajectory(self, trajectory, file):
        writer = glotzformats.writer.CifFileWriter()
        return writer.write(trajectory, file)


class CifFileWriterTest(BaseCifFileWriterTest):

    def test_hpmc_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_HPMC))
        else:
            sample = io.StringIO(glotzformats.samples.POS_HPMC)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)

    def test_incsim_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INCSIM))
        else:
            sample = io.StringIO(glotzformats.samples.POS_INCSIM)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)

    def test_monotype_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_MONOTYPE))
        else:
            sample = io.StringIO(glotzformats.samples.POS_MONOTYPE)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)

    def test_injavis_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(glotzformats.samples.POS_INJAVIS))
        else:
            sample = io.StringIO(glotzformats.samples.POS_INJAVIS)
        traj = self.read_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)


if __name__ == '__main__':
    unittest.main()
