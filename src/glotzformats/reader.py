import logging
logger = logging.getLogger(__name__)

from .posfilereader import PosFileReader

__all__ = ['PosFileReader']

try:
    from .getarfilereader import GetarFileReader
    __all__.append('GetarFileReader')
except ImportError:
    logger.warning("Error importing GetarFileReader")
