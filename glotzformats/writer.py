from .posfilewriter import PosFileWriter
from .ciffilewriter import CifFileWriter

try:
    from .gsdhoomdfilewriter import GSDHOOMDFileWriter
except ImportError:
    class GSDHOOMDFileWriter(object):
        """Dummy implementation to provide useful errors for users"""
        def __init__(self):
            raise ImportError("Writing GSD files using glotzformats requires the gsd package. Please install it if you wish to write GSD files.")

__all__ = ['PosFileWriter', 'CifFileWriter', 'GSDHOOMDFileWriter']
