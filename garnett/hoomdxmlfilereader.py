# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""Hoomd-blue XML-file reader for the Glotzer Group, University of Michigan.

Authors: Carl Simon Adorf

.. code::

    reader = HOOMDXMLFileReader()
    with open('hoomdblue.xml') as xmlfile:
        return reader.read(xmlfile)
"""

import logging
import warnings
import xml.etree.ElementTree as ET

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory
from .errors import ParserError


logger = logging.getLogger(__name__)


class HOOMDXMLFrame(Frame):

    def __init__(self, root):
        self.root = root
        super(HOOMDXMLFrame, self).__init__()

    def read(self):
        "Read the frame data from the stream."
        raw_frame = _RawFrameData()
        config = self.root.find('configuration')
        raw_frame.box = np.asarray(_get_box_matrix(config.find('box')))
        raw_frame.box_dimensions = int(config.get('dimensions', 3))
        raw_frame.position = list(_parse_position(config.find('position')))
        orientation = config.find('orientation')
        if orientation is not None:
            raw_frame.orientation = list(_parse_orientation(orientation))
        velocity = config.find('velocity')
        if velocity is not None:
            raw_frame.velocity = list(_parse_velocity(velocity))

        raw_frame.types = list(_parse_types(config.find('type')))
        return raw_frame

    def __str__(self):
        return "HOOMDXMLFrame(root={})".format(self.root)


class HOOMDXMLFileReader(object):
    "Reader for XML-files containing HOOMD-blue snapshots."

    def read(self, stream):
        """Read text stream and return a trajectory instance.

        :param stream: The stream, which contains the xmlfile.
        :type stream: A file-like textstream.
        """
        # Index the stream
        try:
            frames = [HOOMDXMLFrame(ET.fromstring(stream.read()))]
        except ET.ParseError as error:
            raise ParserError(error)
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)


def _get_box_matrix(box):
    assert box is not None

    def _get(name, default=None):
        v = box.get(name)
        if v is None and default is None:
            raise KeyError(name)
        elif v is None:
            return float(default)
        else:
            return float(v)
    return [
        [_get('lx'), _get('xy', 0) * _get('ly'), _get('xz', 0) * _get('lz')],
        [0.0, _get('ly'), _get('yz', 0) * _get('lz')],
        [0.0, 0.0, _get('lz')]
    ]


def _parse_position(position):
    for i, position in enumerate(position.text.splitlines()[1:]):
        yield [float(x) for x in position.split()]
    if i + 1 != int(position.attrib.get('num', i + 1)):
        warnings.warn("Number of position inconsistent.")


def _parse_velocity(velocity):
    for i, velocity in enumerate(velocity.text.splitlines()[1:]):
        yield [float(x) for x in velocity.split()]
    if i + 1 != int(velocity.attrib.get('num', i + 1)):
        warnings.warn("Number of velocity inconsistent.")


def _parse_orientation(orientation):
    for i, orientation in enumerate(orientation.text.splitlines()[1:]):
        yield [float(x) for x in orientation.split()]
    if i + 1 != int(orientation.attrib.get('num', i + 1)):
        warnings.warn("Number of orientation inconsistent.")


def _parse_types(types):
    for i, type in enumerate(types.text.splitlines()[1:]):
        yield str(type)
    if i + 1 != int(types.attrib.get('num', i)):
        warnings.warn("Number of types inconsistent.")
