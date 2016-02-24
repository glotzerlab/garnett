import logging
logger = logging.getLogger(__name__)

from .posfilereader import PosFileReader
from .hoomdbluexmlreader import HoomdBlueXMLReader

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
    from .dcdreader import DCDFileReader
except ImportError:
    class DCDFileReader(object):
        def __init__(self):
            raise ImportError(
                "DCDFileReader requires the mdtraj package.")

    logger.info(
        "Mocking DCDFileReader, mdtraj package not available.")

__all__ = [
    'PosFileReader', 'HoomdBlueXMLReader',
    'GetarFileReader', 'DCDFileReader']
