"""
This is a collection of samples, parsers and writers for formats
used in the Glotzer Group at the University of Michigan, Ann Arbor."""


from . import formats
from . import reader
from . import writer
from . import samples
from . import trajectory
from .util import read, write
from .convert import convert_file as convert

__version__ = '0.4.1'

__all__ = ['formats', 'reader', 'writer', 'samples', 'trajectory', 'read', 'write', 'convert']
