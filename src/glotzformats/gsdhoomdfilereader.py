"""Hoomd-GSD-file reader for the Glotzer Group, University of Michigan.

Author: Carl Simon Adorf

This module provides a wrapper for the gsd.hoomd and the gsd.pygsd
trajectory reader implementation as part of the gsd package.

A gsd file may not contain all shape information.
To provide additional information it is possible
to pass a frame object, whose properties
are copied into each frame of the gsd trajectory.

The example is given for a hoomd-blue xml frame:

.. code::

    xml_reader = HoomdBlueXMLFileReader()
    gsd_reader = GSDHoomdFileReader()

    with open('init.xml') as xmlfile:
        with open('dump.gsd') as gsdfile:
            xml_frame = xml_reader.read(xmlfile)[0]
            traj = gsd_reader.read(gsdfile, xml_frame)
"""

import logging
import copy

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory
from . import pygsd
from . import gsdhoomd


logger = logging.getLogger(__name__)


def _box_matrix(box):
    lx, ly, lz, xy, xz, yz = box
    return np.array([
        [lx, 0.0, 0.0],
        [xy * ly, ly, 0.0],
        [xz * lz, yz * lz, lz]]).T


class GSDHoomdFrame(Frame):

    def __init__(self, traj, frame_index, t_frame):
        self.traj = traj
        self.frame_index = frame_index
        self.t_frame = t_frame
        super(GSDHoomdFrame, self).__init__()

    def read(self):
        raw_frame = copy.deepcopy(self.t_frame)
        frame = self.traj.read_frame(self.frame_index)
        raw_frame.box = _box_matrix(frame.configuration.box)
        raw_frame.types = [frame.particles.types[t]
                           for t in frame.particles.typeid]
        raw_frame.positions = frame.particles.position
        raw_frame.orientations = frame.particles.orientation
        return raw_frame

    def __str__(self):
        return "GSDHoomdFrame(# frames={})".format(len(self.traj))


class GSDHoomdFileReader(object):
    """Read gsd trajectory files with hoomd schema.."""

    def read(self, stream, frame=None):
        """Read binary stream and return a trajectory instance.

        :param stream: The stream, which contains the gsd-file.
        :type stream: A file-like binary stream
        :param frame: A frame containing shape information
            that is not encoded in the GSD-format.
        :type frame: :class:`trajectory.Frame`"""
        if frame is None:
            frame = _RawFrameData()
        traj = gsdhoomd.HOOMDTrajectory(pygsd.GSDFile(stream))
        frames = [GSDHoomdFrame(traj, i, t_frame=frame)
                  for i in range(len(traj))]
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)
