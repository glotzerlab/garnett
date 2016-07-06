class FileFormat(object):
    """A file-like object wrapper class.

    Used to present a file-like object as
    file with a defined format.

    :param file: The file-like object to wrap.
    """

    def __init__(self, file):
        self._file = file

    @property
    def file(self):
        "Return the underlying file-like object."
        return self._file

    @property
    def data(self):
        "Return the file data."
        return self.read()

    @property
    def mode(self):
        "Return the file mode."
        return self._file.mode

    def read(self, size=-1):
        """Read data from the file.

        :param size: Read size number of bytes/characters.
            Reads all remaining file data if -1.
        :type size: int
        """
        return self._file.read(size)

    def seek(self, offset):
        """Seek the file to the offset position.

        :param offset: The index of the byte/character to seek to.
        :type offset: int
        """
        return self._file.seek(offset)

    def tell(self):
        """Return the current offset position."""
        return self._file.tell()

    def __iter__(self):
        return iter(self._file)

    def close(self):
        """Close the file resource."""
        return self._file.close()


class XMLFile(FileFormat):
    "A file in Extensible Markup Language (XML) format."
    pass


class SnapshotFile(FileFormat):
    "A file containing single simulation snapshot."
    pass


class TrajectoryFile(FileFormat):
    "A file containing multiple simulation snapshots."
    pass


class HOOMDXMLSnapshotFile(XMLFile, SnapshotFile):
    "A file containing a simulation snapshot in HOOMD-XML schema."
    pass


class HoomdXMLSnapshotFile(HOOMDXMLSnapshotFile):
    """A file containing a simulation snapshot in HOOMD-XML schema.

    This class is depreceated, please use: HOOMDXMLSnapshotFile."""
    pass


class GSDTrajectoryFile(TrajectoryFile):
    """A file containing a GSD trajectory.

    See also: `<http://gsd.readthedocs.io>`_"""
    pass


class HOOMDGSDTrajectoryFile(GSDTrajectoryFile):
    """A file containing a GSD trajectory in HOOMD-schema.

    See also: `<http://gsd.readthedocs.io>`_"""
    pass


class PosTrajectoryFile(TrajectoryFile):
    "A file containing a simulation trajectory in POS-format."
    pass


class DCDTrajectoryFile(TrajectoryFile):
    "A file containing a simulation trajectory in DCD-format."
    pass


class GetarTrajectoryFile(TrajectoryFile):
    "A file containing a simulation trajectory in GeTar-format."
    pass


class CifTrajectoryFile(TrajectoryFile):
    "A file containing a simulation trajectory in CIF-format."
    pass


class LogFile(FileFormat):
    "A generic log-file."
    pass


class AnalysisLogFile(LogFile):
    "A generic analysis log file."
    pass


class SourceCodeFile(FileFormat):
    "A file containing source code."
    pass


class SourceCodeHeaderFile(FileFormat):
    "A file containing a source code header."
    pass


class ScriptFile(FileFormat):
    "A file containing a script."
    pass


class SimulationInputFile(FileFormat):
    "A file conatining a generic simulation input file."
    pass


class HOOMDInputFile(SimulationInputFile):
    "A file containing HOOMD-blue input script."
    pass


class HoomdInputFile(SimulationInputFile):
    """A file containing HOOMD-blue input script.

    This class is deprecated, please use: HOOMDInputFile."""
    pass


class PolyhedraVertices(dict):
    "A dict-mapping that contains polyhedra vertices definitions."
    pass
