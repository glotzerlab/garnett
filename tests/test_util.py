# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import os
import unittest
import garnett
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

TESTDATA_PATH = os.path.join(os.path.dirname(__file__), 'files/')


def get_filename(filename):
    return os.path.join(TESTDATA_PATH, filename)


class UtilReaderTest(unittest.TestCase):

    def test_read_io(self):
        with open(get_filename('dump.gsd'), 'rb') as gsdfile:
            with garnett.read(gsdfile) as traj:
                self.assertGreater(len(traj), 0)

    def test_read_gsd(self):
        with garnett.read(get_filename('dump.gsd')) as traj:
            self.assertGreater(len(traj), 0)

    @unittest.skipIf(not GTAR, 'GetarFileReader requires the gtar module.')
    def test_read_gtar(self):
        with garnett.read(get_filename('libgetar_sample.tar')) as traj:
            self.assertGreater(len(traj), 0)

    @unittest.skipIf(not PYCIFRW, 'CifFileReader tests require the PyCifRW package.')
    def test_read_cif(self):
        with garnett.read(get_filename('cI16.cif')) as traj:
            self.assertGreater(len(traj), 0)

    def test_read_pos(self):
        with garnett.read(get_filename('FeSiUC.pos')) as traj:
            self.assertGreater(len(traj), 0)

    def test_read_xml(self):
        with garnett.read(get_filename('hoomd.xml')) as traj:
            self.assertGreater(len(traj), 0)

    def test_read_gsd_template(self):
        with garnett.read(
                get_filename('template-missing-shape.gsd'),
                template=get_filename('template-missing-shape.pos')) as traj:
            self.assertGreater(len(traj), 0)

            # Make sure a shape definition was parsed from the POS file
            self.assertGreater(len(traj[0].shapedef), 0)

    def test_read_unsupported_template(self):
        with self.assertRaises(ValueError):
            with garnett.read(
                    get_filename('FeSiUC.pos'),
                    template=get_filename('template-missing-shape.pos')):
                pass

    def test_read_nonexistent(self):
        with self.assertRaises(FileNotFoundError):
            with garnett.read(get_filename('does_not_exist.pos')):
                pass

    def test_read_unsupported(self):
        with self.assertRaises(NotImplementedError):
            with garnett.read(get_filename('unsupported.ext')):
                pass


class UtilWriterTest(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        with garnett.read(get_filename('dump.gsd')) as traj:
            self.trajectory = traj

    def test_write_io(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test_io.gsd')
        with open(tmp_name, 'wb') as gsdfile:
            garnett.write(self.trajectory, gsdfile)

        # Read back the file and check if it is the same as the original read
        with garnett.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_gsd(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.gsd')
        garnett.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with garnett.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    @unittest.skipIf(not GTAR, 'GetarFileWriter requires the gtar module.')
    def test_write_gtar(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.zip')
        garnett.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with garnett.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    @unittest.skipIf(not PYCIFRW, 'CifFileReader tests require the PyCifRW package.')
    def test_write_cif(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.cif')
        garnett.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with garnett.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_pos(self):
        tmp_name = os.path.join(self.tmp_dir.name, 'test.pos')
        garnett.write(self.trajectory, tmp_name)

        # Read back the file and check if it is the same as the original read
        with garnett.read(tmp_name) as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_format(self):
        # No suffix is given to the temp file, so no format will be detected
        tmp_name = os.path.join(self.tmp_dir.name, 'test')
        garnett.write(self.trajectory, tmp_name, fmt='pos')

        # Read back the file and check if it is the same as the original read
        with garnett.read(tmp_name, fmt='pos') as traj:
            self.assertEqual(len(traj), len(self.trajectory))

    def test_write_unsupported(self):
        # No suffix is given to the temp file, so no format will be detected
        tmp_name = os.path.join(self.tmp_dir.name, 'test')
        with self.assertRaises(NotImplementedError):
            garnett.write(self.trajectory, tmp_name)

    def test_read_unsupported(self):
        with self.assertRaises(NotImplementedError):
            with garnett.read(get_filename('unsupported.ext')):
                pass


if __name__ == '__main__':
    unittest.main()
