# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
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

from .trajectory import _RawFrameData, Frame, Trajectory
from .shapes import FallbackShape, SphereShape, ArrowShape, SphereUnionShape, \
    PolygonShape, ConvexPolyhedronShape, ConvexSpheropolyhedronShape, \
    ConvexPolyhedronUnionShape, GeneralPolyhedronShape, EllipsoidShape
import rowan

from .errors import ParserError, ParserWarning

logger = logging.getLogger(__name__)

POSFILE_FLOAT_DIGITS = 11
COMMENT_CHARACTERS = ['//']
TOKENS_SKIP = ['translation', 'antiAliasing', 'zoomFactor', 'showEdges', 'connection']


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
        tokens = (t for t in line.split())
        shape_class = next(tokens)
        if shape_class.lower() == 'sphere':
            diameter = float(next(tokens))
            try:
                color = next(tokens)
            except StopIteration:
                color = None
            return SphereShape(diameter=diameter,
                               color=color)
        elif shape_class.lower() == 'arrow':
            thickness = float(next(tokens))
            try:
                color = next(tokens)
            except StopIteration:
                color = None
            return ArrowShape(thickness=thickness,
                              color=color)
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
            return SphereUnionShape(diameters=diameters,
                                    centers=centers,
                                    colors=colors)
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
            return ConvexPolyhedronUnionShape(vertices=vertices,
                                              centers=centers,
                                              orientations=orientations,
                                              colors=colors)
        elif shape_class.lower() == 'polyv':  # Officially polyV
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
            return GeneralPolyhedronShape(vertices=vertices,
                                          faces=faces)
        elif shape_class.lower() == 'poly3d':
            num_vertices = int(next(tokens))
            vertices = []
            for i in range(num_vertices):
                xyz = next(tokens), next(tokens), next(tokens)
                vertices.append([self._num(v) for v in xyz])
            try:
                color = next(tokens)
            except StopIteration:
                color = None
            vertices = np.asarray(vertices)
            if (vertices[:, 2] == 0).all():
                # If the z-components of all vertices are zero,
                # create a 2D polygon instead
                return PolygonShape(vertices=vertices[:, :2],
                                    color=color)
            else:
                return ConvexPolyhedronShape(vertices=vertices,
                                             color=color)

            return ConvexPolyhedronShape(vertices=vertices,
                                         color=color)
        elif shape_class.lower() == 'spoly3d':
            rounding_radius = float(next(tokens))
            num_vertices = int(next(tokens))
            vertices = []
            for i in range(num_vertices):
                xyz = next(tokens), next(tokens), next(tokens)
                vertices.append([self._num(v) for v in xyz])
            try:
                color = next(tokens)
            except StopIteration:
                color = None
            # Note: In POS files, there is no way to distinguish a 2D
            # spheropolygon with class spoly3d from a 3D spheropolyhedron whose
            # vertices lie in the x-y plane (with a rounding radius, it becomes
            # 3D).
            return ConvexSpheropolyhedronShape(vertices=vertices,
                                               rounding_radius=rounding_radius,
                                               color=color)
        elif shape_class.lower() == 'cyl':
            rounding_radius = float(next(tokens))/2
            height = float(next(tokens))
            if height > 0:
                vertices = [[-height/2, 0, 0], [height/2, 0, 0]]
            else:
                vertices = [[0, 0, 0]]
            try:
                color = next(tokens)
            except StopIteration:
                color = None
            return ConvexSpheropolyhedronShape(vertices=vertices,
                                               rounding_radius=rounding_radius,
                                               color=color)
        elif shape_class.lower() == 'ellipsoid':
            a = float(next(tokens))
            b = float(next(tokens))
            c = float(next(tokens))
            try:
                color = next(tokens)
            except StopIteration:
                color = None
            return EllipsoidShape(a=a,
                                  b=b,
                                  c=c,
                                  color=color)
        else:
            warnings.warn("Failed to parse shape definition, "
                          "using fallback mode. ({})".format(line))
            return FallbackShape(line)

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
        raw_frame.view_rotation = None
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
                    type_shape = self._parse_shape_definition(data)
                    if name not in raw_frame.types:
                        raw_frame.types.append(name)
                        raw_frame.type_shapes.append(type_shape)
                    else:
                        typeid = raw_frame.type_shapes.index(name)
                        raw_frame.type_shapes[typeid] = type_shape
                        warnings.warn("Redefinition of type '{}'.".format(name))
                elif tokens[0] == 'shape':  # monotype
                    data = line.strip().split('"')[1]
                    raw_frame.types.append(self.default_type)
                    type_shape = self._parse_shape_definition(data)
                    raw_frame.type_shapes.append(type_shape)
                    _assert(len(raw_frame.type_shapes) == 1)
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
                elif tokens[0] == 'rotation':
                    euler_angles = np.array([float(t) for t in tokens[1:]])
                    euler_angles *= np.pi / 180
                    raw_frame.view_rotation = rowan.from_euler(*euler_angles, axis_type='extrinsic', convention='xyz')
                else:
                    # assume we are reading positions now
                    if not monotype:
                        name = tokens[0]
                        if name not in raw_frame.types:
                            raw_frame.types.append(name)
                            type_shape = self._parse_shape_definition(' '.join(tokens[:3]))
                            raw_frame.type_shapes.append(type_shape)
                    else:
                        name = self.default_type
                    typeid = raw_frame.types.index(name)
                    type_shape = raw_frame.type_shapes[typeid]
                    if len(tokens) == 7 and isinstance(type_shape, ArrowShape):
                        xyz = tokens[-6:-3]
                        quat = tokens[-3:] + [0]
                    elif len(tokens) >= 7:
                        xyz = tokens[-7:-4]
                        quat = tokens[-4:]
                    elif len(tokens) >= 3:
                        xyz = tokens[-3:]
                        quat = None
                    else:
                        raise ParserError(line)
                    raw_frame.typeid.append(typeid)
                    raw_frame.position.append([self._num(v) for v in xyz])
                    if quat is None:
                        raw_frame.orientation.append(quat)
                    else:
                        raw_frame.orientation.append([self._num(v) for v in quat])

        # Perform inverse rotation to recover original coordinates
        if raw_frame.view_rotation is not None:
            pos = rowan.rotate(rowan.inverse(raw_frame.view_rotation), raw_frame.position)
        else:
            pos = np.asarray(raw_frame.position)
        # If all the z coordinates are close to zero, set box dimension to 2
        if np.allclose(pos[:, 2], 0.0, atol=1e-7):
            raw_frame.box_dimensions = 2

        # If no valid orientations have been added, the array should be empty
        if all([quat is None for quat in raw_frame.orientation]):
            raw_frame.orientation = []
        else:
            # Replace values of None with an identity quaternion
            for i in range(len(raw_frame.orientation)):
                if raw_frame.orientation[i] is None:
                    raw_frame.orientation[i] = [1, 0, 0, 0]
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
