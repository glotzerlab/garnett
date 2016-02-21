"""cif-file writer for the Glotzer Group, University of Michigan.

Author: Julia Dschemuchadse, Carl Simon Adorf

.. code::

    writer = CifFileWriter()
    with open('a_ciffile.pos', 'w', encoding='utf-8') as ciffile:
        writer.write(trajectory, ciffile)
"""

import io
import sys
import logging
import math

import numpy as np

from .ciffilereader import CIFFILE_FLOAT_DIGITS

logger = logging.getLogger(__name__)
PYTHON_2 = sys.version_info[0] == 2


def _num(x):
    "Round x if x is a floating point number."
    return int(x) if int(x) == x else round(x, CIFFILE_FLOAT_DIGITS)


def _determine_unitcell(box):
    lengths = np.array([box.Lx, box.Ly, box.Lz])  # a, b, c
    gamma = math.degrees(
        np.arccos(
            box.xy / math.sqrt(1 + box.xy**2)))
    beta = math.degrees(
        np.arccos(
            box.xz / math.sqrt(1 + box.xz**2 + box.yz**2)))
    alpha = math.degrees(
        np.arccos(
            (box.xy * box.xz + box.yz) /
            (math.sqrt(1 + box.xy**2) * math.sqrt(1 + box.xz**2 + box.yz**2))))
    angles = np.array([alpha, beta, gamma])
    return lengths, angles


class CifFileWriter(object):
    """Write cif-files from a trajectory instance."""

    def _write_frame(self, frame, file,
                     data, particle_type, particle_id, occupancy):
        def _write(msg='', end='\n'):
            if PYTHON_2:
                file.write(unicode(msg + end))  # noqa
            else:
                file.write(msg + end)
        unitcell_lengths, unitcell_angles = _determine_unitcell(frame.box)
        # write title
        _write("data_" + data)
        # _write("data_" + os.path.splitext(ciffilename)[0])

        # write unit cell parameters
        _write("_cell_length_a                 " +
               "{:12.7f}".format(unitcell_lengths[0]))
        _write("_cell_length_b                 " +
               "{:12.7f}".format(unitcell_lengths[1]))
        _write("_cell_length_c                 " +
               "{:12.7f}".format(unitcell_lengths[2]))
        _write("_cell_angle_alpha              " +
               "{:12.7f}".format(unitcell_angles[0]))
        _write("_cell_angle_beta               " +
               "{:12.7f}".format(unitcell_angles[1]))
        _write("_cell_angle_gamma              " +
               "{:12.7f}".format(unitcell_angles[2]))
        _write()

        # write symmetry - P1
        _write("_symmetry_space_group_name_H-M   " + "'P 1'")
        _write("_symmetry_Int_Tables_number      " + str(1))
        _write()

        # write header for particle positions
        _write("loop_")
        _write("_atom_site_label")
        _write("_atom_site_type_symbol")
        _write("_atom_site_occupancy")
        _write("_atom_site_fract_x")
        _write("_atom_site_fract_y")
        _write("_atom_site_fract_z")

        # write header particle positions
        for i, position in enumerate(frame.positions):
            _write("{pid}{pnum:04d} {ptype} {occ:3.2f} {position}".format(
                pid=particle_id,
                pnum=i + 1,
                ptype=particle_type,
                occ=occupancy,
                position=' '.join(('{:10.9f}'.format(p) for p in position))))
            # _write(
            #     particle_id + "{:04d}".format(i+1) + " " +
            #     particle_type + " " + \
            #     "{:3.2f}".format(occupancy) + " " +
            #     "{:10.9f}".format(position[0]) + " " +
            #     "{:10.9f}".format(position[1]) + " " +
            #     "{:10.9f}".format(position[2]) + " ")

    def write(self, trajectory, file=sys.stdout, data='simulationdata',
              particle_id='X', particle_type='X', occupancy=1.0):
        """Serialize a trajectory into cif-format and write it to file.

        :param trajectory: The trajectory to serialize
        :type trajectory: :class:`~glotzformats.trajectory.Trajectory`
        :param file: A file-like object."""
        for i, frame in enumerate(trajectory):
            self._write_frame(
                frame, file, data,
                particle_id, particle_type, occupancy)
            logger.debug("Wrote frame {}.".format(i + 1))
        logger.info("Wrote {} frames.".format(i + 1))

    def dump(self, trajectory):
        """Serialize trajectory into cif-format.

        :param trajectory: The trajectory to serialize.
        :type trajectory: :class:`~glotzformats.trajectory.Trajectory`
        :rtype: str"""
        f = io.StringIO()
        self.write(trajectory, f)
        return f.getvalue()
