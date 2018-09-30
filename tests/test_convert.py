import os
import sys
import unittest
import tempfile
import itertools

import glotzformats

PYTHON_2 = sys.version_info[0] == 2
if PYTHON_2:
    from tempdir import TemporaryDirectory
else:
    from tempfile import TemporaryDirectory

try:
    import CifFile
except ImportError:
    PYCIFRW = False
else:
    PYCIFRW = True

try:
    import gtar
except ImportError:
    GTAR = False
else:
    GTAR = True

PYTHON_2 = sys.version_info[0] == 2
TESTDATA_PATH = os.path.join(os.path.dirname(__file__), 'files/')


def get_filename(filename):
    return os.path.join(TESTDATA_PATH, filename)


class ConvertTest(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.infiles = {}
        self.outfiles = {}
        self.infiles['gsd'] = ['dump.gsd', 'hpmc-spherocubes.gsd']
        self.outfiles['gsd'] = 'test.gsd'
        self.infiles['pos'] = ['FeSiUC.pos']
        self.outfiles['pos'] = 'test.pos'
        self.infiles['xml'] = ['hoomd.xml']
        if PYCIFRW:
            self.infiles['cif'] = ['cI16.cif']
            self.outfiles['cif'] = 'test.cif'
        if GTAR:
            self.infiles['gtar'] = ['libgetar_sample.tar', 'hpmc-cubes.zip']
            self.outfiles['gtar'] = 'test.tar'
        for fmt in self.infiles:
            self.infiles[fmt] = [get_filename(infile) for infile in self.infiles[fmt]]
        for fmt in self.outfiles:
            self.outfiles[fmt] = os.path.join(self.tmp_dir.name, self.outfiles[fmt])

    def test_convert(self):
        for informat in self.infiles:
            for infile, outformat in itertools.product(self.infiles[informat], self.outfiles):
                outfile = self.outfiles[outformat]
                glotzformats.convert(infile, outfile, no_progress=True)

                # Verify that the output frames match the input frames
                with glotzformats.read(infile) as intraj:
                    with glotzformats.read(outfile) as outtraj:
                        for inframe, outframe in zip(intraj, outtraj):
                            self.assertEqual(inframe, outframe)


if __name__ == '__main__':
    unittest.main()
