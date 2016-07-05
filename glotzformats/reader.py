import warnings

from .posfilereader import PosFileReader
from .hoomdbluexmlfilereader import HoomdBlueXMLFileReader
from .dcdfilereader import _DCDFileReader as PyDCDFileReader
from . import pydcdreader
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
    try:
        from . import dcdreader
    except ImportError:
        import dcdreader
except ImportError:
    warnings.warn("Failed to import dcd-reader. "
                  "Falling back to pure-python reader!")

    class DCDFileReader(PyDCDFileReader):
        pass
else:
    class DCDFileReader(PyDCDFileReader):
        dcdreader = dcdreader

__all__ = [
    'PosFileReader', 'HoomdBlueXMLFileReader',
    'PyDCDFileReader', 'DCDFileReader',
    'GetarFileReader', 'GSDHoomdFileReader']
