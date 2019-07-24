#!/usr/bin/env python

import logging

import glotzformats as gf

logger = logging.getLogger(__name__)


def main(args):
    with gf.read(args.infile) as traj:
        gf.write(traj, args.outfile)
    return 0


if __name__ == '__main__':

    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Translate between supported formats")
    parser.add_argument(
        'infile',
        type=str,
        help="Name of input file")
    parser.add_argument(
        'outfile',
        type=str,
        help="Name of a output file")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sys.exit(main(args))
