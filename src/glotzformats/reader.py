import logging
logger = logging.getLogger(__name__)

from .posfilereader import PosFileReader
from .hoomdbluexmlreader import HoomdBlueXMLReader
__all__ = ['PosFileReader', 'HoomdBlueXMLReader']

try:
    from .getarfilereader import GetarFileReader
    __all__.append('GetarFileReader')
except ImportError:
    logger.warning("Error importing GetarFileReader")
