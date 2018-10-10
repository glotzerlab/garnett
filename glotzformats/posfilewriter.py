"""POS-file writer for the Glotzer Group, University of Michigan.

Author: Carl Simon Adorf

.. code::

    writer = PosFileWriter()
    with open('a_posfile.pos', 'w', encoding='utf-8') as posfile:
        writer.write(trajectory, posfile)
"""

import io
import sys
import logging
import warnings
import math
from itertools import chain

import numpy as np

from .posfilereader import POSFILE_FLOAT_DIGITS
from .shapes import SphereShape, ArrowShape
import rowan


logger = logging.getLogger(__name__)
PYTHON_2 = sys.version_info[0] == 2

DEFAULT_SHAPE_DEFINITION = SphereShape(1.0, color='005984FF')


def _num(x):
    "Round x if x is a floating point number."
    return int(x) if int(x) == x else round(float(x), POSFILE_FLOAT_DIGITS)


class PosFileWriter(object):
    """POS-file writer for the Glotzer Group, University of Michigan.

    Author: Carl Simon Adorf

    .. code::

        writer = PosFileWriter()
        with open('a_posfile.pos', 'w', encoding='utf-8') as posfile:
            writer.write(trajectory, posfile)

    :param rotate: Rotate the system into the view rotation instead of adding
        it to the metadata with the 'rotation' keyword.
    :type rotate: bool
    """
    def __init__(self, rotate=False):
        self._rotate = rotate
        if self._rotate:
            warnings.warn(
                "Rotating the system with a view rotation leads to significant "
                "numerical precision loss!")

    def write(self, trajectory, file=sys.stdout):
        """Serialize a trajectory into pos-format and write it to file.

        :param trajectory: The trajectory to serialize
        :type trajectory: :class:`~glotzformats.trajectory.Trajectory`
        :param file: A file-like object."""
        def _write(msg, end='\n'):
            if PYTHON_2:
                file.write(unicode(msg + end))  # noqa
            else:
                file.write(msg + end)
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

            # boxMatrix and rotation
            box_matrix = np.array(frame.box.get_box_matrix())
            if self._rotate and frame.view_rotation is not None:
                for i in range(3):
                    box_matrix[:, i] = rowan.rotate(frame.view_rotation, box_matrix[:, i])

            if frame.view_rotation is not None and not self._rotate:
                angles = rowan.to_euler(frame.view_rotation, axis_type='extrinsic', convention='xyz') * 180 / math.pi
                _write('rotation ' + ' '.join((str(_num(_)) for _ in angles)))

            _write('boxMatrix ', end='')
            _write(' '.join((str(_num(v)) for v in box_matrix.flatten())))

            # shape defs
            required = set(frame.types).intersection(
                set(frame.shapedef.keys()))
            not_defined = set(frame.types).difference(
                set(frame.shapedef.keys()))
            for name in required:
                _write('def {} "{}"'.format(name, frame.shapedef[name]))
            for name in not_defined:
                logger.info(
                    "No shape defined for '{}'. "
                    "Using fallback definition.".format(name))
                _write('def {} "{}"'.format(name, DEFAULT_SHAPE_DEFINITION))
            for name, pos, rot in zip(frame.types, frame.positions,
                                      frame.orientations):

                _write(name, end=' ')
                shapedef = frame.shapedef.get(name, DEFAULT_SHAPE_DEFINITION)

                if self._rotate and frame.view_rotation is not None:
                    pos = rowan.rotate(frame.view_rotation, pos)
                    rot = rowan.multiply(frame.view_rotation, rot)

                if isinstance(shapedef, SphereShape):
                    _write(' '.join((str(_num(v)) for v in pos)))
                elif isinstance(shapedef, ArrowShape):
                    # The arrow shape actually has two position vectors of
                    # three elements since it has start.{x,y,z} and end.{x,y,z}.
                    # That is, "rot" is not an accurate variable name, since it
                    # does not represent a quaternion.
                    _write(' '.join((str(_num(v)) for v in chain(pos, rot[:3]))))
                else:
                    _write(' '.join((str(_num(v)) for v in chain(pos, rot))))
            _write('eof')
            logger.debug("Wrote frame {}.".format(i + 1))
        logger.info("Wrote {} frames.".format(i + 1))

    def dump(self, trajectory):
        """Serialize trajectory into pos-format.

        :param trajectory: The trajectory to serialize.
        :type trajectory: :class:`~glotzformats.trajectory.Trajectory`
        :rtype: str"""
        f = io.StringIO()
        self.write(trajectory, f)
        return f.getvalue()
