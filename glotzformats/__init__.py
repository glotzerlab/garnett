"""
This is a collection of samples, parsers and writers for formats
used in the Glotzer Group at the University of Michigan, Ann Arbor."""


from . import formats
from . import reader
from . import writer
from . import samples
from . import shapes
from . import trajectory
from .util import read, write

__version__ = '0.4.1'

__all__ = [
    'formats',
    'reader',
    'writer',
    'samples',
    'shapes',
    'trajectory',
    'read',
    'write',
]
