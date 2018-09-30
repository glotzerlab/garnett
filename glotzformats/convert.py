# Copyright (c) 2018 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

"Converts between compatible trajectory formats."
from __future__ import print_function
import os
import sys
import argparse
import logging

from tqdm import tqdm
from . import util


DEFAULT_COLORS = [
    '#00274c',  # blue
    '#ffcb05',  # maize
    '#e41a1c',
    '#377eb8',
    '#4daf4a',
    '#984ea3',
    '#ff7f00',
]


def _print_err(msg=None, *args):
    print(msg, *args, file=sys.stderr)


def _build_slice(slice_string):
    if isinstance(slice_string, slice):
        return slice_string
    if slice_string.count(':') == 0:  # dump the last n frames
        start, end, step = -int(slice_string), None, 1
    elif slice_string.count(':') == 1:
        start, end = [(None if e == '' else int(e)) for e in slice_string.split(':')]
        step = None
    elif slice_string.count(':') == 2:
        start, end, step = [(None if e == '' else int(e)) for e in slice_string.split(':')]
    return slice(start, end, step)


def _center_ld(frame):
    import freud
    import numpy as np
    ld = freud.density.LocalDensity(r_cut=2.5, volume=np.pi**3 * 4 / 3, diameter=1.0)
    ld.compute(frame.box, frame.positions)
    i_max = np.argmax(ld.density)
    frame.positions -= frame.positions[i_max]
    return frame


def _center(frame):
    import numpy as np
    frame.positions -= np.mean(frame.positions, axis=0)
    return frame


def _select_center(frame, s):
    import numpy as np
    b = np.diag(frame.box.get_box_matrix())
    b_ = b * s
    select = (np.abs(frame.positions) < b_ / 2).all(axis=1)
    frame.types = [t for i, t in enumerate(frame.types) if select[i]]
    frame.positions = frame.positions[select]
    frame.orientations = frame.orientations[select]
    frame.box.Lx = b_[0]
    frame.box.Ly = b_[1]
    frame.box.Lz = b_[2]
    return frame


def _color_by_type(frame, colors=DEFAULT_COLORS):
    if len(frame.shapedef) > len(colors):
        raise RuntimeError("Number of types larger than color map!")
    for sd, color in zip(frame.shapedef, colors):
        frame.shapedef[sd].color = color
    return frame


def convert_file(infile, outfile=None, outformat=None, template=None, frames=':',
                 center_by_density=False, select_center=False, center=False,
                 color_by_type=False, colors=DEFAULT_COLORS, no_progress=False):
    """Convert trajectory files from one format to another.

    :param infile: Path to input trajectory.
    :type infile: path
    :param outfile: Path to output trajectory (default: `None`, prints to `sys.stdout`)
    :type outfile: path
    :param outfmt: File format, one of 'gsd', 'gtar', 'pos', 'cif'
        (default: `None`, autodetected from outfile with fallback to 'pos')
    :type outfmt: string
    :param template: Template frame for reading input file (default: `None`).
    :type template: Frame
    :param frames: Slice for selecting frames (default: `':'`, all frames are kept).
    :type frames: Slice-like string or slice.
    :param center_by_density: Whether to center by local density (requires freud, default: `False`).
    :type center_by_density: bool
    :param select_center: Crops box to keep only this fraction from the center (default: `False`, no cropping).
    :type select_center: float
    :param center: Whether to center the box on the center of particle positions (default: `False`).
    :type center: bool
    :param color_by_type: Whether to assign particles colors by their types (default: `False`).
    :type color_by_type: bool
    :param colors: An optional color map for coloring particle types (default: Michigan-inspired color map).
    :type colors: List of hexadecimal strings like `['#00274c', ...]`.
    :param no_progress: Whether to disable the progress bar from tqdm (default: `False`).
    :type no_progress: bool
    """

    with util.read(infile) as traj:
        traj = traj[_build_slice(frames)]

        if center_by_density:
            traj = (_center_ld(f) for f in traj)
        if select_center:
            traj = (_select_center(f, select_center) for f in traj)
        if center:
            traj = (_center(f) for f in traj)
        if color_by_type:
            traj = (_color_by_type(f, colors) for f in traj)

        if outfile is None:
            outfile = sys.stdout
        if outformat is None:
            try:
                outformat = util.detect_format(outfile)
            except Exception as e:
                outformat = 'pos'
        util.write(tqdm(traj, disable=no_progress, unit=' frames'), outfile, fmt=outformat)


def main():
    parser = argparse.ArgumentParser(
        description="Convert between compatible trajectory formats.")
    parser.add_argument(
        'infile',
        type=str,
        help="Path to a compatible trajectory input file.")
    parser.add_argument(
        '-t', '--template',
        type=str,
        help="Use a template frame.")
    parser.add_argument(
        '-o', '--outfile',
        default=None,
        type=str,
        help="Specify an output file instead of dumping files to STDOUT.")
    parser.add_argument(
        '--outformat',
        default=None,
        type=str,
        help="Specify an output file format.")
    parser.add_argument(
        '--force',
        action='store_true',
        help="Overwrite existing output file.")
    parser.add_argument(
        '-f', '--frames',
        default=':',
        help='Select which frames to dump. A single number n dumps the final \
        n frames; otherwise, python slice-like behavior is assumed.')
    parser.add_argument(
        '--color-by-type',
        action='store_true',
        help="Color particles by type.")
    parser.add_argument(
        '-c', '--center',
        action='store_true',
        help="Center particle positions.")
    parser.add_argument(
        '-d', '--center-by-density',
        action='store_true',
        help="Center particles by local density.")
    parser.add_argument(
        '-s', '--select-center',
        type=float,
        help="Select a central fraction of the box.")
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Increase output verbosity.")

    argdict = vars(parser.parse_args())
    logging.basicConfig(level=logging.WARNING - 10 * int(argdict['verbose']))

    try:
        if argdict['template']:
            with util.read(argdict['template']) as template_traj:
                argdict['template'] = template_traj[0]
                argdict['template'].load()
        if argdict['outfile']:
            _print_err("Writing to '{}'...".format(argdict['outfile']))
            if not argdict['force'] and os.path.isfile(argdict['outfile']):
                _print_err("File '{}' already exists. To overwrite, use --force.".format(argdict['outfile']))
                sys.exit(0)
        for unused_key in ['force', 'verbose']:
            del argdict[unused_key]
        convert_file(**argdict)
    except Exception as error:
        _print_err('Error: {}'.format(error))
        sys.exit(1)
    else:
        sys.exit(0)
    finally:
        try:
            sys.stdout.close()
        except Exception as error:
            pass
        try:
            sys.stderr.close()
        except Exception as error:
            pass
