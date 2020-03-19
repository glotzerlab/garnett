# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

"""Utility functions for format detection and simple reading/writing."""
import os
import logging
from contextlib import contextmanager
from . import reader, writer


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

# Mapping of format to writer classes and input modes
WRITE_CLASS_MODES = {
    'pos': {
        'writer': writer.PosFileWriter,
        'mode': 'w'},
    'gsd': {
        'writer': writer.GSDHOOMDFileWriter,
        'mode': 'wb'},
    'gtar': {
        'writer': writer.GetarFileWriter,
        'mode': 'w'},
    'cif': {
        'writer': writer.CifFileWriter,
        'mode': 'w'}}


def detect_format(filename):
    extension = os.path.splitext(filename)[1]
    try:
        file_format = FORMATS[extension]
    except KeyError:
        raise NotImplementedError(
            'The extension "{}" is not supported as a trajectory file.'.format(
                extension))
    return file_format


@contextmanager
def read(filename_or_fileobj, template=None, fmt=None):
    """This function reads a file and returns a trajectory, autodetecting the file format unless ``fmt`` is specified.

    :param filename_or_fileobj: Filename to read.
    :type filename_or_fileobj: string or file object
    :param template: Optional template for the GSDHOOMDFileReader.
    :type template: string
    :param fmt: File format, one of 'gsd', 'gtar', 'pos', 'cif', 'dcd', 'xml'
        (default: None, autodetected from filename_or_fileobj)
    :type fmt: string
    :returns: Trajectory read from the file.
    :rtype: :class:`~garnett.trajectory.Trajectory`
    """
    if isinstance(filename_or_fileobj, str):
        is_fileobj = False
        filename = filename_or_fileobj
    else:
        is_fileobj = True
        try:
            filename = filename_or_fileobj.name
        except AttributeError:
            raise RuntimeError(
                "Unable to determine filename from file object, "
                "which is required for format detection.")

    file_format = fmt or detect_format(filename)
    file_reader = READ_CLASS_MODES[file_format]['reader']()
    mode = READ_CLASS_MODES[file_format]['mode']

    with filename_or_fileobj if is_fileobj else open(filename_or_fileobj, mode) as read_file:
        if template is None:
            traj = file_reader.read(read_file)
            yield traj
        elif file_format == 'gsd':
            file_reader = READ_CLASS_MODES[file_format]['reader']()
            with read(template) as templatetraj:
                traj = file_reader.read(read_file, templatetraj[0])
                yield traj
        else:
            raise ValueError('The reader class {} does not support templates.'.format(file_reader.__class__.__name__))


def write(traj, filename_or_fileobj, fmt=None):
    """This function writes a trajectory to a file, autodetecting the file format unless ``fmt`` is specified.

    :param traj: Trajectory to write.
    :type traj: :class:`~garnett.trajectory.Trajectory`
    :param filename_or_fileobj: Filename to write.
    :type filename_or_fileobj: string or file object
    :param fmt: File format, one of 'gsd', 'gtar', 'pos', 'cif'
        (default: None, autodetected from filename_or_fileobj)
    :type fmt: string
    """
    if isinstance(filename_or_fileobj, str):
        is_fileobj = False
        filename = filename_or_fileobj
    else:
        is_fileobj = True
        try:
            filename = filename_or_fileobj.name
        except AttributeError:
            raise RuntimeError(
                "Unable to determine filename from file object, "
                "which is required for format detection.")

    file_format = detect_format(filename) if fmt is None else fmt
    file_writer = WRITE_CLASS_MODES[file_format]['writer']()
    mode = WRITE_CLASS_MODES[file_format]['mode']

    with filename_or_fileobj if is_fileobj else open(filename_or_fileobj, mode) as write_file:
        file_writer.write(traj, write_file)
