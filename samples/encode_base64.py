#!/usr/bin/env python
# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import sys
import argparse
import logging
import base64


logger = logging.getLogger(__name__)


def main(args):
    with open(args.binaryfile, 'rb') as file:
        print(base64.b64encode(file.read()))
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Dump a binary in base64 encoding.")
    parser.add_argument('binaryfile')
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING)
    sys.exit(main(args))
