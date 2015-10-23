class FileFormat(object):

    def __init__(self, file_object):
        self._file_object = file_object

    @property
    def data(self):
        return self.read()

    def read(self):
        return self._file_object.read()


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
