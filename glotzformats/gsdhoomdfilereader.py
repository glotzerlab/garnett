"""Hoomd-GSD-file reader for the Glotzer Group, University of Michigan.

Author: Carl Simon Adorf

This module provides a wrapper for the trajectory reader
implementation as part of the gsd package.

A gsd file may not contain all shape information.
To provide additional information it is possible
to pass a frame object, whose properties
are copied into each frame of the gsd trajectory.

The example is given for a hoomd-blue xml frame:

.. code::

    pos_reader = PosFileReader()
    gsd_reader = GSDHOOMDFileReader()

    with open('init.pos') as posfile:
        with open('dump.gsd') as gsdfile:
            pos_frame = pos_reader.read(posfile)[0]
            traj = gsd_reader.read(gsdfile, pos_frame)
"""

import logging
import warnings
import copy

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory
from .trajectory import SphereShapeDefinition, PolyShapeDefinition, SpheroPolyShapeDefinition

try:
    from gsd.fl import GSDFile
    NATIVE = True
except ImportError:
    NATIVE = False
from .pygsd import GSDFile as PyGSDFile
from . import gsdhoomd


logger = logging.getLogger(__name__)


def _box_matrix(box):
    lx, ly, lz, xy, xz, yz = box
    return np.array([
        [lx, 0.0, 0.0],
        [xy * ly, ly, 0.0],
        [xz * lz, yz * lz, lz]]).T

def _parse_shape_definitions(frame, gsdfile, frame_index):

    def get_chunk(i, chunk):
        if gsdfile.chunk_exists(i, chunk):
            return gsdfile.read_chunk(i, chunk)
        elif gsdfile.chunk_exists(0, chunk):
            return gsdfile.read_chunk(0, chunk)
        else:
            return None

    shapedefs = dict()
    types = frame.particles.types

    # Spheres
    if get_chunk(frame_index, 'state/hpmc/sphere/radius') is not None:
        radii = get_chunk(frame_index, 'state/hpmc/sphere/radius')
        for typename, radius in zip(types, radii):
            shapedefs[typename] = SphereShapeDefinition(
                diameter=radius*2, color=None)
        return shapedefs

    # Convex Polyhedra
    if get_chunk(frame_index, 'state/hpmc/convex_polyhedron/N') is not None:
        N = get_chunk(frame_index, 'state/hpmc/convex_polyhedron/N')
        N_start = [sum(N[:i]) for i in range(len(N))]
        N_end = [sum(N[:i+1]) for i in range(len(N))]
        verts = get_chunk(frame_index, 'state/hpmc/convex_polyhedron/vertices')
        verts_split = [verts[start:end] for start, end in zip(N_start, N_end)]
        for typename, typeverts in zip(types, verts_split):
            shapedefs[typename] = PolyShapeDefinition(
                shape_class='poly3d', vertices=typeverts, color=None)
        return shapedefs

    # Convex Spheropolyhedra
    if get_chunk(frame_index, 'state/hpmc/convex_spheropolyhedron/N') is not None:
        N = get_chunk(frame_index, 'state/hpmc/convex_spheropolyhedron/N')
        N_start = [sum(N[:i]) for i in range(len(N))]
        N_end = [sum(N[:i+1]) for i in range(len(N))]
        verts = get_chunk(frame_index, 'state/hpmc/convex_spheropolyhedron/vertices')
        verts_split = [verts[start:end] for start, end in zip(N_start, N_end)]
        sweep_radii = get_chunk(frame_index, 'state/hpmc/convex_spheropolyhedron/sweep_radius')
        for typename, typeverts, radius in zip(types, verts_split, sweep_radii):
            shapedefs[typename] = SpheroPolyShapeDefinition(
                shape_class='spoly3d', vertices=typeverts,
                rounding_radius=radius, color=None)
        return shapedefs

    # Shapes supported by state/hpmc but not glotzformats ShapeDefinitions:
    if get_chunk(frame_index, 'state/hpmc/ellipsoid/a') is not None:
        warnings.warn('ellipsoid is not supported by glotzformats.')

    if get_chunk(frame_index, 'state/hpmc/convex_polygon/N') is not None:
        warnings.warn('convex_polygon is not supported by glotzformats.')

    if get_chunk(frame_index, 'state/hpmc/convex_spheropolygon/N') is not None:
        warnings.warn('convex_spheropolygon is not supported by glotzformats.')

    if get_chunk(frame_index, 'state/hpmc/simple_polygon/N') is not None:
        warnings.warn('simple_polygon is not supported by glotzformats.')

    return shapedefs


class GSDHoomdFrame(Frame):

    def __init__(self, traj, frame_index, t_frame, gsdfile):
        self.traj = traj
        self.frame_index = frame_index
        self.t_frame = t_frame
        self.gsdfile = gsdfile
        super(GSDHoomdFrame, self).__init__()

    def read(self):
        raw_frame = _RawFrameData()
        if self.t_frame is not None:
            raw_frame.data = copy.deepcopy(self.t_frame.data)
            raw_frame.data_keys = copy.deepcopy(self.t_frame.data_keys)
            raw_frame.shapedef = copy.deepcopy(self.t_frame.shapedef)
            raw_frame.box_dimensions = self.t_frame.box.dimensions
        frame = self.traj.read_frame(self.frame_index)
        raw_frame.box = _box_matrix(frame.configuration.box)
        raw_frame.box_dimensions = int(frame.configuration.dimensions)
        raw_frame.types = [frame.particles.types[t]
                           for t in frame.particles.typeid]
        raw_frame.positions = frame.particles.position
        raw_frame.orientations = frame.particles.orientation
        raw_frame.velocities = frame.particles.velocity
        raw_frame.shapedef.update(
            _parse_shape_definitions(frame, self.gsdfile, self.frame_index))
        return raw_frame

    def __str__(self):
        return "GSDHoomdFrame(# frames={})".format(len(self.traj))


class GSDHOOMDFileReader(object):
    """Hoomd-GSD-file reader for the Glotzer Group, University of Michigan.

    Author: Carl Simon Adorf

    This class provides a wrapper for the trajectory reader
    implementation as part of the gsd package.

    A gsd file may not contain all shape information.
    To provide additional information it is possible
    to pass a frame object, whose properties
    are copied into each frame of the gsd trajectory.

    The example is given for a hoomd-blue xml frame:

    .. code::

        xml_reader = HOOMDXMLFileReader()
        gsd_reader = GSDHOOMDFileReader()

        with open('init.xml') as xmlfile:
            with open('dump.gsd', 'rb') as gsdfile:
                xml_frame = xml_reader.read(xmlfile)[0]
                traj = gsd_reader.read(gsdfile, xml_frame)
    """

    def read(self, stream, frame=None):
        """Read binary stream and return a trajectory instance.

        :param stream: The stream, which contains the gsd-file.
        :type stream: A file-like binary stream
        :param frame: A frame containing shape information
            that is not encoded in the GSD-format.
        :type frame: :class:`trajectory.Frame`"""
        if NATIVE:
            try:
                gsdfile = GSDFile(stream.name, stream.mode)
                traj = gsdhoomd.HOOMDTrajectory(gsdfile)
            except AttributeError:
                logger.info(
                    "Unable to open file stream natively, falling back "
                    "to pure python GSD reader.")
                gsdfile = PyGSDFile(stream)
                traj = gsdhoomd.HOOMDTrajectory(gsdfile)
        else:
            logger.warning("Native GSD library not available. "
                           "Falling back to pure python reader.")
            gsdfile = PyGSDFile(stream)
            traj = gsdhoomd.HOOMDTrajectory(gsdfile)
        frames = [GSDHoomdFrame(traj, i, t_frame=frame, gsdfile=gsdfile)
                  for i in range(len(traj))]
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
