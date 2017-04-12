"""POS-file reader for the Glotzer Group, University of Michigan.

Authors: Carl Simon Adorf, Richmond Newmann

.. code::

    reader = PosFileReader()
    with open('a_posfile.pos', 'r', encoding='utf-8') as posfile:
        return reader.read(posfile)
"""

import collections
import logging
import warnings

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory, \
    SphereShapeDefinition, PolyShapeDefinition,\
    ArrowShapeDefinition, SphereUnionShapeDefinition, \
    PolyUnionShapeDefinition, GeneralPolyShapeDefinition, FallbackShapeDefinition

from .errors import ParserError, ParserWarning

logger = logging.getLogger(__name__)

POSFILE_FLOAT_DIGITS = 11
COMMENT_CHARACTERS = ['//']
TOKENS_SKIP = ['translation', 'rotation', 'antiAliasing', 'zoomFactor', 'connection']


def _is_comment(line):
    for comment_char in COMMENT_CHARACTERS:
        if line.startswith(comment_char):
            return True
    return False


class PosFileFrame(Frame):

    def __init__(self, stream, start, end, precision, default_type):
        self.stream = stream
        self.start = start
        self.end = end
        self.precision = precision
        self.default_type = default_type
        super(PosFileFrame, self).__init__()

    def _num(self, x):
        if isinstance(x, int):
            return x
        else:
            return round(float(x), self.precision)

    def _read_data_section(self, header, stream):
        """Read data section from stream."""
        data = collections.defaultdict(list)
        keys = header.strip().split()[1:]
        for i, line in enumerate(stream):
            if _is_comment(line):
                continue
            if line.startswith('#[done]'):
                return keys, data, i
            else:
                values = line.split()
                for key, value in zip(keys, values):
                    data[key].append(value)
        else:
            warnings.warn("File ended abruptly.", ParserWarning)
            return keys, data, i

    def _parse_shape_definition(self, line):
        try:
            tokens = (t for t in line.split())
            shape_class = next(tokens)
            if shape_class.lower() == 'sphere':
                diameter = float(next(tokens))
            elif shape_class.lower() == 'arrow':
                thickness = float(next(tokens))
            elif shape_class.lower() == 'sphere_union':
                num_centers = int(next(tokens))
                centers = []
                diameters = []
                colors = []
                for i in range(num_centers):
                    diameters.append(float(next(tokens)))
                    xyz = next(tokens), next(tokens), next(tokens)
                    colors.append(next(tokens))
                    centers.append([self._num(v) for v in xyz])
            elif shape_class.lower() == 'poly3d_union':
                num_centers = int(next(tokens))
                vertices = [[] for p in range(num_centers)]
                centers = []
                orientations = []
                colors = []
                for i in range(num_centers):
                    num_vertices = int(next(tokens))
                    for j in range(num_vertices):
                        xyz = next(tokens), next(tokens), next(tokens)
                        vertices[i].append([self._num(v) for v in xyz])
                    xyz = next(tokens), next(tokens), next(tokens)
                    centers.append([self._num(v) for v in xyz])
                    quat = next(tokens), next(tokens), next(tokens), next(tokens)
                    orientations.append([self._num(q) for q in quat])
                    colors.append(next(tokens))
            elif shape_class.lower() == 'polyv':
                num_vertices = int(next(tokens))
                vertices = []
                for i in range(num_vertices):
                    xyz = next(tokens), next(tokens), next(tokens)
                    vertices.append([self._num(v) for v in xyz])
                num_faces = int(next(tokens))
                faces = []
                for i in range(num_faces):
                    fv = []
                    nvert = int(next(tokens))
                    for j in range(nvert):
                        fv.append(int(next(tokens)))
                    faces.append(fv)
            else:
                num_vertices = int(next(tokens))
                vertices = []
                for i in range(num_vertices):
                    xyz = next(tokens), next(tokens), next(tokens)
                    vertices.append([self._num(v) for v in xyz])
            try:
                color = next(tokens)
            except StopIteration:
                color = None
            if shape_class.lower() == 'sphere':
                return SphereShapeDefinition(diameter=diameter, color=color)
            elif shape_class.lower() == 'arrow':
                return ArrowShapeDefinition(thickness=thickness, color=color)
            elif shape_class.lower() == 'sphere_union':
                return SphereUnionShapeDefinition(shape_class=shape_class, diameters=diameters, centers=centers, colors=colors)
            elif shape_class.lower() == 'poly3d_union':
                return PolyUnionShapeDefinition(shape_class=shape_class, vertices=vertices, centers=centers, orientations=orientations, colors=colors)
            elif shape_class.lower() == 'polyv':
                return GeneralPolyShapeDefinition(shape_class=shape_class, vertices=vertices, faces=faces)
            else:
                return PolyShapeDefinition(shape_class=shape_class,
                                           vertices=vertices, color=color)
        except Exception:
            warnings.warn("Failed to parse shape definition, "
                          "using fallback mode. ({})".format(line))
            return FallbackShapeDefinition(line)

    def read(self):
        "Read the frame data from the stream."
        self.stream.seek(self.start)
        i = line = None

        def _assert(assertion):
            assert i is not None
            assert line is not None
            if not assertion:
                raise ParserError(
                    "Failed to read line #{}: {}.".format(i, line))
        monotype = False
        raw_frame = _RawFrameData()
        for i, line in enumerate(self.stream):
            if _is_comment(line):
                continue
            if line.startswith('#'):
                if line.startswith('#[data]'):
                    _assert(raw_frame.data is None)
                    raw_frame.data_keys, raw_frame.data, j = \
                        self._read_data_section(line, self.stream)
                    i += j
                else:
                    raise ParserError(line)
            else:
                tokens = line.rstrip().split()
                if not tokens:
                    continue  # empty line
                elif tokens[0] in TOKENS_SKIP:
                    continue  # skip these lines
                if tokens[0] == 'eof':
                    logger.debug("Reached end of frame.")
                    break
                elif tokens[0] == 'def':
                    definition, data, end = line.strip().split('"')
                    _assert(len(end) == 0)
                    name = definition.split()[1]
                    raw_frame.shapedef[
                        name] = self._parse_shape_definition(data)
                elif tokens[0] == 'shape':  # monotype
                    definition = line.strip().split('"')[1]
                    raw_frame.shapedef[self.default_type] = \
                        self._parse_shape_definition(definition)
                    _assert(len(raw_frame.shapedef) == 1)
                    monotype = True
                elif tokens[0] in ('boxMatrix', 'box'):
                    if len(tokens) == 10:
                        raw_frame.box = np.array(
                            [self._num(v) for v in tokens[1:]]).reshape((3, 3))
                    elif len(tokens) == 4:
                        raw_frame.box = np.array([
                            [self._num(tokens[1]), 0, 0],
                            [0, self._num(tokens[2]), 0],
                            [0, 0, self._num(tokens[3])]]).reshape((3, 3))
                else:
                    # assume we are reading positions now
                    if not monotype:
                        name = tokens[0]
                        if not name in raw_frame.shapedef:
                            raw_frame.shapedef.setdefault(
                                name, self._parse_shape_definition(' '.join(tokens[:3])))
                    else:
                        name = self.default_type
                    if len(tokens) == 7 and isinstance(
                            raw_frame.shapedef[name], ArrowShapeDefinition):
                        xyz = tokens[-6:-3]
                        quat = tokens[-3:] + [0]
                    elif len(tokens) >= 7:
                        xyz = tokens[-7:-4]
                        quat = tokens[-4:]
                    elif len(tokens) >= 3:
                        xyz = tokens[-3:]
                        quat = (1, 0, 0, 0)
                    else:
                        raise ParserError(line)
                    raw_frame.types.append(name)
                    raw_frame.positions.append([self._num(v) for v in xyz])
                    raw_frame.orientations.append([self._num(v) for v in quat])
        return raw_frame

    def __str__(self):
        return "PosFileFrame(stream={}, start={}, end={})".format(
            self.stream, self.start, self.end)


class PosFileReader(object):
    """POS-file reader for the Glotzer Group, University of Michigan.

        Authors: Carl Simon Adorf, Richmond Newmann

        .. code::

            reader = PosFileReader()
            with open('a_posfile.pos', 'r', encoding='utf-8') as posfile:
                return reader.read(posfile)

        :param precision: The number of digits to
                          round floating-point values to.
        :type precision: int"""

    def __init__(self, precision=None):
        """Initialize a pos-file reader.

        :param precision: The number of digits to
                          round floating-point values to.
        :type precision: int
        """
        self._precision = precision or POSFILE_FLOAT_DIGITS

    def _scan(self, stream, default_type):
        start = 0
        index = 0
        for line in stream:
            index += len(line)
            if line.startswith('eof'):
                yield PosFileFrame(
                    stream, start, index,
                    self._precision, default_type)
                start = index
        if index > start:
            stream.seek(start)
            for line in stream:
                if line.startswith('boxMatrix') or line.startswith('box'):
                    stream.seek(0, 2)
                    yield PosFileFrame(
                            stream, start, index,
                            self._precision, default_type)
                    break
            else:
                logger.warning("Unexpected file ending.")

    def read(self, stream, default_type='A'):
        """Read text stream and return a trajectory instance.

        :param stream: The stream, which contains the posfile.
        :type stream: A file-like textstream.
        :param default_type: The default particle type for
                             posfile dialects without type definition.
        :type default_type: str
        """
        # Index the stream
        frames = list(self._scan(stream, default_type))
        if len(frames) == 0:
            raise ParserError("Did not read a single complete frame.")
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
