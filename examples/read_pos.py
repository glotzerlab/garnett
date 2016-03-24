#!/usr/bin/env python

import logging

from glotzformats.reader import PosFileReader

logger = logging.getLogger(__name__)


def main(args):
    pos_reader = PosFileReader()
    with open(args.posfile) as posfile:
        traj = pos_reader.read(posfile)
        for i, frame in enumerate(traj):
            print(i, frame)
    return 0

if __name__ == '__main__':
    import sys
    import argparse
    parser = argparse.ArgumentParser(
        description="Read a pos-file.")
    parser.add_argument(
        'posfile',
        type=str,
        help="Filename of a pos-file.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(main(args))
