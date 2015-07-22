"""POS-file reader for the Glotzer Group, University of Michigan.

Authors: Richmond Newmann, Carl Simon Adorf

Example:
    reader = PosFileReader()
    with open('a_posfile.pos', 'r', encoding='utf-8') as posfile:
        return reader.read(posfile)
"""

import collections
import logging
import warnings

import numpy as np

from .trajectory import RawFrameData, FrameData, Trajectory, raw_frame_to_frame
from .errors import ParserError, ParserWarning

logger = logging.getLogger(__name__)

class PosFileReader(object):
    """Read pos-files with different dialects."""

    def _read_data_section(self, header, stream):
        """Read data section from stream."""
        data = collections.defaultdict(list)
        keys = header.strip().split()[1:]
        for line in stream:
            if line.startswith('#[done]'):
                return data
            else:
                values = line.split()
                for key, value in zip(keys, values):
                    data[key].append(value)
        else:
            warnings.warn("File ended abruptly.", ParserWarning)
            return data

    def read(self, stream):
        """Read text stream and return a trajectory instance."""
        frames = list()
        raw_frame = RawFrameData()
        logger.debug("Reading frames.")
        for line in stream:
            if line.startswith('#'):
                if line.startswith('#[data]'):
                    assert raw_frame.data is None
                    raw_frame.data = self._read_data_section(line, stream)
                else:
                    raise ParserError(line)
            else:
                tokens = line.rstrip().split(' ')
                if tokens[0] == 'eof':
                    # end of frame, start new frame
                    frames.append(raw_frame_to_frame(raw_frame))
                    raw_frame = RawFrameData()
                    logger.debug("Read frame {}.".format(len(frames)))
                elif tokens[0] == 'def':
                    definition, data, end = line.strip().split('"')
                    assert len(end) == 0
                    name = definition.split(' ')[1]
                    raw_frame.shapedef[name] = data
                elif tokens[0] == 'boxMatrix':
                    assert len(tokens) == 10
                    raw_frame.box = np.array(tokens[1:]).reshape((3,3))
                else:
                    # assume we are reading positions now
                    name = tokens[0]
                    assert name in raw_frame.shapedef
                    if len(tokens) == 4:
                        xyz = tokens[-3:]
                        quat = (1,0,0,0)
                    elif len(tokens) >= 8:
                        xyz = tokens[-7:-4]
                        quat = tokens[-4:]
                    else:
                        raise ParserError(line)
                    raw_frame.types.append(name)
                    raw_frame.positions.append([float(v) for v in xyz])
                    raw_frame.orientations.append([float(v) for v in quat])
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
