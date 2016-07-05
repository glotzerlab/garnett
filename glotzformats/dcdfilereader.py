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
from numpy.core import numeric as _nx
from numpy.core.numeric import asanyarray

from .trajectory import _RawFrameData, Frame, Trajectory
from . import pydcdreader

logger = logging.getLogger(__name__)


def _euler_to_quaternion(alpha):
    q = np.zeros((len(alpha), 4))
    q.T[0] = np.cos(alpha/2)
    q.T[1] = q.T[2] = q.T[3] = np.sin(alpha/2)
    return q


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


def _np_stack(arrays, axis=0):
    """Join a sequence of arrays along a new axis.

    Copyright (c) 2005-2016, NumPy Developers.
    All rights reserved.

    From numpy/core/shape_base.py (requires numpy>=1.10),
    included to avoid numpy dependency >=1.10."""
    arrays = [asanyarray(arr) for arr in arrays]
    if not arrays:
        raise ValueError('need at least one array to stack')

    shapes = set(arr.shape for arr in arrays)
    if len(shapes) != 1:
        raise ValueError('all input arrays must have the same shape')

    result_ndim = arrays[0].ndim + 1
    if not -result_ndim <= axis < result_ndim:
        msg = 'axis {0} out of bounds [-{1}, {1})'.format(axis, result_ndim)
        raise IndexError(msg)
    if axis < 0:
        axis += result_ndim

    sl = (slice(None),) * axis + (_nx.newaxis,)
    expanded_arrays = [arr[sl] for arr in arrays]
    return _nx.concatenate(expanded_arrays, axis=axis)


_DCDFileHeader = namedtuple(
    '_DCDFileHeader',
    ('num_frames', 'm_start_timestep', 'm_period', 'timesteps',
     'timestep', 'include_unitcell', 'charmm_version', 'n_particles'))


_DCDFrameHeader = namedtuple(
    '_DCDFrameHeader',
    ('box_a', 'box_gamma', 'box_b', 'box_beta', 'box_alpha', 'box_c'))


class DCDFrame(Frame):

    def __init__(self, dcdreader, stream, file_header,
                 offset, t_frame, default_type='A',
                 dtype=None):
        self.dcdreader = dcdreader
        self.stream = stream
        self.file_header = _DCDFileHeader(** file_header)
        self.offset = offset
        self.t_frame = t_frame
        self.default_type = default_type
        self._types = None
        self._box = None
        self._positions = None
        self._orientations = None
        super(DCDFrame, self).__init__(dtype=dtype)

    def __len__(self):
        return int(self.file_header.n_particles)

    def _read(self, xyz):
        frame_header = _DCDFrameHeader(
            ** self.dcdreader.read_frame(self.stream, xyz, self.offset))
        self._box = np.asarray(_box_matrix_from_frame_header(frame_header)).T
        self._positions = xyz.swapaxes(0, 1).astype(self._dtype, copy=False)

    def _load(self, xyz=None, ort=None):
        N = int(self.file_header.n_particles)
        if xyz is None:
            xyz = np.zeros((3, N), dtype=np.float32)
        if ort is None:
            ort = np.zeros((N, 4), dtype=self._dtype)
        self._read(xyz=xyz)
        if self.t_frame is None:
            self._types = np.repeat(np.str_(self.default_type), len(self))
        else:
            self._types = np.copy(self.t_frame.types)
        if self.t_frame is None or self.t_frame.box.dimensions == 3:
            ort.T[0] = 1.0
        elif self.t_frame.box.dimensions == 2:
            ort = _euler_to_quaternion(self._positions.T[-1])
            self._positions.T[-1] = 0
        else:
            raise ValueError(self.t_frame.box.dimensions)
        self._orientations = ort

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
        xyz = np.ascontiguousarray(
            np.zeros((len(self), 3, len(self.frames[0]))),
            dtype=np.float32)
        ort = np.zeros(
            (len(self), len(self.frames[0]), 4),
            dtype=self._dtype)
        for i, frame in enumerate(self.frames):
            if not frame._loaded():
                frame._load(xyz=xyz[i], ort=ort[i])
        self._positions = xyz.swapaxes(1, 2).astype(self._dtype, copy=False)
        self._orientations = ort.astype(self._dtype, copy=False)
        self._types = np.vstack((f._types for f in self.frames))

    def xyz(self, xyz=None):
        """Return the xyz coordinates of the dcd file.

        Use this function if you only want to read xyz coordinates
        and nothin else."""
        shape = (len(self), 3, len(self.frames[0]))
        if xyz is None:
            xyz = np.zeros(shape, dtype=np.float32)
        else:
            assert xyz.flags['C_CONTIGUOUS']
            assert xyz.dtype == np.float32
            assert xyz.shape == shape
        for i, frame in enumerate(self.frames):
            frame._read(xyz[i])
        return xyz.swapaxes(1, 2).astype(self._dtype, copy=False)


class _DCDFileReader(object):
    """Read dcd trajectory files."""
    dcdreader = pydcdreader

    def _scan(self, stream, t_frame=None, default_type=None):
        file_header, offsets = self.dcdreader.scan(stream)
        for offset in offsets:
            yield DCDFrame(
                dcdreader=self.dcdreader,
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
