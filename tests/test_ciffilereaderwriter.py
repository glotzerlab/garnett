# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import io
import logging
import os
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

HP2_PATH = os.path.join(os.path.dirname(__file__), 'files', 'hP2-Mg.cif')


class CifAtomSiteLabelParserTest(unittest.TestCase):

    def test_parse_labels(self):
        # Test parsing _atom_site_label.
        # These examples are taken from:
        # https://www.iucr.org/__data/iucr/cif/standard/cifstd15.html
        parser = garnett.ciffilereader._parse_atom_site_label_to_type_name
        assert parser('Cu') == 'Cu'
        assert parser('Cu2+') == 'Cu2+'
        assert parser('dummy') == 'dummy'
        assert parser('Fe3+Ni2+') == 'Fe3+Ni2+'
        assert parser('S-') == 'S-'
        assert parser('H+') == 'H+'
        assert parser('H*') == 'H*'
        assert parser('H(SDS)') == 'H(SDS)'
        assert parser('C1') == 'C'
        assert parser('C103g28') == 'C'
        assert parser('Fe3+17b') == 'Fe3+'
        assert parser('H*251') == 'H*'
        assert parser('boron2a') == 'boron'
        assert parser('Ni22+') == 'Ni22+'
        assert parser('Ni2+2') == 'Ni2+'
        assert parser('Fe2+Ni2+2') == 'Fe2+Ni2+'


@unittest.skipIf(not PYCIFRW,
                 'CifFileReader tests require the PyCifRW package.')
class BaseCifFileReaderTest(unittest.TestCase):

    def read_pos_trajectory(self, stream, precision=None):
        reader = garnett.reader.PosFileReader(precision=precision)
        return reader.read(stream)

    def read_cif_trajectory(self, stream, **kwargs):
        reader = garnett.reader.CifFileReader(**kwargs)
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
        sample = io.StringIO(garnett.samples.POS_HPMC)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].position, dump)

    def test_incsim_dialect(self):
        sample = io.StringIO(garnett.samples.POS_INCSIM)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].position, dump)

    def test_monotype_dialect(self):
        sample = io.StringIO(garnett.samples.POS_MONOTYPE)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].position, dump)

    def test_injavis_dialect(self):
        sample = io.StringIO(garnett.samples.POS_INJAVIS)
        traj = self.read_pos_trajectory(sample)
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        return (traj[-1].position, dump)


class CifFileReaderTest(CifFileWriterTest):
    # note that, in the future, if the cif reader automatically wraps
    # cif files that are written by garnett, these tests will
    # fail because particles in the pos file examples lie outside the box

    def test_hpmc_dialect(self):
        (ref_position, sample) = super(CifFileReaderTest, self).test_hpmc_dialect()
        sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read position:')
        logger.debug(traj[-1].position)
        logger.debug('Pos-read position:')
        logger.debug(ref_position)
        self.assertTrue(np.allclose(traj[-1].position, ref_position))

    def test_incsim_dialect(self):
        (ref_position, sample) = super(CifFileReaderTest, self).test_incsim_dialect()
        sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read position:')
        logger.debug(traj[-1].position)
        logger.debug('Pos-read position:')
        logger.debug(ref_position)
        self.assertTrue(np.allclose(traj[-1].position, ref_position))

    def test_monotype_dialect(self):
        (ref_position, sample) = super(CifFileReaderTest, self).test_monotype_dialect()
        sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read position:')
        logger.debug(traj[-1].position)
        logger.debug('Pos-read position:')
        logger.debug(ref_position)
        self.assertTrue(np.allclose(traj[-1].position, ref_position))

    def test_injavis_dialect(self):
        (ref_position, sample) = super(CifFileReaderTest, self).test_injavis_dialect()
        sample = io.StringIO(sample.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read position:')
        logger.debug(traj[-1].position)
        logger.debug('Pos-read position:')
        logger.debug(ref_position)
        self.assertTrue(np.allclose(traj[-1].position, ref_position))

    def test_aflow_dialect(self):
        sample = io.StringIO(garnett.samples.CIF)
        traj = self.read_cif_trajectory(sample)

        aflow_dialect_cif = garnett.samples.CIF.replace(
            '_symmetry_equiv_pos_as_xyz',
            '_space_group_symop_operation_xyz')
        aflow_sample = io.StringIO(aflow_dialect_cif)
        aflow_traj = self.read_cif_trajectory(aflow_sample)

        logger.debug('AFLOW cif-read positions:')
        logger.debug(aflow_traj[-1].position)
        logger.debug('Cif-read positions:')
        logger.debug(traj[-1].position)

        # confirm that the string was modified
        self.assertNotEqual(garnett.samples.CIF, aflow_dialect_cif)
        # confirm that positions are the same
        self.assertTrue(np.allclose(aflow_traj[-1].position, traj[-1].position))

    def test_cif_read_write(self):
        sample = io.StringIO(garnett.samples.CIF)
        traj = self.read_cif_trajectory(sample)
        ref_position = traj[-1].position
        dump = io.StringIO()
        self.write_trajectory(traj, dump)
        sample = io.StringIO(dump.getvalue())
        traj = self.read_cif_trajectory(sample)
        logger.debug('Cif-read position:')
        logger.debug(traj[-1].position)
        logger.debug('original position:')
        logger.debug(ref_position)
        cif_coordinates = np.array(
                [[0.333333333, 0.6666666667, 0.25],
                 [0.6666666667, 0.333333333, 0.75]])

        self.assertTrue(np.allclose(traj[-1].position, ref_position))
        self.assertTrue(np.allclose(traj[-1].cif_coordinates, cif_coordinates))

        with self.assertRaises(ValueError):
            traj[-1].cif_coordinates = 'hello'
        with self.assertRaises(ValueError):
            # This should fail since it's using 2d positions
            traj[-1].cif_coordinates = [[0, 0], [0, 0]]

    def test_hexagonal(self):
        with open(HP2_PATH, 'r') as f:
            default_trajectory = self.read_cif_trajectory(f)

            f.seek(0)
            bad_trajectory = self.read_cif_trajectory(f, tolerance=1e-5)

        self.assertEqual(len(default_trajectory[0].position), 2)
        self.assertGreater(len(bad_trajectory[0].position), 2)


if __name__ == '__main__':
    unittest.main()
