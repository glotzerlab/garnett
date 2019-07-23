#!/usr/bin/env python

import logging

from garnett.reader import PosFileReader
from garnett.writer import PosFileWriter

logger = logging.getLogger(__name__)


def main(args):
    pos_reader = PosFileReader()
    pos_writer = PosFileWriter()
    with open(args.posfile) as posfile:
        pos_writer.write(pos_reader.read(posfile))
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
