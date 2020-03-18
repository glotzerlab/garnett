# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
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

try:
    from .ciffilereader import CifFileReader
except ImportError:
    class CifFileReader(object):
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "CifFileReader requires the PyCifRW package.")


class PyDCDFileReader(_DCDFileReader):
    """Pure-python DCD-file reader for the Glotzer Group.

    This class is a pure python dcd-reader implementation
    which should only be used when the more efficient
    cythonized dcd-reader is not available or you want to
    work with non-standard file-like objects.

    .. seealso:: The API is identical to: :py:class:`~.DCDFileReader`"""
    pass


try:
    try:
        from . import dcdreader
    except ImportError:
        import dcdreader
except ImportError:

    class DCDFileReader(PyDCDFileReader):
        def __init__(self):
            warnings.warn("Failed to import dcdreader library. "
                          "Falling back to pure-python reader!")
            super(DCDFileReader, self).__init__()

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
    'GSDHOOMDFileReader', 'GSDHoomdFileReader',
    'CifFileReader']
