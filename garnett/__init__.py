# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""
This is a collection of samples, parsers and writers for formats
used in the Glotzer Group at the University of Michigan, Ann Arbor."""


from . import reader
from . import writer
from . import samples
from . import shapes
from . import trajectory
from .util import read, write
from .version import __version__


__all__ = [
    '__version__',
    'reader',
    'writer',
    'samples',
    'shapes',
    'trajectory',
    'read',
    'write',
]
