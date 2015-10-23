import io
import sys
import logging
from itertools import chain

import numpy as np

from .posfilereader import POSFILE_FLOAT_DIGITS

logger = logging.getLogger(__name__)
PYTHON_3 = sys.version_info[0] == 3


def num(x):
    return int(x) if int(x) == x else round(x, POSFILE_FLOAT_DIGITS)


class PosFileWriter(object):
    """Write pos-files from a trajectory instance."""

    def write(self, trajectory, file):
        """Write trajectory to the file-like object file."""
        def _write(msg, end='\n'):
            if PYTHON_3:
                file.write(msg + end)
            else:
                file.write(unicode(msg + end))  # noqa
        for i, frame in enumerate(trajectory):
            # data section
            if frame.data is not None:
                header_keys = frame.data_keys
                _write('#[data] ', end='')
                _write(' '.join(header_keys))
                columns = list()
                for key in header_keys:
                    columns.append(frame.data[key])
                rows = np.array(columns).transpose()
                for row in rows:
                    _write(' '.join(row))
                _write('#[done]')
            # boxMatrix
            box_matrix = np.array(frame.box.get_box_matrix())
            _write('boxMatrix ', end='')
            _write(' '.join((str(num(v)) for v in box_matrix.flatten())))
            # shape defs
            for name, definition in frame.shapedef.items():
                _write('def {} "{}"'.format(name, definition))
            for name, pos, rot in zip(frame.types, frame.positions,
                                      frame.orientations):
                _write(name, end=' ')
                _write(' '.join((str(num(v)) for v in chain(pos, rot))))
            _write('eof')
            logger.debug("Wrote frame {}.".format(i + 1))
        logger.info("Wrote {} frames.".format(i + 1))

    def dump(self, trajectory):
        f = io.StringIO()
        self.write(trajectory, f)
        return f.getvalue()