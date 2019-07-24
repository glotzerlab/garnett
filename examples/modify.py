#!/usr/bin/env python

import logging
import numpy as np

from garnett.reader import PosFileReader
from garnett.writer import PosFileWriter
from garnett.trajectory import Trajectory

logger = logging.getLogger(__name__)


def center(frame):
    frame.positions -= np.average(frame.positions, axis=0)
    return frame


def main(args):
    with garnett.read(args.infile) as traj:
        traj_centered = Trajectory((center(frame) for frame in traj))
        garnett.write(traj_centered, args.outfile)

    return 0


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Read a file.")
    parser.add_argument(
        'infile',
        type=str,
        help="Filename of the file to read.")
    parser.add_argument(
        'outfile',
        type=str,
        help="Filename of the file to write to.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sys.exit(main(args))
