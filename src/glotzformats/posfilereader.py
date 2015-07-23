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
import re

import numpy as np

from .trajectory import RawFrameData, FrameData, Trajectory, raw_frame_to_frame, SphereShapeDefinition, PolyShapeDefinition, FallbackShapeDefinition
from .errors import ParserError, ParserWarning

logger = logging.getLogger(__name__)

POSFILE_FLOAT_DIGITS = 11

def num(x):
    if isinstance(x, int):
        return x
    else:
        return round(float(x), POSFILE_FLOAT_DIGITS)

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
        line = None
        def _assert(assertion):
            if not bool(assertion):
                if line is not None:
                    raise ParserError("Assertion fail for line '{}': {}.".format(line, assertion))
                else:
                    raise ParserError("Assertion fail: {}".format(assertion))
        frames = list()
        raw_frame = RawFrameData()
        logger.debug("Reading frames.")
        for line in stream:
            if line.startswith('#'):
                if line.startswith('#[data]'):
                    _assert(raw_frame.data is None)
                    raw_frame.data = self._read_data_section(line, stream)
                else:
                    raise ParserError(line)
            else:
                tokens = line.rstrip().split()
                if tokens[0] == 'eof':
                    # end of frame, start new frame
                    frames.append(raw_frame_to_frame(raw_frame))
                    raw_frame = RawFrameData()
                    logger.debug("Read frame {}.".format(len(frames)))
                elif tokens[0] == 'def':
                    definition, data, end = line.strip().split('"')
                    _assert(len(end) == 0)
                    name = definition.split()[1]
                    try:
                        raw_frame.shapedef[name] = parse_shape_definition(data)
                    except Exception as error:
                        warnings.warn("Error during parsing of shape definition: {}".format(error))
                        raw_frame.shapedef[name] = FallbackShapeDefinition(data)
                elif tokens[0] == 'boxMatrix':
                    _assert(len(tokens) == 10)
                    #raw_frame.box = np.array((num(v) for v in tokens[1:])).reshape((3,3))
                    raw_frame.box = np.array(tokens[1:]).reshape((3,3))
                else:
                    # assume we are reading positions now
                    name = tokens[0]
                    _assert(name in raw_frame.shapedef)
                    if len(tokens) == 4:
                        xyz = tokens[-3:]
                        quat = (1,0,0,0)
                    elif len(tokens) >= 8:
                        xyz = tokens[-7:-4]
                        quat = tokens[-4:]
                    else:
                        raise ParserError(line)
                    raw_frame.types.append(name)
                    raw_frame.positions.append([num(v) for v in xyz])
                    raw_frame.orientations.append([num(v) for v in quat])
        if len(frames) == 0:
            raise ParserError("Did not read a single complete frame.")
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)

def parse_shape_definition(line):
    tokens = (t for t in line.split())
    shape_class = next(tokens)
    if shape_class.lower() == 'sphere':
        diameter = float(next(tokens))
    else:
        num_vertices = int(next(tokens))
        vertices = []
        for i in range(num_vertices):
            vertices.append(float(next(tokens)))
    try:
        color = next(tokens)
    except StopIteration:
        color = None
    if shape_class.lower() == 'sphere':
        return SphereShapeDefinition(diameter=diameter,color=color)
    else:
        return PolyShapeDefinition(shape_class=shape_class,vertices=vertices,color=color)
