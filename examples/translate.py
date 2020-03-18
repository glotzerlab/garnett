#!/usr/bin/env python
# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

import garnett
import logging

logger = logging.getLogger(__name__)


def main(args):
    with garnett.read(args.infile) as traj:
        garnett.write(traj, args.outfile)
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
