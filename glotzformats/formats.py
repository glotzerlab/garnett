class FileFormat(object):

    def __init__(self, file):
        self._file = file

    @property
    def file(self):
        return self._file

    @property
    def data(self):
        return self.read()

    @property
    def mode(self):
        return self._file.mode

    def read(self, size=-1):
        return self._file.read(size)

    def seek(self, offset):
        return self._file.seek(offset)

    def tell(self):
        return self._file.tell()

    def __iter__(self):
        return iter(self._file)

    def close(self):
        return self._file.close()


class XMLFile(FileFormat):
    pass


class SnapshotFile(FileFormat):
    pass


class TrajectoryFile(FileFormat):
    pass


class HoomdXMLSnapshotFile(XMLFile, SnapshotFile):
    pass


class PosTrajectoryFile(TrajectoryFile):
    pass


class DCDTrajectoryFile(TrajectoryFile):
    pass


class GetarTrajectoryFile(TrajectoryFile):
    pass


class CifTrajectoryFile(TrajectoryFile):
    pass


class LogFile(FileFormat):
    pass


class AnalysisLogFile(LogFile):
    pass


class SourceCodeFile(FileFormat):
    pass


class SourceCodeHeaderFile(FileFormat):
    pass


class ScriptFile(FileFormat):
    pass


class SimulationInputFile(FileFormat):
    pass


class HoomdInputFile(SimulationInputFile):
    pass


class PolyhedraVertices(dict):
    pass
