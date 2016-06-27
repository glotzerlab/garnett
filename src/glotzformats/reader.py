import logging
logger = logging.getLogger(__name__)

from .posfilereader import PosFileReader
from .hoomdbluexmlfilereader import HoomdBlueXMLFileReader
from .dcdfilereader import DCDFileReader
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

__all__ = [
    'PosFileReader', 'HoomdBlueXMLFileReader',
    'DCDFileReader', 'GetarFileReader',
    'GSDHoomdFileReader']
