"""
This is a collection of samples, parsers and writers for formats
used in the Glotzer Group at the University of Michigan, Ann Arbor."""


from . import formats
from . import reader
from . import writer
from . import samples
from . import trajectory
from .reader_function import autoread ## to make a shortcut syntax when reading files having particle data. (glotzformats.autoread('filename.ext'))

__version__ = '0.4.1'

__all__ = ['formats', 'reader', 'writer', 'samples', 'trajectory','autoread']
