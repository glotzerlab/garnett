import io
from itertools import chain

import numpy as np

from .posfilereader import POSFILE_FLOAT_DIGITS

def num(x):
    return int(x) if int(x) == x else round(x, POSFILE_FLOAT_DIGITS)

class PosFileWriter(object):
    """Write pos-files from a trajectory instance."""

    def write(self, trajectory, file):
        """Write trajectory to the file-like object file."""
        def _print(*args, **kwargs):
            return print(file=file, *args, **kwargs)
        for frame in trajectory:
            # data section
            if frame.data is not None:
                header_keys = list(frame.data.keys())
                _print('#[data] ', end='')
                _print(' '.join(header_keys))
                columns = list()
                for key in header_keys:
                    columns.append(frame.data[key])
                rows = np.array(columns).transpose()
                for row in rows:
                    _print(' '.join(row))
                _print('#[done]')
            # boxMatrix
            box_matrix = np.array(frame.box.get_box_matrix())
            _print('boxMatrix', end=' ')
            _print(' '.join((str(num(v)) for v in box_matrix.flatten())))
            # shape defs
            for name, definition in frame.shapedef.items():
                _print('def {} "{}"'.format(name, definition))
            for name, pos, rot in zip(frame.types, frame.positions, frame.orientations):
                _print(name, end=' ')
                _print(' '.join((str(num(v)) for v in chain(pos, rot))))
            _print('eof')
    
    def dump(self, trajectory):
        f = io.StringIO()
        self.write(trajectory, f)
        return f.getvalue()
