# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""DCD-file reader for the Glotzer Group, University of Michigan.

Authors: Carl Simon Adorf

A dcd file consists only of positions.
To provide additional information it is possible
to provide a frame object, whose properties
are copied into each frame of the dcd trajectory.

The example is given for a hoomd-blue xml frame:

.. code::

    xml_reader = HOOMDXMLFileReader()
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

        ort = traj[0].orientation
        alpha = 2 * np.arctan2(ort[:, 3], ort[:, 0])
"""

import logging
import copy
from collections import namedtuple

import numpy as np
from numpy.core import numeric as _nx
from numpy.core.numeric import asanyarray

from .trajectory import Frame, Trajectory, Box
from .trajectory import FRAME_PROPERTIES, TYPE_PROPERTIES, PARTICLE_PROPERTIES
from .trajectory import _RawFrameData
from . import pydcdreader

logger = logging.getLogger(__name__)


def _euler_to_quaternion(alpha, q):
    q.T[0] = np.cos(alpha * 0.5)
    q.T[1] = q.T[2] = 0.0
    q.T[3] = np.sin(alpha * 0.5)


def _box_from_frame_header(frame_header):
    fh = frame_header

    lx = fh.box_a
    xy = fh.box_b * fh.box_gamma
    xz = fh.box_c * fh.box_beta
    ly = np.sqrt(fh.box_b*fh.box_b - xy*xy)
    yz = (fh.box_b*fh.box_c*fh.box_alpha - xy*xz) / lx
    lz = np.sqrt(fh.box_c*fh.box_c - xz*xz - yz*yz)

    xy /= ly
    xz /= lz
    yz /= lz
    return Box(lx, ly, lz, xy=xy, xz=xz, yz=yz, dimensions=3)


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
        self._dcdreader = dcdreader
        self.stream = stream
        self.file_header = _DCDFileHeader(** file_header)
        self.offset = offset
        self.t_frame = t_frame
        self.default_type = default_type
        self._box = None
        self._types = None
        self._typeid = None
        self._position = None
        self._orientation = None
        super(DCDFrame, self).__init__(dtype=dtype)

    def __len__(self):
        return int(self.file_header.n_particles)

    def _read(self, xyz):
        frame_header = _DCDFrameHeader(
            ** self._dcdreader.read_frame(self.stream, xyz, self.offset))
        self._box = _box_from_frame_header(frame_header)
        self._position = xyz.swapaxes(0, 1)

    def _load(self, xyz=None, ort=None):
        N = FRAME_PROPERTIES['N'](self.file_header.n_particles)
        if xyz is None:
            xyz = np.zeros((3, N), dtype=np.float32)
        if ort is None:
            ort = np.zeros((N, 4), dtype=self._dtype)
        self._read(xyz=xyz)
        if self.t_frame is None:
            self._types = np.asarray([self.default_type],
                                     dtype=TYPE_PROPERTIES['types'])
            self._typeid = np.zeros(N, dtype=PARTICLE_PROPERTIES['typeid'])
        else:
            self._types = copy.copy(self.t_frame.types)
            self._typeid = copy.copy(self.t_frame.typeid)
        if self.t_frame is None or self.t_frame.box.dimensions == 3:
            ort.T[0] = 1.0
            ort.T[1:] = 0
        elif self.t_frame.box.dimensions == 2:
            _euler_to_quaternion(
                self._position.T[-1], ort)
            self._position.T[-1] = 0
        else:
            raise ValueError(self.t_frame.box.dimensions)
        self._orientation = ort

    def _loaded(self):
        return not (self._box is None or
                    self._types is None or
                    self._typeid is None or
                    self._position is None or
                    self._orientation is None)

    def read(self):
        raw_frame = _RawFrameData()
        if self.t_frame is not None:
            raw_frame.data = copy.deepcopy(self.t_frame.data)
            raw_frame.data_keys = copy.deepcopy(self.t_frame.data_keys)
            raw_frame.box_dimensions = self.t_frame.box.dimensions
            try:
                raw_frame.type_shapes = copy.deepcopy(self.t_frame.type_shapes)
            except AttributeError:
                pass
        if not self._loaded():
            self._load()
        assert self._loaded()
        raw_frame.box = self._box
        raw_frame.types = self._types
        raw_frame.typeid = self._typeid
        raw_frame.position = self._position
        raw_frame.orientation = self._orientation
        assert len(raw_frame.typeid) == len(self)
        assert len(raw_frame.position) == len(self)
        assert len(raw_frame.orientation) == len(self)
        return raw_frame

    def unload(self):
        self._box = None
        self._types = None
        self._position = None
        self._orientation = None
        super(DCDFrame, self).unload()

    def __str__(self):
        return "DCDFrame(# particles={}, topology_frame={})".format(
            len(self), self.t_frame)


class DCDTrajectory(Trajectory):

    def arrays_loaded(self):
        """Returns true if arrays are loaded into memory.

        See also: :meth:`~.load_arrays`"""
        return not (self._box is None or
                    self._N is None or
                    self._types is None or
                    self._typeid is None or
                    self._position is None or
                    self._orientation is None)

    def load_arrays(self):
        # Determine array shapes
        M = len(self)
        N = len(self.frames[0])
        _N = np.full(M, N, dtype=FRAME_PROPERTIES['N'])

        # Coordinates
        xyz = np.zeros((M, 3, N), dtype=np.float32)
        ort = np.zeros((M, N, 4), dtype=self._dtype)
        for i, frame in enumerate(self.frames):
            if not frame._loaded():
                frame._load(xyz=xyz[i], ort=ort[i])

        # Types can only be handled after frame._load() calls.
        types = np.asarray([f._types for f in self.frames],
                           dtype=TYPE_PROPERTIES['types'])
        typeid = np.asarray([f._typeid for f in self.frames],
                            dtype=PARTICLE_PROPERTIES['typeid'])
        box = np.asarray([f._box for f in self.frames],
                         dtype=FRAME_PROPERTIES['box'])

        try:
            # Perform swap
            self._box = box
            self._N = _N
            self._types = types
            self._typeid = typeid
            self._position = xyz.swapaxes(1, 2)
            self._orientation = ort
        except Exception:
            # Ensure consistent error state
            self._box = self._N = self._type = self._types = \
                self._type_ids = self._position = self._orientation = None
            raise

    def xyz(self, xyz=None):
        """Return the xyz coordinates of the dcd file.

        Use this function to access xyz-coordinates with minimal
        overhead and maximal performance.

        You can provide a reference to an existing numpy.ndarray
        with shape (Mx3xN), where M is the length of the trajectory
        and N is the number of particles.
        Please note that the array needs to be of data type float32
        and in-memory contiguous.

        :param xyz: A numpy array of shape (Mx3xN).
        :type xyz: numpy.ndarray
        :returns: A view or a copy of the xyz-array of shape (MxNx3).
        :rtype: numpy.ndarray
        """
        shape = (len(self), 3, len(self.frames[0]))
        if xyz is None:
            xyz = np.zeros(shape, dtype=np.float32)
        else:
            assert xyz.flags['C_CONTIGUOUS']
            assert xyz.dtype == np.float32
            assert xyz.shape == shape
        for i, frame in enumerate(self.frames):
            frame._read(xyz[i])
        return xyz.swapaxes(1, 2)


class _DCDFileReader(object):
    """DCD-file reader for the Glotzer Group, University of Michigan.

    Author: Carl Simon Adorf

    A dcd file consists only of positions.
    To provide additional information it is possible
    to provide a frame object, whose properties
    are copied into each frame of the dcd trajectory.

    The example is given for a hoomd-blue xml frame:

    .. code::

        xml_reader = HOOMDXMLFileReader()
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

            alpha = 2 * np.arctan2(ort[:, 3], ort[:, 0])
    """
    _dcdreader = pydcdreader

    def _scan(self, stream, t_frame=None, default_type=None):
        file_header, offsets = self._dcdreader.scan(stream)
        for offset in offsets:
            yield DCDFrame(
                dcdreader=self._dcdreader,
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
        :type default_type: str
        :returns: A trajectory instance.
        :rtype: :class:`~.DCDTrajectory`"""
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
