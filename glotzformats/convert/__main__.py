# Copyright (c) 2018 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

"Converts between compatible trajectory formats."
from __future__ import print_function
import os
import sys
import argparse
import logging

from .. import util
from . import convert_file


def _print_err(msg=None, *args):
    print(msg, *args, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Convert between compatible trajectory formats.")
    parser.add_argument(
        'infile',
        type=str,
        help="Path to a compatible trajectory input file.")
    parser.add_argument(
        '-t', '--template',
        type=str,
        help="Use a template frame.")
    parser.add_argument(
        '-o', '--outfile',
        default=None,
        type=str,
        help="Specify an output file instead of dumping files to STDOUT.")
    parser.add_argument(
        '--outformat',
        default=None,
        type=str,
        help="Specify an output file format.")
    parser.add_argument(
        '--force',
        action='store_true',
        help="Overwrite existing output file.")
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
        '-s', '--select-center',
        type=float,
        help="Select a central fraction of the box.")
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Increase output verbosity.")

    argdict = vars(parser.parse_args())
    logging.basicConfig(level=logging.WARNING - 10 * int(argdict['verbose']))

    try:
        if argdict['template']:
            with util.read(argdict['template']) as template_traj:
                argdict['template'] = template_traj[0]
                argdict['template'].load()
        if argdict['outfile']:
            _print_err("Writing to '{}'...".format(argdict['outfile']))
            if not argdict['force'] and os.path.isfile(argdict['outfile']):
                _print_err("File '{}' already exists. To overwrite, use --force.".format(argdict['outfile']))
                sys.exit(0)
        for unused_key in ['force', 'verbose']:
            del argdict[unused_key]
        convert_file(**argdict)
    except Exception as error:
        _print_err('Error: {}'.format(error))
        sys.exit(1)
    else:
        sys.exit(0)
    finally:
        try:
            sys.stdout.close()
        except Exception as error:
            pass
        try:
            sys.stderr.close()
        except Exception as error:
            pass


if __name__ == '__main__':
    main()
