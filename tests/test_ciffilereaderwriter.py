# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import io
import logging
import sys
import unittest
import numpy as np
import garnett

try:
    import CifFile  # noqa: F401
except ImportError:
    PYCIFRW = False
else:
    PYCIFRW = True

logger = logging.getLogger(__name__)

PYTHON_2 = sys.version_info[0] == 2


@unittest.skipIf(not PYCIFRW,
                 'CifFileReader tests require the PyCifRW package.')
class BaseCifFileReaderTest(unittest.TestCase):

    def read_pos_trajectory(self, stream, precision=None):
        reader = garnett.reader.PosFileReader(precision=precision)
        return reader.read(stream)

    def read_cif_trajectory(self, stream, precision=None):
        reader = garnett.reader.CifFileReader(precision=precision)
        return reader.read(stream)


class BaseCifFileWriterTest(BaseCifFileReaderTest):

    def dump_trajectory(self, trajectory):
        writer = garnett.writer.CifFileWriter()
        return writer.dump(trajectory)

    def write_trajectory(self, trajectory, file):
        writer = garnett.writer.CifFileWriter()
        return writer.write(trajectory, file)


class CifFileWriterTest(BaseCifFileWriterTest):

    def test_hpmc_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(garnett.samples.POS_HPMC))  # noqa
        else:
            sample = io.StringIO(garnett.samples.POS_HPMC)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].positions, dump)

    def test_incsim_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(garnett.samples.POS_INCSIM))  # noqa
        else:
            sample = io.StringIO(garnett.samples.POS_INCSIM)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].positions, dump)

    def test_monotype_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(garnett.samples.POS_MONOTYPE))  # noqa
        else:
            sample = io.StringIO(garnett.samples.POS_MONOTYPE)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].positions, dump)

    def test_injavis_dialect(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(garnett.samples.POS_INJAVIS))  # noqa
        else:
            sample = io.StringIO(garnett.samples.POS_INJAVIS)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].positions, dump)


class CifFileReaderTest(CifFileWriterTest):
    # note that, in the future, if the cif reader automatically wraps
    # cif files that are written by garnett, these tests will
    # fail because particles in the pos file examples lie outside the box

    def test_hpmc_dialect(self):
        (ref_positions, sample) = super(CifFileReaderTest, self).test_hpmc_dialect()
        if PYTHON_2:
            sample = io.StringIO(unicode(sample.getvalue()))  # noqa
        else:
            sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read positions:')
        logger.debug(traj[-1].positions)
        logger.debug('Pos-read positions:')
        logger.debug(ref_positions)
        self.assertTrue(np.allclose(traj[-1].positions, ref_positions))

    def test_incsim_dialect(self):
        (ref_positions, sample) = super(CifFileReaderTest, self).test_incsim_dialect()
        if PYTHON_2:
            sample = io.StringIO(unicode(sample.getvalue()))  # noqa
        else:
            sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read positions:')
        logger.debug(traj[-1].positions)
        logger.debug('Pos-read positions:')
        logger.debug(ref_positions)
        self.assertTrue(np.allclose(traj[-1].positions, ref_positions))

    def test_monotype_dialect(self):
        (ref_positions, sample) = super(CifFileReaderTest, self).test_monotype_dialect()
        if PYTHON_2:
            sample = io.StringIO(unicode(sample.getvalue()))  # noqa
        else:
            sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read positions:')
        logger.debug(traj[-1].positions)
        logger.debug('Pos-read positions:')
        logger.debug(ref_positions)
        self.assertTrue(np.allclose(traj[-1].positions, ref_positions))

    def test_injavis_dialect(self):
        (ref_positions, sample) = super(CifFileReaderTest, self).test_injavis_dialect()
        if PYTHON_2:
            sample = io.StringIO(unicode(sample.getvalue()))  # noqa
        else:
            sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read positions:')
        logger.debug(traj[-1].positions)
        logger.debug('Pos-read positions:')
        logger.debug(ref_positions)
        self.assertTrue(np.allclose(traj[-1].positions, ref_positions))

    def test_cif_read_write(self):
        if PYTHON_2:
            sample = io.StringIO(unicode(garnett.samples.CIF))  # noqa
        else:
            sample = io.StringIO(garnett.samples.CIF)
        traj = self.read_cif_trajectory(sample)
        ref_positions = traj[-1].positions

        dump = io.StringIO()
        self.write_trajectory(traj, dump)

        if PYTHON_2:
            sample = io.StringIO(unicode(dump.getvalue()))  # noqa
        else:
            sample = io.StringIO(dump.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read positions:')
        logger.debug(traj[-1].positions)
        logger.debug('original positions:')
        logger.debug(ref_positions)
        cif_coordinates = np.array(
                [[0.333333333, 0.6666666667, 0.25],
                 [0.6666666667, 0.333333333, 0.75]])

        self.assertTrue(np.allclose(traj[-1].positions, ref_positions))
        self.assertTrue(np.allclose(traj[-1].cif_coordinates, cif_coordinates))

        with self.assertRaises(ValueError):
            traj[-1].cif_coordinates = 'hello'
        with self.assertRaises(ValueError):
            # This should fail since it's using 2d positions
            traj[-1].cif_coordinates = [[0, 0], [0, 0]]


if __name__ == '__main__':
    unittest.main()
