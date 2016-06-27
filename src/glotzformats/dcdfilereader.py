"""DCD-file reader for the Glotzer Group, University of Michigan.

Authors: Carl Simon Adorf

A dcd file conists only of positions.
To provide additional information it is possible
to provide a frame object, whose properties
are copied into each frame of the dcd trajectory.

The example is given for a hoomd-blue xml frame:

.. code::

    xml_reader = HoomdBlueXMLFileReader()
    dcd_reader = DCDFileReader()

    with open('init.xml') as xmlfile:
        with open('dump.dcd', 'rb') as dcdfile:
            xml_frame = xml_reader.read(xmlfile)[0]
            traj = reader.read(dcdfile, xml_frame)
"""

import logging
import copy
from collections import namedtuple

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory
from . import dcdreader
from .pydcdfilereader import _box_matrix_from_frame_header, _euler_to_quaternion


logger = logging.getLogger(__name__)


_DCDFileHeader = namedtuple(
    '_DCDFileHeader',
    ('num_frames', 'm_start_timestep', 'm_period', 'timesteps',
     'timestep', 'include_unitcell', 'charmm_version', 'n_particles'))


_DCDFrameHeader = namedtuple(
    '_DCDFrameHeader',
    ('box_a', 'box_gamma', 'box_b', 'box_beta', 'box_alpha', 'box_c'))


class DCDFrame(Frame):

    def __init__(self, stream, file_header, offset, t_frame, default_type='A'):
        self.stream = stream
        self.file_header = _DCDFileHeader(** file_header)
        self.offset = offset
        self.t_frame = t_frame
        self.default_type = default_type
        super(DCDFrame, self).__init__()

    def read(self):
        raw_frame = _RawFrameData()
        raw_frame.types = copy.deepcopy(self.t_frame.types)
        raw_frame.data = copy.deepcopy(self.t_frame.data)
        raw_frame.data_keys = copy.deepcopy(self.t_frame.data_keys)
        raw_frame.shapedef = copy.deepcopy(self.t_frame.shapedef)
        self.stream.seek(self.offset)
        N = int(self.file_header.n_particles)
        xyz = np.zeros((3, N))
        frame_header = _DCDFrameHeader(
            ** dcdreader.read_frame(self.stream, xyz))
        raw_frame.box = np.asarray(
            _box_matrix_from_frame_header(frame_header)).T
        if self.t_frame.box is None:
            raw_frame.box_dimensions = self.t_frame.box_dimensions
        else:
            raw_frame.box_dimensions = self.t_frame.box.dimensions
        raw_frame.positions = xyz.T
        raw_frame.orientations = np.zeros((len(raw_frame.positions), 4))
        if self.default_type is not None:
            raw_frame.types = [self.default_type] * len(raw_frame.positions)
        assert len(raw_frame.types) == self.file_header.n_particles
        assert len(raw_frame.positions) == self.file_header.n_particles
        if raw_frame.box_dimensions == 2:
            raw_frame.orientations = _euler_to_quaternion(
                raw_frame.positions.T[-1])
            raw_frame.positions.T[-1] = 0
        return raw_frame

    def __str__(self):
        return "DCDFrame(# frames={}, topology_frame={})".format(
            len(self.traj), self.t_frame)


class DCDFileReader(object):
    """Read dcd trajectory files."""

    def _scan(self, stream, t_frame=None, default_type=None):
        file_header, offsets = dcdreader.scan(stream)
        for offset in offsets:
            yield DCDFrame(
                stream=stream, file_header=file_header, offset=offset,
                t_frame=t_frame, default_type=default_type)

    def read(self, stream, frame=None, default_type=None):
        """Read binary stream and return a trajectory instance.

        :param stream: The stream, which contains the dcd-file.
        :type stream: A file-like binary stream
        :param frame: A frame containing topological information
            that cannot be encoded in the dcd-format.
        :type frame: :class:`trajectory.Frame`
        :param default_type: A type name to be used when no first
            frame is provided, defaults to 'A'.
        :type default_type: str"""
        if frame is not None and default_type is not None:
            raise ValueError(
                "You can only provide a frame or a default_type, not both.")
        if frame is None:
            frame = _RawFrameData()
            default_type = 'A'
        elif frame.box.dimensions == 2:
            logger.info(
                "2-dimensional box, interpreting 3rd dimension "
                "as euler orientation angle.")

        frames = list(self._scan(stream, t_frame=frame,
                                 default_type=default_type))
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
