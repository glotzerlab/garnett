import warnings

from .posfilereader import PosFileReader
from .hoomdxmlfilereader import HOOMDXMLFileReader
from .dcdfilereader import _DCDFileReader
from .gsdhoomdfilereader import GSDHOOMDFileReader

try:
    from .getarfilereader import GetarFileReader
except ImportError:
    class GetarFileReader(object):
        def __init__(self):
            raise ImportError(
                "GetarFileReader requires the gtar package.")

    warnings.warn(
        "Mocking GetarFileReader, gtar package not available.")

class PyDCDFileReader(_DCDFileReader):
    """Pure-python DCD-file reader for the Glotzer Group.

    This class is a pure python dcd-reader implementation
    which should only be used when the more efficient
    cythonized dcd-reader is not available.

    .. seealso:: The API is identical to: :py:class:`~.DCDFileReader`"""
    pass

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
        """DCD-file reader for the Glotzer Group, University of Michigan.

        Author: Carl Simon Adorf

        A dcd file consists only of positions.
        To provide additional information it is possible
        to provide a frame object, whose properties
        are copied into each frame of the dcd trajectory.

        The example is given for a HOOMD-blue xml frame:

        .. code::

            xml_reader = HOOMDXMLFileReader()
            dcd_reader = DCDFileReader()

            with open('init.xml') as xmlfile:
                with open('dump.dcd', 'rb') as dcdfile:
                    xml_frame = xml_reader.read(xmlfile)[0]
                    traj = reader.read(dcdfile, xml_frame)

        .. note::

            If the topology frame is 2-dimensional, the dcd
            trajectory positions are interpreted such that
            the first two values contain the xy-coordinates,
            the third value is an euler angle.

            The euler angle is converted to a quaternion and stored
            in the orientation of the frame.

            To retrieve the euler angles, simply convert the quaternion:

            .. code::

                alpha = 2 * np.arccos(traj[0].orientations.T[0])
        """
        _dcdreader = dcdreader

class GSDHoomdFileReader(GSDHOOMDFileReader):

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "This class has been renamed to GSDHOOMDFileReader!",
            DeprecationWarning)
        super(GSDHoomdFileReader, self).__init__(*args, **kwargs)


class HoomdBlueXMLFileReader(HOOMDXMLFileReader):

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "This class has been renamed to HOOMDXMLFileReader!",
            DeprecationWarning)
        super(HoomdBlueXMLFileReader, self).__init__(*args, **kwargs)


__all__ = [
    'PosFileReader',
    'HOOMDXMLFileReader', 'HoomdBlueXMLFileReader',
    'PyDCDFileReader', 'DCDFileReader',
    'GetarFileReader',
    'GSDHOOMDFileReader', 'GSDHoomdFileReader']
