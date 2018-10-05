import os
import sys
import unittest

import glotzformats

PYTHON_2 = sys.version_info[0] == 2
if PYTHON_2:
    from tempdir import TemporaryDirectory
else:
    from tempfile import TemporaryDirectory

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

    def test_read_io(self):
        with open(get_filename('dump.gsd'), 'rb') as gsdfile:
            with glotzformats.read(gsdfile) as traj:
                self.assertGreater(len(traj), 0)

    def test_read_gsd(self):
        with glotzformats.read(get_filename('dump.gsd')) as traj:
            self.assertGreater(len(traj), 0)

    @unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
    def test_read_gtar(self):
        with glotzformats.read(get_filename('libgetar_sample.tar')) as traj:
            self.assertGreater(len(traj), 0)

    @unittest.skipIf(not PYCIFRW, 'CifFileReader tests require the PyCifRW package.')
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


class UtilWriterTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        with glotzformats.read(get_filename('dump.gsd')) as traj:
            self.trajectory = traj

    def test_write_io(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test_io.gsd')
        with open(tmp_name, 'wb') as gsdfile:
            glotzformats.write(self.trajectory, gsdfile)

        # Read back the file and check if it is the same as the original read
        with glotzformats.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_gsd(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.gsd')
        glotzformats.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with glotzformats.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    @unittest.skipIf(not GTAR, 'GetarFileWriter requires the gtar module.')
    def test_write_gtar(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.zip')
        glotzformats.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with glotzformats.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    @unittest.skipIf(not PYCIFRW, 'CifFileReader tests require the PyCifRW package.')
    def test_write_cif(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.cif')
        glotzformats.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with glotzformats.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_pos(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.pos')
        glotzformats.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with glotzformats.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_format(self):
        # No suffix is given to the temp file, so no format will be detected
        tmp_name = os.path.join(self.tmp_dir.name, 'test')
        glotzformats.write(self.trajectory, tmp_name, fmt='pos')

        # Read back the file and check if it is the same as the original read
        with glotzformats.read(tmp_name, fmt='pos') as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_unsupported(self):
        # No suffix is given to the temp file, so no format will be detected
        tmp_name = os.path.join(self.tmp_dir.name, 'test')
        with self.assertRaises(NotImplementedError):
            glotzformats.write(self.trajectory, tmp_name)

    def test_read_unsupported(self):
        with self.assertRaises(NotImplementedError):
            with glotzformats.read(get_filename('unsupported.ext')):
                pass


if __name__ == '__main__':
    unittest.main()
