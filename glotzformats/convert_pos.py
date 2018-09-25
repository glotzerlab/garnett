# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

"Convert glotzformats compatible trajectories to POS."
import os
import sys
import argparse
import logging

from tqdm import tqdm
from . import reader
from . import writer
from . import util


COLORS = [
    '#00274c',  # blue
    '#ffcb05',  # maize
    '#e41a1c',
    '#377eb8',
    '#4daf4a',
    '#984ea3',
    '#ff7f00',
]


pos_reader = reader.PosFileReader()
pos_writer = writer.PosFileWriter()


def _print_err(msg=None, *args):
    print(msg, *args, file=sys.stderr)


def _build_slice(slice_string):
    if slice_string.count(':') == 0: # dump the last n frames
        start, end, step = -int(slice_string), None, 1
    elif slice_string.count(':') == 1:
        start, end = [(None if e == '' else int(e))
                for e in slice_string.split(':')]
        step = None
    elif slice_string.count(':') == 2:
        start, end, step = [(None if e == '' else int(e))
                for e in slice_string.split(':')]
    return slice(start, end, step)


def center_ld(frame):
    from math import pi
    import freud
    import numpy as np
    ld = freud.density.LocalDensity(
        r_cut=2.5, volume=pi**3 * 4 / 3, diameter=1.0)
    b = frame.box
    box = freud.box.Box(Lx=b.Lx, Ly=b.Ly, Lz=b.Lz, xy=b.xy,
                        xz=b.xz, yz=b.yz, is2D=b.dimensions == 2)
    ld.compute(box, np.asarray(frame.positions, dtype=np.float32))
    density = ld.getDensity()
    i_max = np.argmax(density)
    frame.positions -= frame.positions[i_max]
    return frame


def center(frame):
    import numpy as np
    frame.positions -= np.mean(frame.positions, axis=0)
    return frame


def select_center(frame, s):
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


def wrap_into_box(frame):
    import numpy as np
    b = np.diag(frame.box.get_box_matrix())
    images = np.round(frame.positions / b)
    frame.positions -= images * b
    return frame


def color_by_type(frame):
    if len(frame.shapedef) > len(COLORS):
        raise RuntimeError("Number of types larger than color map!")
    for sd, color in zip(frame.shapedef, COLORS):
        frame.shapedef[sd].color = color
    return frame


def convert_pos(fn, outfile, args, template=None):
    frame_slice = _build_slice(args.frames)

    with util.read(fn) as traj:
        traj = traj[frame_slice]

        if args.center_by_density:
            traj = (center_ld(f) for f in traj)
        if args.select_center:
            traj = (select_center(f, args.select_center) for f in traj)
        if args.center:
            traj = (center(f) for f in traj)
        if args.wrap_into_box:
            traj = (wrap_into_box(f) for f in traj)
        if args.color_by_type:
            traj = (color_by_type(f) for f in traj)
        pos_writer.write(tqdm(traj), outfile)


def main():
    parser = argparse.ArgumentParser(
        description="Convert glotzformats compatible trajectories to POS.")
    parser.add_argument(
        'infile',
        type=str,
        nargs='+',
        help="One or more paths to glotzformats-compatible file(s).")
    parser.add_argument(
        '-t', '--template',
        type=str,
        help="Use a (POS) template frame.")
    parser.add_argument(
        '-o', '--out',
        type=str,
        help="Specify an output directory instead "
              "of dumping files to STDOUT.")
    parser.add_argument(
        '--force',
        action='store_true',
        help="Overwrite existing files. Use with caution.")
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
        '-w', '--wrap-into-box',
        action='store_true',
        help="Wrap all particles to fit into the box.")
    parser.add_argument(
        '-s', '--select-center',
        type=float,
        help="Select the the fraction of the box.")
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Increase output verbosity.")

    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING - 10 * int(args.verbose))

    try:
        if args.template:
            with open(args.template) as pos:
                template = pos_reader.read(pos)[0]
                template.load()
        else:
            template = None
        if not isinstance(args.infile, list):
            args.infile = [args.infile]
        if args.out:
            if not os.path.isdir(args.out):
                raise ValueError("'{}' must be a directory.".format(args.out))
            for fn in args.infile:
                fn_out = os.path.join(args.out, os.path.splitext(fn)[0] + '.pos')
                _print_err("Writing to '{}'...".format(fn_out))
                if not args.force and os.path.isfile(fn_out):
                    _print_err("File '{}' already exists, skipping.".format(fn_out))
                with open(fn_out, 'w') as outfile:
                    convert_pos(fn, outfile, args, template)
        else:
            for fn in args.infile:
                convert_pos(fn, sys.stdout, args, template)
    except Exception as error:
        _print_err('Error: {}'.format(error))
        sys.exit(1)
    else:
        sys.exit(0)
    finally:
        try:
            sys.stdout.close()
            sys.stderr.close()
        except Exception as error:
            pass
