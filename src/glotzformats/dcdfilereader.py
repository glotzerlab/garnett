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
        with open('dump.dcd') as dcdfile:
            xml_frame = xml_reader.read(xmlfile)[0]
            traj = reader.read(dcdfile, xml_frame)
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
    from math import sin, cos, sqrt, pi
    fh = frame_header

    def almost_zero(r):
        return 0.0 if r < tol else r

    alpha = fh.box_alpha or pi / 2
    beta = fh.box_beta or pi / 2
    gamma = fh.box_gamma or pi / 2
    a = [fh.box_a, 0, 0]
    b = [almost_zero(fh.box_b * cos(gamma)), fh.box_b * sin(gamma), 0]
    c1 = fh.box_c * cos(beta)
    c2 = fh.box_c * (cos(alpha) - cos(beta) * cos(gamma)) / sin(gamma)
    c3 = sqrt(fh.box_c**2 - c1**2 - c2**2)
    c = [almost_zero(c1), almost_zero(c2), c3]
    return [a, b, c]


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
        raw_frame = copy.deepcopy(self.t_frame)
        raw_frame.box = np.asarray(
            _box_matrix_from_frame_header(self.frame_header)).T
        self.stream.seek(self.start)
        N = self.file_header.n_particles
        xyz = []
        for i in range(3):
            len_section = _read_int(self.stream)
            xyz.append([_read_float(self.stream) for j in range(N)])
            assert _read_int(self.stream) == len_section
        raw_frame.positions = np.array(xyz).T
        raw_frame.orientations = np.zeros((len(raw_frame.positions), 4))
        raw_frame.types = [self.default_type] * len(raw_frame.positions)
        assert len(raw_frame.positions) == self.file_header.n_particles
        return raw_frame

    def __str__(self):
        return "DCDFrame(# frames={}, topology_frame={})".format(
            len(self.traj), self.t_frame)


class DCDFileReader(object):
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

    def _scan(self, stream, t_frame=None, default_type='A'):
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

    def read(self, stream, frame=None, default_type='A'):
        """Read binary stream and return a trajectory instance.

        :param stream: The stream, which contains the dcd-file.
        :type stream: A file-like binary stream
        :param frame: A frame containing topological information
            that cannot be encoded in the dcd-format.
        :type frame: :class:`trajectory.Frame`
        :param default_type: A type name to be used when no first
            frame is provided.
        :type default_type: str"""
        if frame is None:
            frame = _RawFrameData()
        frames = list(self._scan(stream, t_frame=frame,
                                 default_type=default_type))
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
