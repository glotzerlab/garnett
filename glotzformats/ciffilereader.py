"""POS-file reader for the Glotzer Group, University of Michigan.

Authors: Matthew Spellings

.. code::

    reader = CifFileReader()
    with open('a_ciffile.cif', 'r', encoding='utf-8') as ciffile:
        return reader.read(ciffile)
"""

import collections
import logging
import re
import warnings

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory

from CifFile import CifFile

from .errors import ParserError, ParserWarning

logger = logging.getLogger(__name__)

CIFFILE_FLOAT_DIGITS = 11


# invalid characters for symmetry expressions
REMOVE_NONNUM_REGEXP = re.compile(r'[^+\-*/0-9\.,\(\)xyz]+')

# (an integer or floating point number)/(an integer or floating point number)
PARSE_DIVISION_REGEXP = re.compile(r'(?P<num>\d+(\.(\d+)?)?)\s*/\s*(?P<denom>\d+(\.(\d+)?)?)')

def _parse_division(match):
    """Helper function to substitute ratios in cif files, like '1/4', into
    fractions, like '0.25'."""
    return str(float(match.group('num'))/float(match.group('denom')))


class CifFileFrame(Frame):

    def __init__(self, parsed, precision, default_type, tolerance=1e-5):
        self.parsed = parsed
        self.precision = precision
        self.default_type = default_type
        self.tolerance = tolerance
        super(CifFileFrame, self).__init__()

    def _num(self, x):
        if isinstance(x, int):
            return x
        else:
            return round(float(x), self.precision)

    def _safer_float(self, s):
        """Only takes the first component of a string as a number, in case
        some notion of imprecision is specified e.g. 1.3141(2)"""
        idx = s.rfind('(')
        return self._num(s[:idx]) if idx >= 0 else self._num(s)

    def _parseBox(self, parsed):
        (a, b, c) = [self._safer_float(parsed['_cell_length_{}'.format(name)])
                     for name in ['a', 'b', 'c']]
        (alpha, beta, gamma) = [self._safer_float(parsed['_cell_angle_{}'.format(name)])
                                for name in ['alpha', 'beta', 'gamma']]
        alpha *= np.pi/180
        beta *= np.pi/180
        gamma *= np.pi/180

        # http://lammps.sandia.gov/doc/Section_howto.html#howto-12
        # in this block, use the definitions lammps uses
        # (lammps xy == hoomd xy*ly, etc)
        lx = a
        xy = b*np.cos(gamma)
        xz = c*np.cos(beta)
        ly = np.sqrt(b**2 - xy**2)
        yz = (b*c*np.cos(alpha) - xy*xz)/ly
        lz = np.sqrt(c**2 - xz**2 - yz**2)

        return np.array([[lx, xy, xz],
                         [ 0, ly, yz],
                         [ 0,  0, lz]])

    def read(self):
        "Read the frame data from the stream."
        box_matrix = self._parseBox(self.parsed)

        fractions = np.array([(self._safer_float(x), self._safer_float(y), self._safer_float(z))
                              for (x, y, z) in zip(
            self.parsed['_atom_site_fract_x'], self.parsed['_atom_site_fract_y'], self.parsed['_atom_site_fract_z'])])

        if '_symmetry_equiv_pos_as_xyz' in self.parsed:
            symmetry_ops = [PARSE_DIVISION_REGEXP.sub(
                            _parse_division, REMOVE_NONNUM_REGEXP.sub('', sym))
                            for sym in self.parsed['_symmetry_equiv_pos_as_xyz']]

            replicated_fractions = []
            replicated_types = []
            for (typ, (fx, fy, fz)) in zip(self.parsed['_atom_site_label'], fractions):
                extra_fractions = [eval(sym, dict(x=fx, y=fy, z=fz)) for sym in symmetry_ops]
                replicated_fractions.extend(extra_fractions)
                replicated_types.extend(len(extra_fractions)*[typ])
            # wrap back into the box
            replicated_fractions -= np.floor(replicated_fractions)
            replicated_fractions = dict(enumerate(np.array(replicated_fractions, dtype=np.float32)))

            unique_points = []
            types = []
            bad_types = False
            # short of using scipy or freud, we just exhaustively search
            # for points near each point to find symmetry-induced duplicates
            while len(replicated_fractions):
                (ref_index, ref_point) = replicated_fractions.popitem()
                types.append(replicated_types[ref_index])

                # set of points that are ~equivalent to ref_point given a tolerance
                current_points = [ref_point]

                # find similar points and add them to the list
                for index in list(replicated_fractions):
                    if np.allclose(replicated_fractions[index], ref_point, self.tolerance):
                        current_points.append(replicated_fractions.pop(index))

                        if replicated_types[ref_index] != replicated_types[index]:
                            bad_types = True
                            msg = ('Some distinct sites were merged into the same '
                                   'position, the types for this file are invalid.')
                            warnings.warn(msg, ParserWarning)

                unique_points.append(np.mean(current_points, axis=0))
            unique_points = np.array(unique_points, dtype=np.float32)

            if bad_types:
                unique_types = len(unique_points)*[self.default_type]
            else:
                unique_types = types
        else:
            unique_points = fractions
            if '_atom_site_label' in self.parsed:
                unique_types = self.parsed['_atom_site_label']
            else:
                unique_types = len(unique_points)*[self.default_type]

        # shift so that (0, 0, 0) in fractional coordinates goes to a
        # corner of the box, not the center of the box
        unique_points -= 0.5

        coordinates = np.sum(
            unique_points[:, np.newaxis, :]*box_matrix[np.newaxis, :, :], axis=2)

        raw_frame = _RawFrameData()
        raw_frame.box = box_matrix
        raw_frame.types = unique_types
        raw_frame.positions = coordinates
        raw_frame.velocities = np.zeros_like(coordinates)
        raw_frame.orientations = np.zeros((coordinates.shape[0], 4), dtype=np.float32)
        return raw_frame

    def __str__(self):
        return "CifFileFrame(parsed={}, precision={})".format(
            self.parsed, self.precision)


class CifFileReader(object):
    """CIF-file reader for the Glotzer Group, University of Michigan.

        Requires the PyCifRW package to parse CIF files.

        Authors: Matthew Spellings

        .. code::

            reader = CifFileReader()
            with open('a_ciffile.cif', 'r') as ciffile:
                return reader.read(ciffile)

        :param precision: The number of digits to
                          round floating-point values to.
        :type precision: int
    """

    def __init__(self, precision=None, tolerance=1e-5):
        """Initialize a cif-file reader.

        :param precision: The number of digits to
                          round floating-point values to.
        :param tolerance: Floating-point tolerance of particle
                          identity as symmetry operations are applied
        :type precision: int
        :type tolerance: float
        """
        self._precision = precision or CIFFILE_FLOAT_DIGITS
        self._tolerance = tolerance

    def _scan(self, parsed_file, keys, default_type):
        return (CifFileFrame(parsed_file[key], self._precision, default_type,
                             self._tolerance) for key in keys)

    def read(self, stream, default_type='A'):
        """Read text stream and return a trajectory instance.

        :param stream: The stream, which contains the ciffile.
        :type stream: A file-like textstream.
        :param default_type: The default particle type for
                             ciffile dialects without type definition.
        :type default_type: str
        """
        parsed_file = CifFile(stream)
        keys = list(sorted(parsed_file.keys()))

        # Index the stream
        frames = list(self._scan(parsed_file, keys, default_type))
        if len(frames) == 0:
            raise ParserError("Did not read a single complete frame.")
        logger.info("Read {} frames.".format(len(frames)))
        return Trajectory(frames)