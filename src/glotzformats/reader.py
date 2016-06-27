import logging
logger = logging.getLogger(__name__)

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

    logger.info(
        "Mocking GetarFileReader, gtar package not available.")
try:
    from .dcdfilereader import DCDFileReader
except ImportError:
    logger.warning("Failed to import cythonized dcd-reader. "
        "Using pure-python fallback reader!")
    from .pydcdfilereader import PyDCDFileReader as DCDFileReader

__all__ = [
    'PosFileReader', 'HoomdBlueXMLFileReader',
    'DCDFileReader', 'GetarFileReader',
    'GSDHoomdFileReader']
