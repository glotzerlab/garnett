import io
import unittest
import base64
import tempfile

import numpy as np

import glotzformats

try:
    import gsd  # noqa: F401
    import gsd.hoomd  # noqa: F401
except ImportError:
    GSD = False
else:
    GSD = True


@unittest.skipIf(not GSD, 'GSDHOOMDFileWriter requires the gsd module.')
class BaseGSDHOOMDFileWriterTest(unittest.TestCase):
    reader_class = glotzformats.reader.GSDHOOMDFileReader
    writer_class = glotzformats.writer.GSDHOOMDFileWriter

    def setUp(self):
        self.reader = type(self).reader_class()
        self.writer = type(self).writer_class()

    def test_write(self):
        # Note that this test assumes that the reader is working, and therefore
        # could fail if the reader is broken even if the writer is fine.
        gsdfile = io.BytesIO(base64.b64decode(glotzformats.samples.GSD_BASE64))

        traj = self.reader.read(gsdfile)
        traj.load_arrays()
        len_orig = len(traj)
        readwrite_props = ['N', 'types', 'type_ids',
                           'positions', 'orientations', 'velocities',
                           'mass', 'charge', 'diameter',
                           'moment_inertia', 'angmom']
        original_data = {}
        for prop in readwrite_props:
            original_data[prop] = getattr(traj, prop)
        box_orig = traj[0].box.get_box_matrix()  # Just checking one frame

        # Write to a temp file
        tmpfile = tempfile.NamedTemporaryFile(mode='wb')
        with tmpfile as f:
            self.writer.write(traj, f)

            # Read back the file and check if it is the same as the original read
            traj = self.reader.read(f)
            traj.load_arrays()
            self.assertEqual(len(traj), len_orig)
            for prop in readwrite_props:
                self.assertTrue(np.array_equal(
                    getattr(traj, prop), original_data[prop]))
            self.assertTrue(np.allclose(traj[0].box.get_box_matrix(), box_orig))


if __name__ == '__main__':
    unittest.main()
