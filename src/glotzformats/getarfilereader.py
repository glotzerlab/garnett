"""getar-file reader for the Glotzer Group, University of Michigan.

Authors: Matthew Spellings, Carl Simon Adorf

.. code::

    reader = GetarFileReader()
    traj = reader.read(open('trajectory.tar', 'rb'))

.. note::

    The current implementation of the reader's read() method
    requres a file-like object as argument, however the file-like
    object needs to have a 'name' attribute, as the underlying
    library is reading the file directly from disc.
    The file object syntax is used for future compatibility.
"""

import json
import logging

import numpy as np
import gtar

from .trajectory import _RawFrameData, Box, Frame, Trajectory

logger = logging.getLogger(__name__)


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

    def read(self):
        raw_frame = _RawFrameData()
        for name in ['position', 'orientation']:
            try:
                values = self._trajectory.getRecord(
                    self._records[name], self._frame)
            except KeyError:
                values = None

            if values is not None:
                setattr(raw_frame, '{}s'.format(name), values)

        if 'type' in self._records and 'type_names.json' in self._records:
            names = json.loads(self._trajectory.getRecord(
                self._records['type_names.json'], self._frame))
            types = self._trajectory.getRecord(
                self._records['type'], self._frame)
            raw_frame.types = [names[t] for t in types]
        else:
            raw_frame.types = len(raw_frame.positions) * [self._default_type]

        if 'box' in self._records:
            dimensions = (
                self._trajectory.getRecord(self._records['dimension'], self._frame)
                    if 'dimension' in self._records else 3)
            box = self._trajectory.getRecord(self._records['box'], self._frame)
            gbox = Box(
                    **dict(
                        zip(['Lx', 'Ly', 'Lz', 'xy', 'xz', 'yz'], box),
                        dimensions=dimensions)
                    )
            raw_frame.box = np.array(gbox.get_box_matrix())
        else:
            raw_frame.box = self._default_box

        return raw_frame


class GetarFileReader(object):
    """Read GEneric Trajectory ARchive files, a binary format designed
    for efficient, extensible storage of trajectory data."""

    def read(self, stream, default_type='A', default_box=np.diag([1.0] * 3)):
        """Read binary stream and return a trajectory instance.

        .. note::

            The current implementation of the reader's read() method
            requres a file-like object as argument, however the file-like
            object needs to have a 'name' attribute, as the underlying
            library is reading the file directly from disc.
            The file object syntax is used for future compatibility.

        :param stream: The stream, which contains the GeTarFile.
        :type stream: A file-like binary stream.
        :param default_type: The default particle type for
                             posfile dialects without type definition.
        :type default_type: str
        """
        try:
            filename = stream.name
        except AttributeError:
            raise NotImplementedError(
                "The current implementation of the GeTarFileReader requires "
                "file objects with name attribute, such as NamedTemporaryFile "
                "as the underlying library is reading the file by filename "
                "and not directly from the stream.")
        _trajectory = gtar.GTAR(filename, 'r')
        _records = {rec.getName(): rec for rec in _trajectory.getRecordTypes()}
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
