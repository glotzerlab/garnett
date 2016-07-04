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

.. note::

    If the topology frame is 2-dimensional, the dcd
    trajectory positions are interpreted such that
    the first two values contain the xy-coordinates,
    the third value is an euler angle.

    The euler angle is converted to a quaternion and stored
    in the orientation of the frame.

    To retrieve the euler angles, simply convert the quaternion:

    .. code::

        alpha = 2 * np.arccos(traj[0].orientations.T[0])
"""

import logging
import copy
from collections import namedtuple

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory
from .pydcdfilereader import _box_matrix_from_frame_header
from .pydcdfilereader import _euler_to_quaternion
try:
    from . import dcdreader
except ImportError:
    import dcdreader


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
        self._types = None
        self._box = None
        self._positions = None
        self._orientations = None
        super(DCDFrame, self).__init__()

    def __len__(self):
        return int(self.file_header.n_particles)

    def _read(self):
        N = len(self)
        xyz = np.zeros((3, N))
        frame_header = _DCDFrameHeader(
            ** dcdreader.read_frame(self.stream, xyz, self.offset))
        self._box = np.asarray(_box_matrix_from_frame_header(frame_header)).T
        self._positions = xyz.T

    def _load(self):
        N = int(self.file_header.n_particles)
        self._read()
        if self.t_frame is None:
            self._types = np.repeat(np.str_(self.default_type), len(self))
        else:
            self._types = np.copy(self.t_frame.types)
        if self.t_frame is None or self.t_frame.box.dimensions == 3:
            self._orientations = np.zeros((N, 4))
            self._orientations.T[0] = 1.0
        elif self.t_frame.box.dimensions == 2:
            self._orientations = _euler_to_quaternion(
                self._positions.T[-1])
            self._positions.T[-1] = 0
        else:
            raise ValueError(self.t_frame.box.dimensions)

    def _loaded(self):
        return not (self._types is None or
                    self._box is None or
                    self._positions is None or
                    self._orientations is None)

    def read(self):
        raw_frame = _RawFrameData()
        if self.t_frame is not None:
            raw_frame.data = copy.deepcopy(self.t_frame.data)
            raw_frame.data_keys = copy.deepcopy(self.t_frame.data_keys)
            raw_frame.shapedef = copy.deepcopy(self.t_frame.shapedef)
            raw_frame.box_dimensions = self.t_frame.box.dimensions
        if not self._loaded():
            self._load()
        assert self._loaded()
        raw_frame.box = self._box
        raw_frame.types = self._types
        raw_frame.positions = self._positions
        raw_frame.orientations = self._orientations
        assert len(raw_frame.types) == self.file_header.n_particles
        assert len(raw_frame.positions) == self.file_header.n_particles
        return raw_frame

    def unload(self):
        self._types = None
        self._box = None
        self._positions = None
        self._orientations = None
        super(DCDFrame, self).unload()

    def __str__(self):
        return "DCDFrame(# particles={}, topology_frame={})".format(
            len(self), self.t_frame)


class DCDTrajectory(Trajectory):

    def load_arrays(self):
        for frame in self.frames:
            if not frame._loaded():
                frame._load()
        self._positions = np.stack((f._positions for f in self.frames))
        self._orientations = np.stack((f._orientations for f in self.frames))
        self._types = np.vstack((f._types for f in self.frames))

    def xyz(self):
        """Return the xyz coordinates of the dcd file.

        Use this function if you only want to read xyz coordinates
        and nothin else."""
        for frame in self.frames:
            frame._read()
        return np.vstack((f._positions for f in self.frames))


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
        elif frame is None and default_type is None:
            default_type = 'A'
        elif frame is not None and frame.box.dimensions == 2:
            logger.info(
                "2-dimensional box, interpreting 3rd dimension "
                "as euler orientation angle.")

        frames = list(self._scan(stream, t_frame=frame,
                                 default_type=default_type))
        logger.info("Read {} frames.".format(len(frames)))
        return DCDTrajectory(frames)
