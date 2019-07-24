# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""getar-file reader for the Glotzer Group, University of Michigan.

Authors: Matthew Spellings, Carl Simon Adorf

.. code::

    reader = GetarFileReader()
    traj = reader.read(open('trajectory.tar', 'rb'))
"""

import json
import logging
import collections

import numpy as np
import gtar

from .trajectory import _RawFrameData, Box, Frame, Trajectory
from .shapes import FallbackShape, SphereShape, ConvexPolyhedronShape, \
    ConvexSpheropolyhedronShape, GeneralPolyhedronShape, PolygonShape, \
    SpheropolygonShape, EllipsoidShape

logger = logging.getLogger(__name__)


def _parse_shape_definition(shape):
    if not shape:
        return FallbackShape('')

    rounding_radius = shape.get('rounding_radius', 0)
    shape_type = shape['type'].lower()

    shapedef = None

    if shape_type in ('sphere', 'disk'):
        diameter = shape.get('diameter', 2*shape.get('rounding_radius', 0.5))
        orientable = shape.get('orientable', False)
        shapedef = SphereShape(diameter=diameter, orientable=orientable, color=None)
    elif shape_type == 'convexpolyhedron':
        if rounding_radius == 0:
            shapedef = ConvexPolyhedronShape(vertices=shape['vertices'], color=None)
        else:
            shapedef = ConvexSpheropolyhedronShape(vertices=shape['vertices'],
                                                   rounding_radius=rounding_radius,
                                                   color=None)
    elif shape_type == 'polyhedron':
        shapedef = GeneralPolyhedronShape(vertices=shape['vertices'],
                                          faces=shape['faces'],
                                          facet_colors=shape['colors'],
                                          color=None)
    elif shape_type == 'polygon':
        if rounding_radius == 0:
            shapedef = PolygonShape(vertices=shape['vertices'], color=None)
        else:
            shapedef = SpheropolygonShape(vertices=shape['vertices'],
                                          rounding_radius=rounding_radius,
                                          color=None)
    elif shape_type == 'ellipsoid':
        shapedef = EllipsoidShape(a=shape['a'], b=shape['b'], c=shape['c'], color=None)

    if shapedef is None:
        logger.warning("Failed to parse shape definition: shape {} not supported. "
                       "Using fallback mode.".format(shape_type))
        shapedef = FallbackShape(json.dumps(shape))

    return shapedef


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
        raw_frame.shapedef = collections.OrderedDict()
        prop_map = {
            'position': 'positions',
            'orientation': 'orientations',
            'velocity': 'velocities',
            'angular_momentum_quat': 'angmom',
            'image': 'image'}
        supported_records = ['position', 'orientation', 'velocity',
                             'mass', 'charge', 'diameter',
                             'moment_inertia', 'angular_momentum_quat',
                             'image']
        for name in supported_records:
            try:
                values = self._trajectory.getRecord(
                    self._records[name], self._frame)
            except KeyError:
                values = None

            if values is not None:
                frame_prop = prop_map.get(name, name)
                setattr(raw_frame, frame_prop, values)

        if 'type' in self._records and 'type_names.json' in self._records:
            names = json.loads(self._trajectory.getRecord(
                self._records['type_names.json'], self._frame))
            types = self._trajectory.getRecord(
                self._records['type'], self._frame)
            raw_frame.types = [names[t] for t in types]
        else:
            raw_frame.types = len(raw_frame.positions) * [self._default_type]

        if 'box' in self._records:
            # Read dimension if stored
            if 'dimensions' in self._records:
                dimensions = self._trajectory.getRecord(
                             self._records['dimensions'], self._frame)[0]
            # Fallback to detection based on z coordinates
            else:
                zs = raw_frame.positions[:, 2]
                dimensions = 2 if np.allclose(zs, 0.0, atol=1e-7) else 3

            box = self._trajectory.getRecord(self._records['box'], self._frame)
            gbox = Box(
                **dict(
                    zip(['Lx', 'Ly', 'Lz', 'xy', 'xz', 'yz'], box),
                    dimensions=dimensions)
            )
            raw_frame.box = np.array(gbox.get_box_matrix())
            raw_frame.box_dimensions = int(dimensions)
        else:
            raw_frame.box = self._default_box

        if 'type_names.json' in self._records and 'type_shapes.json' in self._records:
            names = json.loads(self._trajectory.getRecord(
                self._records['type_names.json'], self._frame))
            shapes = json.loads(self._trajectory.getRecord(
                self._records['type_shapes.json'], self._frame))
            for name, shape in zip(names, shapes):
                shape_def = _parse_shape_definition(shape)
                raw_frame.shapedef.update({name: shape_def})

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
