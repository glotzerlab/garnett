# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""CIF-file reader for the Glotzer Group, University of Michigan.

Authors: Matthew Spellings

.. code::

    reader = CifFileReader()
    with open('a_ciffile.cif', 'r', encoding='utf-8') as ciffile:
        traj = reader.read(ciffile)
"""

import logging
import re
import warnings
from collections import OrderedDict

import numpy as np

from .trajectory import _RawFrameData, Frame, Trajectory

# CifFile is from the pycifrw package
from CifFile import CifFile

from .errors import ParserError, ParserWarning

logger = logging.getLogger(__name__)

CIFFILE_FLOAT_DIGITS = 11

# invalid characters for symmetry expressions
REMOVE_NONNUM_REGEXP = re.compile(r'[^+\-*/0-9\.,\(\)xyz]+')

# (an integer or floating point number)/(an integer or floating point number)
PARSE_DIVISION_REGEXP = re.compile(r'(?P<num>\d+(\.(\d+)?)?)\s*/\s*(?P<denom>\d+(\.(\d+)?)?)')

# This regex matches _atom_site_label component 0 (but not component 1) of the
# definition here:
# https://www.iucr.org/__data/iucr/cif/standard/cifstd15.html
_ATOM_SITE_LABEL_COMPONENT_0 = re.compile(r'^(([^\s_0-9])|([0-9]*[\+\-]))*')


def _parse_division(match):
    """Helper function to substitute ratios in cif files, like '1/4', into
    fractions, like '0.25'."""
    return str(float(match.group('num'))/float(match.group('denom')))


def _parse_atom_site_label_to_type_name(label):
    """Matches _atom_site_label component 0.

    This regex matches component 0 (but not component 1) of the definition here:
    https://www.iucr.org/__data/iucr/cif/standard/cifstd15.html
    """
    m = re.search(_ATOM_SITE_LABEL_COMPONENT_0, label)
    return m.group()


class _RawCifFrameData(_RawFrameData):
    """Extend base class to support raw CIF coordinates"""

    def __init__(self):
        # Append the cif_coordinates to the dataset
        super(_RawCifFrameData, self).__init__()
        self.cif_coordinates = list()               # Nx3


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

    def _parse_box(self, parsed):
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
                         [0, ly, yz],
                         [0, 0, lz]])

    @property
    def cif_coordinates(self):
        "Nx3 matrix of exact coordinates provided in the CIF file."
        self.load()
        return self._frame_data.cif_coordinates

    @cif_coordinates.setter
    def cif_coordinates(self, value):
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("CIF coordinates can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("CIF coordinates being set must all be finite numbers.")
        elif not len(value.shape) == 2 or value.shape[1] != self.box.dimensions:
            raise ValueError("Input array must be of shape (N,{}) where N is the "
                             "number of particles.".format(self.box.dimensions))

        self.load()
        self._frame_data.cif_coordinates = value

    @staticmethod
    def _raw_frame_data_to_frame_data(raw_frame, dtype=None):
        """Extend parent function to also incorporate cif_coordinates"""
        ret = super(CifFileFrame, CifFileFrame)._raw_frame_data_to_frame_data(raw_frame, dtype)
        ret.cif_coordinates = np.asarray(raw_frame.cif_coordinates, dtype=dtype)
        assert len(ret.position) == len(ret.cif_coordinates)
        return ret

    def read(self):
        "Read the frame data from the stream."
        box_matrix = self._parse_box(self.parsed)

        fractions = np.array([(self._safer_float(x), self._safer_float(y), self._safer_float(z))
                              for (x, y, z) in zip(
            self.parsed['_atom_site_fract_x'], self.parsed['_atom_site_fract_y'], self.parsed['_atom_site_fract_z'])])

        if '_atom_site_type_symbol' in self.parsed:
            site_types = list(self.parsed['_atom_site_type_symbol'])
        elif '_atom_site_label' in self.parsed:
            site_types = [_parse_atom_site_label_to_type_name(label)
                          for label in self.parsed['_atom_site_label']]
        else:
            site_types = len(fractions)*[self.default_type]

        space_group_keys = ['_symmetry_equiv_pos_as_xyz', '_space_group_symop_operation_xyz']
        found_keys = [key for key in space_group_keys if key in self.parsed]

        unique_points = []
        type_strings = []

        if found_keys:
            key_to_use = found_keys[0]
            symmetry_ops = [PARSE_DIVISION_REGEXP.sub(
                            _parse_division, REMOVE_NONNUM_REGEXP.sub('', sym))
                            for sym in self.parsed[key_to_use]]

            replicated_fractions = []
            replicated_types = []
            for (type_name, (fx, fy, fz)) in zip(site_types, fractions):
                extra_fractions = [eval(sym, dict(x=fx, y=fy, z=fz)) for sym in symmetry_ops]
                replicated_fractions.extend(extra_fractions)
                replicated_types.extend(len(extra_fractions)*[type_name])
            # wrap back into the box
            replicated_fractions -= np.floor(replicated_fractions)
            replicated_fractions = dict(enumerate(np.array(replicated_fractions, dtype=np.float32)))

            bad_types = False
            # short of using scipy or freud, we just exhaustively search
            # for points near each point to find symmetry-induced duplicates
            while len(replicated_fractions):
                (ref_index, ref_point) = replicated_fractions.popitem()
                type_name = replicated_types[ref_index]

                # set of points that are ~equivalent to ref_point given a tolerance
                current_points = [ref_point]

                # find similar points and add them to the list
                for index in list(replicated_fractions):
                    # find nearest periodic image
                    delta = replicated_fractions[index] - ref_point
                    delta = ((delta + 0.5) % 1.0) - 0.5

                    if np.allclose(delta, 0, atol=self.tolerance):
                        del replicated_fractions[index]
                        current_points.append(ref_point + delta)

                        if replicated_types[ref_index] != replicated_types[index]:
                            bad_types = True
                            msg = ('Some distinct sites were merged into the same '
                                   'position, the types for this file are invalid.')
                            warnings.warn(msg, ParserWarning)

                type_strings.append(type_name)
                unique_points.append(np.mean(current_points, axis=0))
            unique_points = np.array(unique_points, dtype=np.float32)

            if bad_types:
                site_types = [self.default_type]
                type_strings = [self.default_type] * len(unique_points)
        else:
            unique_points = fractions
            type_strings = site_types

        # Remove duplicate site_types while preserving their order
        site_types = list(OrderedDict.fromkeys(site_types))

        # Convert type strings to typeid
        site_types_lookup = {key: index for index, key in enumerate(site_types)}
        typeid = [site_types_lookup[t] for t in type_strings]

        # Save the exact points
        cif_coordinates = unique_points.copy()

        # shift so that (0, 0, 0) in fractional coordinates goes to a
        # corner of the box, not the center of the box
        unique_points -= 0.5

        coordinates = np.sum(
            unique_points[:, np.newaxis, :]*box_matrix[np.newaxis, :, :], axis=2)

        raw_frame = _RawFrameData()
        raw_frame.box = box_matrix
        raw_frame.types = site_types
        raw_frame.typeid = typeid
        raw_frame.position = coordinates
        raw_frame.cif_coordinates = cif_coordinates
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
                traj = reader.read(ciffile)

        :param precision: The number of digits to
                          round floating-point values to.
        :type precision: int
        :param tolerance: Floating-point tolerance (in fractional
                          coordinates) of particle identity as symmetry
                          operations are applied.
        :type tolerance: float
    """

    def __init__(self, precision=None, tolerance=1e-3):
        """Initialize a cif-file reader."""
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
