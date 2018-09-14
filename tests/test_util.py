import os
import sys
import unittest

import glotzformats

try:
    import CifFile  # noqa: F401
except ImportError:
    PYCIFRW = False
else:
    PYCIFRW = True

try:
    import gtar  # noqa: F401
except ImportError:
    GTAR = False
else:
    GTAR = True

PYTHON_2 = sys.version_info[0] == 2
TESTDATA_PATH = os.path.join(os.path.dirname(__file__), 'files/')


def get_filename(filename):
    return os.path.join(TESTDATA_PATH, filename)


class UtilReaderTest(unittest.TestCase):

    def test_read_gsd(self):
        with glotzformats.read(get_filename('dump.gsd')) as traj:
            self.assertGreater(len(traj), 0)

    @unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
    def test_read_gtar(self):
        with glotzformats.read(get_filename('libgetar_sample.tar')) as traj:
            self.assertGreater(len(traj), 0)

    @unittest.skipIf(not PYCIFRW,
                     'CifFileReader tests require the PyCifRW package.')
    def test_read_cif(self):
        with glotzformats.read(get_filename('cI16.cif')) as traj:
            self.assertGreater(len(traj), 0)

    def test_read_pos(self):
        with glotzformats.read(get_filename('FeSiUC.pos')) as traj:
            self.assertGreater(len(traj), 0)

    def test_read_xml(self):
        with glotzformats.read(get_filename('hoomd.xml')) as traj:
            self.assertGreater(len(traj), 0)

    @unittest.skipIf(PYTHON_2, 'requires python 3')
    def test_read_nonexistent(self):
        with self.assertRaises(FileNotFoundError):
            with glotzformats.read(get_filename('does_not_exist.pos')):
                pass

    def test_read_unsupported(self):
        with self.assertRaises(NotImplementedError):
            with glotzformats.read(get_filename('unsupported.ext')):
                pass


if __name__ == '__main__':
    unittest.main()
