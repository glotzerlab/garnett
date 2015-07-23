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
COMMENT_CHARACTERS = ['//']
TOKENS_SKIP = ['rotation', 'antiAliasing']

def num(x):
    if isinstance(x, int):
        return x
    else:
        return round(float(x), POSFILE_FLOAT_DIGITS)

def is_comment(line):
    for comment_char in COMMENT_CHARACTERS:
        if line.startswith(comment_char):
            return True
    return False

class PosFileReader(object):
    """Read pos-files with different dialects."""

    def _read_data_section(self, header, stream):
        """Read data section from stream."""
        data = collections.defaultdict(list)
        keys = header.strip().split()[1:]
        for i, line in enumerate(stream):
            if is_comment(line):
                continue
            if line.startswith('#[done]'):
                return data, i
            else:
                values = line.split()
                for key, value in zip(keys, values):
                    data[key].append(value)
        else:
            warnings.warn("File ended abruptly.", ParserWarning)
            return data, i

    def read(self, stream, default_type='A'):
        """Read text stream and return a trajectory instance.

        :param stream: The stream, which contains the posfile.
        :type stream: A file-like textstream.
        :param default_type: The default particle type for posfile dialects without type definition.
        :type default_type: str
        """
        i = line = None
        def _assert(assertion):
            assert i is not None
            assert line is not None
            if not assertion:
                raise ParserError("Failed to read line #{}: {}.".format(i, line))
        monotype = False
        frames = list()
        raw_frame = RawFrameData()
        logger.debug("Reading frames.")
        for i, line in enumerate(stream):
            if is_comment(line):
                continue
            if line.startswith('#'):
                if line.startswith('#[data]'):
                    _assert(raw_frame.data is None)
                    raw_frame.data, j = self._read_data_section(line, stream)
                    i += j
                else:
                    raise ParserError(line)
            else:
                tokens = line.rstrip().split()
                if not tokens:
                    continue # empty line
                elif tokens[0] in TOKENS_SKIP:
                    continue # skip these lines
                if tokens[0] == 'eof':
                    # end of frame, start new frame
                    frames.append(raw_frame_to_frame(raw_frame))
                    raw_frame = RawFrameData()
                    logger.debug("Read frame {}.".format(len(frames)))
                elif tokens[0] == 'def':
                    definition, data, end = line.strip().split('"')
                    _assert(len(end) == 0)
                    name = definition.split()[1]
                    raw_frame.shapedef[name] = parse_shape_definition(data)
                elif tokens[0] == 'shape': # monotype
                    definition = line.strip().split('"')[1]
                    raw_frame.shapedef[default_type] = parse_shape_definition(definition)
                    _assert(len(raw_frame.shapedef) == 1)
                    monotype = True
                elif tokens[0] in ('boxMatrix', 'box'):
                    if len(tokens) == 10:
                    #_assert(len(tokens) == 10)
                    #raw_frame.box = np.array((num(v) for v in tokens[1:])).reshape((3,3))
                        raw_frame.box = np.array([num(v) for v in tokens[1:]]).reshape((3,3))
                    elif len(tokens) == 4:
                    #raw_frame.box = np.array(tokens[1:]).reshape((3,3))
                    #__assert(len(tokens) == 4)
                        raw_frame.box = np.array([[num(tokens[1]),0,0],[0,num(tokens[2]),0],[0,0,num(tokens[3])]]).reshape((3,3))
                else:
                    # assume we are reading positions now
                    if not monotype:
                        name = tokens[0]
                        _assert(name in raw_frame.shapedef)
                    else:
                        name = default_type
                    if len(tokens) >= 7:
                        xyz = tokens[-7:-4]
                        quat = tokens[-4:]
                    elif len(tokens) >= 3:
                        xyz = tokens[-3:]
                        quat = (1,0,0,0)
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
    try:
        tokens = (t for t in line.split())
        shape_class = next(tokens)
        if shape_class.lower() == 'sphere':
            diameter = float(next(tokens))
        else:
            num_vertices = int(next(tokens))
            vertices = []
            for i in range(num_vertices):
                xyz = next(tokens), next(tokens), next(tokens)
                vertices.append([num(v) for v in xyz])
        try:
            color = next(tokens)
        except StopIteration:
            color = None
        if shape_class.lower() == 'sphere':
            return SphereShapeDefinition(diameter=diameter,color=color)
        else:
            return PolyShapeDefinition(shape_class=shape_class,vertices=vertices,color=color)
    except Exception as error:
        warnings.warn("Failed to parse shape definition, using fallback mode. ({})".format(line))
        return FallbackShapeDefinition(line)
