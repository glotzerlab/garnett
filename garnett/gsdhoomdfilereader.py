# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
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
import collections

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory
from .shapes import SphereShape, ConvexPolyhedronShape, ConvexSpheropolyhedronShape, \
    PolygonShape, SpheropolygonShape, EllipsoidShape

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

    def get_chunk(i, chunk, default=None):
        if gsdfile.chunk_exists(i, chunk):
            return gsdfile.read_chunk(i, chunk)
        elif gsdfile.chunk_exists(0, chunk):
            return gsdfile.read_chunk(0, chunk)
        else:
            return default

    shapedefs = collections.OrderedDict()
    types = frame.particles.types

    # Spheres
    if get_chunk(frame_index, 'state/hpmc/sphere/radius') is not None:
        radii = get_chunk(frame_index, 'state/hpmc/sphere/radius')
        orientables = get_chunk(frame_index, 'state/hpmc/sphere/orientable')
        # Since the orientable chunk was only added in HOOMD Schema version 1.3,
        # not all GSD files may have it. Thus, it is set to False in such cases.
        if orientables is None:
            orientables = [False]*len(radii)
        for typename, radius, orientable in zip(types, radii, orientables):
            shapedefs[typename] = SphereShape(
                diameter=radius*2, orientable=orientable, color=None)
        return shapedefs

    # Convex Polyhedra
    elif get_chunk(frame_index, 'state/hpmc/convex_polyhedron/N') is not None:
        N = get_chunk(frame_index, 'state/hpmc/convex_polyhedron/N')
        N_start = [sum(N[:i]) for i in range(len(N))]
        N_end = [sum(N[:i+1]) for i in range(len(N))]
        verts = get_chunk(frame_index, 'state/hpmc/convex_polyhedron/vertices')
        verts_split = [verts[start:end] for start, end in zip(N_start, N_end)]
        for typename, typeverts in zip(types, verts_split):
            shapedefs[typename] = ConvexPolyhedronShape(
                vertices=typeverts, color=None)
        return shapedefs

    # Convex Spheropolyhedra
    elif get_chunk(frame_index, 'state/hpmc/convex_spheropolyhedron/N') is not None:
        N = get_chunk(frame_index, 'state/hpmc/convex_spheropolyhedron/N')
        N_start = [sum(N[:i]) for i in range(len(N))]
        N_end = [sum(N[:i+1]) for i in range(len(N))]
        verts = get_chunk(frame_index,
                          'state/hpmc/convex_spheropolyhedron/vertices')
        verts_split = [verts[start:end] for start, end in zip(N_start, N_end)]
        sweep_radii = get_chunk(frame_index,
                                'state/hpmc/convex_spheropolyhedron/sweep_radius')
        for typename, typeverts, radius in zip(types, verts_split, sweep_radii):
            shapedefs[typename] = ConvexSpheropolyhedronShape(
                vertices=typeverts, rounding_radius=radius, color=None)
        return shapedefs

    # Ellipsoid
    elif get_chunk(frame_index, 'state/hpmc/ellipsoid/a') is not None:
        a_all = get_chunk(frame_index, 'state/hpmc/ellipsoid/a')
        b_all = get_chunk(frame_index, 'state/hpmc/ellipsoid/b')
        c_all = get_chunk(frame_index, 'state/hpmc/ellipsoid/c')
        for typename, a, b, c in zip(types, a_all, b_all, c_all):
            shapedefs[typename] = EllipsoidShape(
                a=a, b=b, c=c, color=None)
        return shapedefs

    # Convex Polygons
    elif get_chunk(frame_index, 'state/hpmc/convex_polygon/N') is not None:
        N = get_chunk(frame_index, 'state/hpmc/convex_polygon/N')
        N_start = [sum(N[:i]) for i in range(len(N))]
        N_end = [sum(N[:i+1]) for i in range(len(N))]
        verts = get_chunk(frame_index, 'state/hpmc/convex_polygon/vertices')
        verts_split = [verts[start:end] for start, end in zip(N_start, N_end)]
        for typename, typeverts in zip(types, verts_split):
            shapedefs[typename] = PolygonShape(
                vertices=typeverts, color=None)
        return shapedefs

    # Convex Spheropolygons
    elif get_chunk(frame_index, 'state/hpmc/convex_spheropolygon/N') is not None:
        N = get_chunk(frame_index, 'state/hpmc/convex_spheropolygon/N')
        N_start = [sum(N[:i]) for i in range(len(N))]
        N_end = [sum(N[:i+1]) for i in range(len(N))]
        verts = get_chunk(frame_index, 'state/hpmc/convex_spheropolygon/vertices')
        verts_split = [verts[start:end] for start, end in zip(N_start, N_end)]
        sweep_radii = get_chunk(frame_index,
                                'state/hpmc/convex_spheropolygon/sweep_radius')
        for typename, typeverts, radius in zip(types, verts_split, sweep_radii):
            shapedefs[typename] = SpheropolygonShape(
                vertices=typeverts, rounding_radius=radius, color=None)
        return shapedefs

    # Simple Polygons
    elif get_chunk(frame_index, 'state/hpmc/simple_polygon/N') is not None:
        N = get_chunk(frame_index, 'state/hpmc/simple_polygon/N')
        N_start = [sum(N[:i]) for i in range(len(N))]
        N_end = [sum(N[:i+1]) for i in range(len(N))]
        verts = get_chunk(frame_index, 'state/hpmc/simple_polygon/vertices')
        verts_split = [verts[start:end] for start, end in zip(N_start, N_end)]
        for typename, typeverts in zip(types, verts_split):
            shapedefs[typename] = PolygonShape(
                vertices=typeverts, color=None)
        return shapedefs
    # If no shapes were detected, return None
    else:
        return None


class GSDHoomdFrame(Frame):
    """Extends the Frame object for GSD files.

    :param traj:
        Trajectory containing the frame to cast
    :type traj:
        :class:`trajectory.Trajectory`
    :param frame_index:
        The index of the frame to cast
    :type frame_index:
        int
    :param t_frame:
        A frame containing shape information that is not encoded in
        the GSD-format. By default, shape information is read from the
        passed frame object, if one provided. Otherwise, shape information
        is read from the gsd file.
    :type :
        :class:`trajectory.Frame`
    :param gsdfile:
        A gsd file object.
    :type gsdfile:
        :class:`gsd.fl.GSDFile`
    """

    def __init__(self, traj, frame_index, t_frame, gsdfile):
        self.traj = traj
        self.frame_index = frame_index
        self.t_frame = t_frame
        self.gsdfile = gsdfile
        super(GSDHoomdFrame, self).__init__()

    def read(self):
        raw_frame = _RawFrameData()
        frame = self.traj.read_frame(self.frame_index)
        # If frame is provided, read shape data from it
        if self.t_frame is not None:
            raw_frame.data = copy.deepcopy(self.t_frame.data)
            raw_frame.data_keys = copy.deepcopy(self.t_frame.data_keys)
            raw_frame.box_dimensions = self.t_frame.box.dimensions
            try:
                raw_frame.shapedef = copy.deepcopy(self.t_frame.shapedef)
            except AttributeError:
                pass
        else:
            # Fallback to gsd shape data if no frame is provided
            raw_frame.shapedef = _parse_shape_definitions(frame, self.gsdfile, self.frame_index)
        raw_frame.box = _box_matrix(frame.configuration.box)
        raw_frame.box_dimensions = int(frame.configuration.dimensions)
        raw_frame.types = [frame.particles.types[t] for t in frame.particles.typeid]
        raw_frame.positions = frame.particles.position
        raw_frame.orientations = frame.particles.orientation
        raw_frame.velocities = frame.particles.velocity
        raw_frame.mass = frame.particles.mass
        raw_frame.charge = frame.particles.charge
        raw_frame.diameter = frame.particles.diameter
        raw_frame.moment_inertia = frame.particles.moment_inertia
        raw_frame.angmom = frame.particles.angmom
        raw_frame.image = frame.particles.image
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

    The example is given for a HOOMD-blue XML frame:

    .. code::

        xml_reader = HOOMDXMLFileReader()
        gsd_reader = GSDHOOMDFileReader()

        with open('init.xml') as xmlfile:
            with open('dump.gsd', 'rb') as gsdfile:
                xml_frame = xml_reader.read(xmlfile)[0]
                traj = gsd_reader.read(gsdfile, xml_frame)

    About the read_gsd_shape_data parameter: This parameter was removed. By default,
                shape information is read from a passed frame object, if one
                provided. Otherwise, shape information is read from the gsd file.

    """

    def __init__(self):
        pass

    def read(self, stream, frame=None):
        """Read binary stream and return a trajectory instance.

        :param stream: The stream, which contains the gsd-file.
        :type stream: A file-like binary stream
        :param frame: A frame containing shape information
            that is not encoded in the GSD-format. By default,
            shape information is read from the passed frame object,
            if one provided. Otherwise, shape information
            is read from the gsd file.
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
            warnings.warn("Native GSD library not available. "
                          "Falling back to pure python reader.")
            gsdfile = PyGSDFile(stream)
            traj = gsdhoomd.HOOMDTrajectory(gsdfile)
        frames = [GSDHoomdFrame(traj, i, t_frame=frame, gsdfile=gsdfile)
                  for i in range(len(traj))]
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
