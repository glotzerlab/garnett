# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
from .posfilewriter import PosFileWriter
from .ciffilewriter import CifFileWriter

try:
    from .gsdhoomdfilewriter import GSDHOOMDFileWriter
except ImportError:
    class GSDHOOMDFileWriter(object):
        """Dummy implementation to provide useful errors for users"""
        def __init__(self):
            raise ImportError("Writing GSD files using garnett requires "
                              "the gsd package. Please install it if you "
                              "wish to write GSD files.")

try:
    from .getarfilewriter import GetarFileWriter
except ImportError:
    class GetarFileWriter(object):
        """Dummy implementation to provide useful errors for users"""
        def __init__(self):
            raise ImportError("Writing GTAR files using garnett requires "
                              "the libgetar package. Please install it if you "
                              "wish to write GTAR files.")

__all__ = ['PosFileWriter', 'CifFileWriter', 'GSDHOOMDFileWriter', 'GetarFileWriter']
