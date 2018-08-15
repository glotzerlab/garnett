# Copyright (c) 2018 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

#This Code is modified from Pyjavis.util.py (https://bitbucket.org/bdice/pyjavis/src/master/) written by Bradley Dice.

"""Utility functions for format detection and conversion."""
import os
import logging
from . import reader, trajectory

# Mapping of file extension to format
FORMATS = {
    '.pos': 'pos',
    '.gsd': 'gsd',
    '.zip': 'gtar',
    '.tar': 'gtar',
    '.sqlite': 'gtar',
    '.dcd': 'dcd',
    '.xml': 'xml',
    '.cif': 'cif'
}

# Mapping of format to read input mode
READ_MODES = {
    'pos': 'r',
    'gsd': 'rb',
    'gtar': 'rb',
    'dcd':'rb',
    'xml':'r',
    'cif':'r'
}

def detect_format(filename):
    extension = os.path.splitext(filename)[1]
    file_format = FORMATS[extension]
    return file_format



    """ The function 'autoread' which is declared right after this comment, is imported in the __init__.py under glotzformats.
    So, when you want to read the files with particle data (pos, gsd, gtar, dcd, xml, cif), 
    you can just give syntax line like following manner: glotzformat.autoread('filename.ext')

    """

def autoread(filename, template=None, frames=None):
    file_format = detect_format(filename)
    mode = READ_MODES[file_format]

    if not os.path.isfile(filename):
        raise FileNotFoundError('Filename {} cannot be found.'.format(
            filename))

    with open(filename, mode) as read_file:
        if file_format == 'gsd':
            gsd_reader = reader.GSDHOOMDFileReader()
            traj = gsd_reader.read(read_file, template)
        elif file_format == 'gtar':
            getar_reader = reader.GetarFileReader()
            traj = getar_reader.read(read_file)
        elif file_format == 'pos':
            pos_reader = reader.PosFileReader()
            traj = pos_reader.read(read_file)
        elif file_format == 'dcd':
            dcd_reader = reader.DCDFileReader()
            traj = dcd_reader.read(read_file)
        elif file_format == 'xml':
            xml_reader = reader.HOOMDXMLFileReader()
            traj = xml_reader.read(read_file)
        elif file_format == 'cif':
            cif_reader = reader.CifFileReader()
            traj = cif_reader.read(read_file)
        if frames is not None:
            if type(frames) is int or type(frames) is slice:
                traj = traj[frames]
            else:
                raise ValueError('Argument frames must be an int or slice.')

        if not isinstance(traj, trajectory.Trajectory):
            traj = trajectory.Trajectory([traj])
        traj.load_arrays()


    return traj
