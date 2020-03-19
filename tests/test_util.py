# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import os
import unittest
import garnett
from tempfile import TemporaryDirectory
from contextlib import contextmanager

try:
    import CifFile  # noqa: F401
except ImportError:
    PYCIFRW = False
else:
    PYCIFRW = True

try:
    import gsd  # noqa: F401
except ImportError:
    GSD = False
else:
    GSD = True


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

    @contextmanager
    def create_tmp_and_traj(self):
        with TemporaryDirectory() as tmp_dir:
            with garnett.read(get_filename('dump.gsd')) as traj:
                yield (tmp_dir, traj)

    @unittest.skipIf(not GSD, 'GSDHOOMDFileWriter requires the gsd module.')
    def test_write_io(self):
        with self.create_tmp_and_traj() as (tmp_dir, traj):
            tmp_name = os.path.join(tmp_dir, 'test_io.gsd')
            with open(tmp_name, 'wb') as gsdfile:
                garnett.write(traj, gsdfile)

            # Read back the file and check if it is the same as the original
            with garnett.read(tmp_name) as traj2:
                self.assertEqual(len(traj), len(traj2))

    @unittest.skipIf(not GSD, 'GSDHOOMDFileWriter requires the gsd module.')
    def test_write_gsd(self):
        with self.create_tmp_and_traj() as (tmp_dir, traj):
            tmp_name = os.path.join(tmp_dir, 'test.gsd')
            garnett.write(traj, tmp_name)

            # Read back the file and check if it is the same as the original
            with garnett.read(tmp_name) as traj2:
                self.assertEqual(len(traj), len(traj2))

    @unittest.skipIf(not GTAR, 'GetarFileWriter requires the gtar module.')
    def test_write_gtar(self):
        with self.create_tmp_and_traj() as (tmp_dir, traj):
            tmp_name = os.path.join(tmp_dir, 'test.zip')
            garnett.write(traj, tmp_name)

            # Read back the file and check if it is the same as the original
            with garnett.read(tmp_name) as traj2:
                self.assertEqual(len(traj), len(traj2))

    @unittest.skipIf(not PYCIFRW, 'CifFileReader tests require the PyCifRW package.')
    def test_write_cif(self):
        with self.create_tmp_and_traj() as (tmp_dir, traj):
            tmp_name = os.path.join(tmp_dir, 'test.cif')
            garnett.write(traj, tmp_name)

            # Read back the file and check if it is the same as the original
            with garnett.read(tmp_name) as traj2:
                self.assertEqual(len(traj), len(traj2))

    def test_write_pos(self):
        with self.create_tmp_and_traj() as (tmp_dir, traj):
            tmp_name = os.path.join(tmp_dir, 'test.pos')
            garnett.write(traj, tmp_name)

            # Read back the file and check if it is the same as the original
            with garnett.read(tmp_name) as traj2:
                self.assertEqual(len(traj), len(traj2))

    def test_write_format(self):
        with self.create_tmp_and_traj() as (tmp_dir, traj):
            # No suffix is given to the temp file, so no format is detected
            tmp_name = os.path.join(tmp_dir, 'test')
            garnett.write(traj, tmp_name, fmt='pos')

            # Read back the file and check if it is the same as the original
            with garnett.read(tmp_name, fmt='pos') as traj2:
                self.assertEqual(len(traj), len(traj2))

    def test_write_unsupported(self):
        with self.create_tmp_and_traj() as (tmp_dir, traj):
            # No suffix is given to the temp file, so no format is detected
            tmp_name = os.path.join(tmp_dir, 'test')
            with self.assertRaises(NotImplementedError):
                garnett.write(traj, tmp_name)


if __name__ == '__main__':
    unittest.main()
