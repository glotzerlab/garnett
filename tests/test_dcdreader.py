import sys
import io
import unittest
import base64
import tempfile

import numpy as np

import glotzformats


PYTHON_2 = sys.version_info[0] == 2


class BaseHoomdBlueXMLReaderTest(unittest.TestCase):
    
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile()
        self.addCleanup(self.tmpfile.close)

    def read_top_trajectory(self):
        top_reader = glotzformats.reader.HoomdBlueXMLReader()
        if PYTHON_2:
            return top_reader.read(io.StringIO(
                unicode(glotzformats.samples.HOOMD_BLUE_XML)))  # noqa
        else:
            return top_reader.read(
                io.StringIO(glotzformats.samples.HOOMD_BLUE_XML))

    def test_read(self):
        top_traj = self.read_top_trajectory()
        with tempfile.NamedTemporaryFile('wb') as file:
            file.write(base64.b64decode(glotzformats.samples.DCD_BASE64))
            file.flush()
            with open(file.name, 'rb') as dcdfile:
                traj = glotzformats.reader.DCDReader().read(dcdfile, top_traj[0])
                print(traj)
                self.assertEqual(len(traj), 10)
                self.assertEqual(len(traj[0]), 10)
                self.assertTrue(np.allclose(traj[-1].positions, np.array(
                     [[0.10384979,  0.2343477, -0.03911163],
                      [-0.17528328, -0.23562074,  0.20388559],
                      [-0.16650136,  0.23522241, -0.0931704 ],
                      [-0.0487466,  -0.19215092, -0.12439428],
                      [-0.07279485, -0.05283319, -0.14788103],
                      [ 0.20529102,  -0.04865859,  0.08000968],
                      [-0.03808761,  0.1632334,  0.01829624],
                      [ 0.01157076, 0.08730309, -0.0880134 ],
                      [ 0.1782254,  -0.02665343, -0.13930623],
                      [ 0.01622098, -0.22276552, -0.12746359]])))
                self.assertTrue(np.allclose(
                    np.asarray(traj[0].box.get_box_matrix()),
                    np.array([
                        [4.713492870331, 0, 0],
                        [0, 4.713492870331, 0],
                        [0, 0, 4.713492870331]])))


if __name__ == '__main__':
    unittest.main()
