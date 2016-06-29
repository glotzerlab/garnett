import warnings

from .posfilereader import PosFileReader
from .hoomdbluexmlfilereader import HoomdBlueXMLFileReader
from .pydcdfilereader import PyDCDFileReader
from .gsdhoomdfilereader import GSDHoomdFileReader

try:
    from .getarfilereader import GetarFileReader
except ImportError:
    class GetarFileReader(object):
        def __init__(self):
            raise ImportError(
                "GetarFileReader requires the gtar package.")

    warnings.warn(
        "Mocking GetarFileReader, gtar package not available.")
try:
    from .dcdfilereader import DCDFileReader
except ImportError:
    warnings.warn("Failed to import cythonized dcd-reader. "
        "Falling back to pure-python reader!")
    from .pydcdfilereader import PyDCDFileReader as DCDFileReader

__all__ = [
    'PosFileReader', 'HoomdBlueXMLFileReader',
    'PyDCDFileReader', 'DCDFileReader',
    'GetarFileReader', 'GSDHoomdFileReader']
