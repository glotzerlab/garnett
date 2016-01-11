#!/usr/bin/env python

import sys
import logging

from glotzformats.reader import PosFileReader
from glotzformats.writer import PosFileWriter

logger = logging.getLogger(__name__)


def main(args):
    pos_reader = PosFileReader()
    pos_writer = PosFileWriter()
    with open(args.posfile) as posfile:
        traj = pos_reader.read(posfile)
        for i, frame in enumerate(traj):
            print(i, frame)
        pos_writer.write(traj, sys.stdout)
    return 0

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description="Read a pos-file.")
    parser.add_argument(
        'posfile',
        type=str,
        help="Filename of a pos-file.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sys.exit(main(args))
