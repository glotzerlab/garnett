"""DCD-file reader for the Glotzer Group, University of Michigan.

Authors: Carl Simon Adorf

A dcd file conists only of positions.
To provide additional information it is possible
to provide a frame object, whose properties
are copied into each frame of the dcd trajectory.

The example is given for a hoomd-blue xml frame:

.. code::

    xml_reader = HoomdBlueXMLReader()
    dcd_reader = DCDFileReader()

    with open('init.xml') as xmlfile:
        with open('dump.dcd') as dcdfile:
            xml_frame = xml_reader.read(xmlfile)[0]
            traj = reader.read(dcdfile, xml_frame)
"""

import logging
import warnings
import copy

import numpy as np
import mdtraj as md

from .trajectory import _RawFrameData, Frame, Trajectory
from .errors import ParserError


logger = logging.getLogger(__name__)


class DCDFrame(Frame):

    def __init__(self, traj, frame_index, t_frame):
        # This implementation requires a 3rd party reader
        self.traj=traj
        self.frame_index = frame_index
        self.t_frame = t_frame
        super(DCDFrame, self).__init__()

    def read(self):
        "Read the frame data from the stream."
        raw_frame = copy.deepcopy(self.t_frame)
        raw_frame.box = np.asarray(raw_frame.box.get_box_matrix())
        B = raw_frame.box
        p = self.traj.slice(self.frame_index, copy=False).xyz[0]
        raw_frame.positions = [2*np.dot(B, p_.reshape((3,1))) for p_ in p]
        return raw_frame

    def __str__(self):
        return "DCDFrame(# frames={}, topology_frame={})".format(len(self.traj), self.t_frame)


class DCDFileReader(object):
    """Read dcd trajectory files."""

    def read(self, stream, frame):
        """Read binary stream and return a trajectory instance.

        :param stream: The stream, which contains the xmlfile.
        :type stream: A file-like textstream.
        """
        try:
            top = md.Topology()
            [top.add_atom(t, 'X', top.add_residue('x', top.add_chain())) for t in frame.types]
            mdtraj = md.load_dcd(stream.name, top=top)
        except AttributeError:
            raise
        else:
            frames = [DCDFrame(mdtraj, i, frame) for i in range(len(mdtraj))]
            logger.info("Read {} frames.".format(len(frames)))
            return Trajectory(frames)
