"""getar-file reader for the Glotzer Group, University of Michigan.

Authors: Matthew Spellings

.. code::

    reader = GetarFileReader('trajectory.tar')
    return reader.read()
"""

import collections
import json
import logging
import warnings

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

    def __init__(self, trajectory, records, frame, default_type):
        super(GetarFrame, self).__init__()
        self._trajectory = trajectory
        self._records = records
        self._frame = frame
        self._default_type = default_type

    def read(self):
        raw_frame = _RawFrameData()
        for name in ['position', 'orientation']:
            try:
                values = self._trajectory.getRecord(self._records[name], self._frame)
            except KeyError:
                values = None

            if values is not None:
                setattr(raw_frame, '{}s'.format(name), values)

        if 'type' in self._records and 'type_names.json' in self._records:
            names = json.loads(self._trajectory.getRecord(self._records['type_names.json'], self._frame))
            types = self._trajectory.getRecord(self._records['type'], self._frame)

            raw_frame.types = [names[t] for t in types]
        else:
            raw_frame.types = len(raw_frame.positions)*[self._default_type]

        if 'box' in self._records:
            dimensions = (self._trajectory.getRecord(self._records['dimension'], self._frame)
                          if 'dimension' in self._records else 3)
            box = self._trajectory.getRecord(self._records['box'], self._frame)
            gbox = Box(**dict(zip(['Lx', 'Ly', 'Lz', 'xy', 'xz', 'yz'], box), dimensions=dimensions))
            raw_frame.box = np.array(gbox.get_box_matrix())

        return raw_frame


class GetarFileReader(object):
    """Read getar-format files.

        :param path: The path to the archive to open
    """

    def __init__(self, path):
        """Initialize a getar-format file reader.

        :param path: The path to the archive to open
        """
        self._trajectory = gtar.GTAR(path, 'r')
        self._records = {rec.getName(): rec for rec in self._trajectory.getRecordTypes()}
        # assume that we care primarily about positions
        try:
            self._frames = self._trajectory.queryFrames(self._records['position'])
        except KeyError:
            raise RuntimeError('Given trajectory {} contained no '
                               'positions'.format(path))

    def read(self, default_type='A'):
        """Read text stream and return a trajectory instance.

        :param default_type: The default particle type for
                             posfile dialects without type definition.
        :type default_type: str
        """
        frames = [GetarFrame(self._trajectory, self._records, idx, default_type) for idx in self._frames]
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
