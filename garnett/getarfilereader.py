# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""getar-file reader for the Glotzer Group, University of Michigan.

Authors: Matthew Spellings, Carl Simon Adorf

.. code::

    reader = GetarFileReader()
    traj = reader.read(open('trajectory.tar', 'rb'))
"""

import bisect
import functools
import gtar
import json
import logging
import numpy as np

from .trajectory import _RawFrameData, Box, Frame, Trajectory
from .shapes import _parse_type_shape

logger = logging.getLogger(__name__)


def _find_le(a, x):
    """Find rightmost value less than or equal to x"""
    i = bisect.bisect_right(a, x)
    if i:
        return a[i-1]
    raise ValueError


@functools.lru_cache(maxsize=64)
def _get_record_frames(trajectory, record):
    return trajectory.queryFrames(record)


class GetarFrame(Frame):
    """Interface to grab getar frame data.

    :param trajectory: gtar.GTAR trajectory object to read from
    :param records: Dictionary of gtar.Record objects
    :param frame: Frame name inside the trajectory
    :param default_type: The default particle type
    :type default_type: str
    """

    def __init__(self, trajectory, records, frame, default_type, default_box):
        super(GetarFrame, self).__init__()
        self._trajectory = trajectory
        self._records = records
        self._frame = frame
        self._default_type = default_type
        self._default_box = default_box

    def __str__(self):
        return "GetarFrame({})".format(self._records)

    def _get_record_frame(self, name):
        record = self._records[name]
        frames = _get_record_frames(self._trajectory, record)
        return _find_le(frames, self._frame)

    def _get_record_value(self, name):
        record = self._records[name]
        frame = self._get_record_frame(name)
        return self._trajectory.getRecord(record, frame)

    def read(self):
        raw_frame = _RawFrameData()
        raw_frame.type_shapes = []

        # Map getar field names onto HOOMD convention's names
        prop_map = {
            'angular_momentum_quat': 'angmom',
            'type': 'typeid',
        }

        supported_records = [
            'type', 'position', 'orientation', 'velocity',
            'mass', 'charge', 'diameter',
            'moment_inertia', 'angular_momentum_quat',
            'image'
        ]
        for name in supported_records:
            try:
                values = self._get_record_value(name)
                frame_prop = prop_map.get(name, name)
                setattr(raw_frame, frame_prop, values)
            except (KeyError, ValueError):
                # either the record wasn't present (KeyError) or the
                # quantity was not yet provided in index-order
                # (ValueError)
                pass

        try:
            raw_frame.types = json.loads(self._get_record_value('type_names.json'))
        except (KeyError, ValueError):
            raw_frame.types = [self._default_type]
        # if raw_frame.typeid is not set, np.max() here returns a
        # float, so pass through int()
        num_types_to_add = (int(np.max(raw_frame.typeid, initial=0)) +
                            1 - len(raw_frame.types))
        last_type_name = raw_frame.types[-1]
        for t in range(1, num_types_to_add + 1):
            type_name = (last_type_name[:-1] + chr(ord(last_type_name[-1]) + t))
            raw_frame.types.append(type_name)

        try:
            # Read dimension if stored
            if 'dimensions' in self._records:
                dimensions = self._get_record_value('dimensions')[0]
            # Fallback to detection based on z coordinates
            else:
                zs = raw_frame.position[:, 2]
                dimensions = 2 if np.allclose(zs, 0.0, atol=1e-7) else 3

            box = self._get_record_value('box')
            gbox = Box(
                **dict(
                    zip(['Lx', 'Ly', 'Lz', 'xy', 'xz', 'yz'], box),
                    dimensions=dimensions)
            )
            raw_frame.box = np.array(gbox.get_box_matrix())
            raw_frame.box_dimensions = int(dimensions)
        except (KeyError, ValueError):
            raw_frame.box = self._default_box

        try:
            type_shapes = json.loads(self._get_record_value('type_shapes.json'))
            raw_frame.type_shapes = [_parse_type_shape(t) for t in type_shapes]
        except (KeyError, ValueError):
            pass

        return raw_frame


class GetarFileReader(object):
    """getar-file reader for the Glotzer Group, University of Michigan.

    Authors: Matthew Spellings, Carl Simon Adorf

    Read GEneric Trajectory ARchive files, a binary format designed
    for efficient, extensible storage of trajectory data.

    This class provides a wrapper for the gtar library.

    .. code::

        reader = GetarFileReader()
        with open('trajectory.tar', 'rb') as file:
            traj = reader.read(file)
    """

    def read(self, stream, default_type='A', default_box=None):
        """Read binary stream and return a trajectory instance.

        :param stream: The stream, which contains the GeTarFile.
        :type stream: A file-like binary stream.
        :param default_type: The default particle type for
                             posfile dialects without type definition.
        :type default_type: str
        :param default_box: The default_box value is used if no
                            box is specified in the libgetar file.
                            Defaults to [Lx=Ly=Lz=1.0].
        :type default_box: :class:`numpy.ndarray`
        """
        if default_box is None:
            default_box = np.diag([1.0] * 3)
        try:
            filename = stream.name
        except AttributeError:
            raise NotImplementedError(
                "The current implementation of the GeTarFileReader requires "
                "file objects with name attribute, such as NamedTemporaryFile "
                "as the underlying library is reading the file by filename "
                "and not directly from the stream.")
        _trajectory = gtar.GTAR(filename, 'r')
        _records = {rec.getName(): rec for rec in _trajectory.getRecordTypes() if not rec.getGroup()}
        # assume that we care primarily about positions
        try:
            self._frames = _trajectory.queryFrames(_records['position'])
        except KeyError:
            raise RuntimeError("Given trajectory '{}' contained no "
                               "positions.".format(stream))
        frames = [GetarFrame(_trajectory, _records, idx, default_type, default_box)
                  for idx in self._frames]
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
