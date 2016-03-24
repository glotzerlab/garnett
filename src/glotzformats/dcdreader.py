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
#import mdtraj as md

from .trajectory import _RawFrameData, Frame, Trajectory
from .errors import ParserError


logger = logging.getLogger(__name__)


def read_int(file):
    return struct.unpack('<L', file.read(4))[0]


def read_double(file):
    return struct.unpack('<d', file.read(8))[0]


def read_float(file):
    return struct.unpack('<f', file.read(4))[0]


class _DCDFrameHeader(object):
    pass


class _DCDFileHeader(object):
    pass


def read_frame_header(file):
    frame_header = _DCDFrameHeader()
    frame_header_size = read_int(file)
    frame_header.box_a = read_double(file)
    frame_header.box_gamma = read_double(file)
    frame_header.box_b = read_double(file)
    frame_header.box_beta = read_double(file)
    frame_header.box_alpha = read_double(file)
    frame_header.box_c = read_double(file)
    assert read_int(file) == frame_header_size
    return frame_header


def skip_frame(file):
    for i in range(3):
        len_section = read_int(file)
        file.seek(len_section, 1)
        assert read_int(file) == len_section


def box_matrix_from_frame_header(frame_header, tol=1e-12):
    from math import sin, cos, sqrt, pi
    fh = frame_header
    def almost_zero(r):
        return 0.0 if r < tol else r

    alpha = fh.box_alpha or pi/2
    beta = fh.box_beta or pi/2
    gamma = fh.box_gamma or pi/2
    a = [fh.box_a, 0, 0]
    b = [almost_zero(fh.box_b * cos(gamma)), fh.box_b * sin(gamma), 0]
    c1 = fh.box_c * cos(beta)
    c2 = fh.box_c * (cos(alpha) - cos(beta) * cos(gamma)) / sin(gamma)
    c3 = sqrt(fh.box_c**2 - c1**2 - c2**2)
    c = [almost_zero(c1), almost_zero(c2), c3]
    return [a, b, c]

class DCDFrame(Frame):

    def __init__(self, file, file_header, frame_header, start, t_frame):
        self.file = file
        self.file_header = file_header
        self.frame_header = frame_header
        self.start = start
        self.t_frame = t_frame
        super(DCDFrame, self).__init__()

    def read(self):
        raw_frame = copy.deepcopy(self.t_frame)
        assert len(raw_frame.positions) == self.file_header.n_particles
        raw_frame.box = np.asarray(box_matrix_from_frame_header(self.frame_header)).T
        self.file.seek(self.start)
        N = self.file_header.n_particles
        xyz = []
        for i in range(3):
            len_section = read_int(self.file)
            xyz.append([read_float(self.file) for j in range(N)])
            assert read_int(self.file) == len_section
        print(np.array(xyz).T)
        raw_frame.positions = np.array(xyz).T
        return raw_frame

    def __str__(self):
        return "DCDFrame(# frames={}, topology_frame={})".format(len(self.traj), self.t_frame)


# class DCDFrame(Frame):
#
#     def __init__(self, traj, frame_index, t_frame):
#         # This implementation requires a 3rd party reader
#         self.traj=traj
#         self.frame_index = frame_index
#         self.t_frame = t_frame
#         super(DCDFrame, self).__init__()
#
#     def read(self):
#         "Read the frame data from the file."
#         raw_frame = copy.deepcopy(self.t_frame)
#         raw_frame.box = np.asarray(raw_frame.box.get_box_matrix())
#         B = raw_frame.box
#         p = self.traj.xyz[self.frame_index]
#         raw_frame.positions = [2*np.dot(B, p_) for p_ in p]
#         return raw_frame

class DCDFileReader(object):
    """Read dcd trajectory files."""

    def _read_file_header(self, file):
        file_header = _DCDFileHeader()
        assert read_int(file) == 84
        assert file.read(4) == b'CORD'
        file_header.num_frames = read_int(file)
        file_header.m_start_timestep = read_int(file)
        file_header.m_period = read_int(file)
        file_header.timesteps = read_int(file)
        for i in range(5):
            read_int(file)
        file_header.timestep = read_int(file)
        file_header.include_unitcell = bool(read_int(file))
        for i in range(8):
            assert read_int(file) == 0
        file_header.charmm_version = read_int(file)
        assert read_int(file) == 84
        title_section_size = read_int(file)
        n_titles = read_int(file)
        len_title = int((title_section_size-4) / 2)
        file_header.titles = []
        for i in range(n_titles):
            file_header.titles.append(file.read(len_title).decode('ascii'))
        assert read_int(file) == title_section_size
        assert read_int(file) == 4
        file_header.n_particles = read_int(file)
        assert read_int(file) == 4
        return file_header

    def _scan(self, file, t_frame=None):
        file_header = self._read_file_header(file)
        for i in range(file_header.num_frames):
            frame_header = read_frame_header(file)
            yield DCDFrame(file=file, file_header=file_header, frame_header=frame_header, start=file.tell(), t_frame=t_frame)
            skip_frame(file)


    def read(self, file, frame=None):
        """Read binary file and return a trajectory instance.

        :param file: The file, which contains the xmlfile.
        :type file: A file-like textfile.
        :param frame: A frame containing topological information
            that cannot be encoded in the dcd-format.
        :type frame: :class:`trajectory.Frame`"""
        if frame is None:
            frame = _RawFrameData()
        frames = list(self._scan(file, t_frame=frame))
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
#
#
#        try:
#            top = md.Topology()
#            [top.add_atom(t, 'X', top.add_residue('x', top.add_chain())) for t in frame.types]
#            mdtraj = md.load_dcd(file.name, top=top)
#        except AttributeError:
#            raise
#        else:
#            frames = [DCDFrame(mdtraj, i, frame) for i in range(len(mdtraj))]
#            logger.info("Read {} frames.".format(len(frames)))
#            return Trajectory(frames)
