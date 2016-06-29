"""DCD-file reader for the Glotzer Group, University of Michigan.

Authors: Carl Simon Adorf

A dcd file conists only of positions.
To provide additional information it is possible
to provide a frame object, whose properties
are copied into each frame of the dcd trajectory.

The example is given for a hoomd-blue xml frame:

.. code::

    xml_reader = HoomdBlueXMLFileReader()
    dcd_reader = PyDCDFileReader()

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

.. seealso::

    This is the pure-python version of the dcd-reader,
    see :class:`reader.DCDFileReader` for the cythonized (faster)
    version.
"""

import logging
import struct
import copy

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory
from .errors import ParserError


logger = logging.getLogger(__name__)


def _read_int(stream):
    return struct.unpack('<L', stream.read(4))[0]


def _read_double(stream):
    return struct.unpack('<d', stream.read(8))[0]


def _read_float(stream):
    return struct.unpack('<f', stream.read(4))[0]


def _euler_to_quaternion(alpha):
    q = np.zeros((len(alpha), 4))
    q.T[0] = np.cos(alpha/2)
    q.T[1] = q.T[2] = q.T[3] = np.sin(alpha/2)
    return q


class _DCDFrameHeader(object):
    pass


class _DCDFileHeader(object):
    pass


def read_frame_header(stream):
    frame_header = _DCDFrameHeader()
    frame_header_size = _read_int(stream)
    frame_header.box_a = _read_double(stream)
    frame_header.box_gamma = _read_double(stream)
    frame_header.box_b = _read_double(stream)
    frame_header.box_beta = _read_double(stream)
    frame_header.box_alpha = _read_double(stream)
    frame_header.box_c = _read_double(stream)
    assert _read_int(stream) == frame_header_size
    return frame_header


def _skip_frame(stream):
    for i in range(3):
        len_section = _read_int(stream)
        stream.seek(len_section, 1)
        assert _read_int(stream) == len_section


def _box_matrix_from_frame_header(frame_header, tol=1e-12):
    from math import cos, sqrt, pi
    fh = frame_header

    def almost_zero(r):
        return 0.0 if r < tol else r

    alpha = 90 - fh.box_alpha
    beta = 90 - fh.box_beta
    gamma = 90 - fh.box_gamma
    c_alpha = cos(alpha * pi / 180)
    c_beta = cos(beta * pi / 180)
    c_gamma = cos(gamma * pi / 180)

    lx = fh.box_a
    xy = fh.box_b * c_gamma
    xz = fh.box_c * c_beta
    ly = sqrt(fh.box_b*fh.box_b - xy*xy)
    yz = (fh.box_b*fh.box_c*c_alpha - xy*xz) / lx
    lz = sqrt(fh.box_c*fh.box_c - xz*xz - yz*yz)

    xy /= ly
    xz /= lz
    yz /= lz
    return [
        [lx, 0.0, 0.0],
        [almost_zero(xy * ly), ly, 0.0],
        [almost_zero(xz * lz), (yz * lz), lz]]


class DCDFrame(Frame):

    def __init__(self, stream, file_header, frame_header, start,
                 t_frame, default_type='A'):
        self.stream = stream
        self.file_header = file_header
        self.frame_header = frame_header
        self.start = start
        self.t_frame = t_frame
        self.default_type = default_type
        super(DCDFrame, self).__init__()

    def read(self):
        raw_frame = _RawFrameData()
        raw_frame.types = copy.deepcopy(self.t_frame.types)
        raw_frame.data = copy.deepcopy(self.t_frame.data)
        raw_frame.data_keys = copy.deepcopy(self.t_frame.data_keys)
        raw_frame.shapedef = copy.deepcopy(self.t_frame.shapedef)
        raw_frame.box = np.asarray(
            _box_matrix_from_frame_header(self.frame_header)).T
        if self.t_frame.box is None:
            raw_frame.box_dimensions = self.t_frame.box_dimensions
        else:
            raw_frame.box_dimensions = self.t_frame.box.dimensions
        self.stream.seek(self.start)
        N = self.file_header.n_particles
        xyz = []
        for i in range(3):
            len_section = _read_int(self.stream)
            xyz.append([_read_float(self.stream) for j in range(N)])
            assert _read_int(self.stream) == len_section
        raw_frame.positions = np.array(xyz).T
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
        return "DCDFrame(# particles={}, topology_frame={})".format(
            len(self), self.t_frame)


class PyDCDFileReader(object):
    """Read dcd trajectory files."""

    def _read_file_header(self, stream):
        file_header = _DCDFileHeader()
        assert _read_int(stream) == 84
        assert stream.read(4) == b'CORD'
        file_header.num_frames = _read_int(stream)
        file_header.m_start_timestep = _read_int(stream)
        file_header.m_period = _read_int(stream)
        file_header.timesteps = _read_int(stream)
        for i in range(5):
            _read_int(stream)
        file_header.timestep = _read_int(stream)
        file_header.include_unitcell = bool(_read_int(stream))
        for i in range(8):
            assert _read_int(stream) == 0
        file_header.charmm_version = _read_int(stream)
        assert _read_int(stream) == 84
        title_section_size = _read_int(stream)
        n_titles = _read_int(stream)
        len_title = int((title_section_size - 4) / 2)
        file_header.titles = []
        for i in range(n_titles):
            file_header.titles.append(stream.read(len_title).decode('ascii'))
        assert _read_int(stream) == title_section_size
        assert _read_int(stream) == 4
        file_header.n_particles = _read_int(stream)
        assert _read_int(stream) == 4
        return file_header

    def _scan(self, stream, t_frame=None, default_type=None):
        try:
            file_header = self._read_file_header(stream)
        except Exception as error:
            raise ParserError(
                "Failed to read dcd file header: '{}'.".format(error))
        for i in range(file_header.num_frames):
            try:
                frame_header = read_frame_header(stream)
                yield DCDFrame(stream=stream, file_header=file_header,
                               frame_header=frame_header, start=stream.tell(),
                               t_frame=t_frame, default_type=default_type)
                _skip_frame(stream)
            except Exception as error:
                raise ParserError(
                    "Failed to read frame #{}: '{}'.".format(i, error))

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
