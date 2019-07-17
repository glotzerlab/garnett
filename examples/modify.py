#!/usr/bin/env python

import logging
import numpy as np
import glotzformats as gf

logger = logging.getLogger(__name__)


def center(frame):
    frame.positions -= np.average(frame.positions, axis=0)
    return frame


def main(args):
    with gf.read(args.file) as traj:
        traj_centered = Trajectory((center(frame) for frame in traj))
        gf.write(traj_centered, args.file)

    return 0

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Read a file.")
    parser.add_argument(
        'file',
        type=str,
        help="Filename of a file.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sys.exit(main(args))
