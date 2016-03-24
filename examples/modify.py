#!/usr/bin/env python

import logging

import numpy as np

from glotzformats.reader import PosFileReader
from glotzformats.writer import PosFileWriter
from glotzformats.trajectory import Trajectory

logger = logging.getLogger(__name__)


def center(frame):
    frame.positions -= np.average(frame.positions, axis=0)
    return frame


def main(args):
    pos_reader = PosFileReader()
    pos_writer = PosFileWriter()
    with open(args.posfile) as posfile:
        traj = pos_reader.read(posfile)
        traj_centered = Trajectory((center(frame) for frame in traj))
        pos_writer.write(traj_centered)

        # or short:
        # pos_writer.write(
        #    Trajectory((center(f) for f in pos_.read.read(posfile))))
    return 0

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Read a pos-file.")
    parser.add_argument(
        'posfile',
        type=str,
        help="Filename of a pos-file.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sys.exit(main(args))
