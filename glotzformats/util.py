# Copyright (c) 2018 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

"""Utility functions for format detection and conversion."""
import os
import logging
from .common import six
from contextlib import contextmanager
from . import reader, trajectory


logger = logging.getLogger(__name__)


# Mapping of file extension to format
FORMATS = {
    '.pos': 'pos',
    '.gsd': 'gsd',
    '.zip': 'gtar',
    '.tar': 'gtar',
    '.sqlite': 'gtar',
    '.dcd': 'dcd',
    '.xml': 'xml',
    '.cif': 'cif'}

# Mapping of format to reader classes and input modes
READ_CLASS_MODES = {
    'pos': {
        'reader': reader.PosFileReader,
        'mode': 'r'},
    'gsd': {
        'reader': reader.GSDHOOMDFileReader,
        'mode': 'rb'},
    'gtar': {
        'reader': reader.GetarFileReader,
        'mode': 'rb'},
    'dcd': {
        'reader': reader.DCDFileReader,
        'mode': 'rb'},
    'xml': {
        'reader': reader.HOOMDXMLFileReader,
        'mode': 'r'},
    'cif': {
        'reader': reader.CifFileReader,
        'mode': 'r'}}


def _detect_format(filename):
    extension = os.path.splitext(filename)[1]
    try:
        file_format = FORMATS[extension]
    except KeyError:
        raise NotImplementedError(
            'The extension "{}" is not supported as a trajectory file.'.format(
                extension))
    return file_format


@contextmanager
def read(filename_or_fileobj, template=None):
    """This function automatically detects the file format, read the file, and
    returns a trajectory object.

    :param filename: Filename to read.
    :param template: Optional template for the GSDHOOMDFileReader.
    :param frames: Optional integer or slice object to subset the trajectory.
    :type filename: string
    :type template: string
    :type frames: int or slice
    :returns: Trajectory read from the file.
    :rtype: :class:`glotzformats.trajectory.Trajectory`
    """
    if isinstance(filename_or_fileobj, six.string_types):
        filename = filename_or_fileobj
    else:
        try:
            filename = filename_or_fileobj.name
        except AttributeError:
            raise RuntimeError(
                "Unable to determine filename from file object, "
                "which is required for format detection.")

    file_format = _detect_format(filename)
    reader = READ_CLASS_MODES[file_format]['reader']()
    mode = READ_CLASS_MODES[file_format]['mode']

    with open(filename, mode) as read_file:
        if file_format == 'gsd':
            traj = reader.read(read_file, template)
        else:
            traj = reader.read(read_file)

        yield traj
