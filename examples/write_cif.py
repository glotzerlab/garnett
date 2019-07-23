#!/usr/bin/env python

import argparse

import garnett

def main(args):
    pos_reader = garnett.reader.PosFileReader()
    cif_writer = garnett.writer.CifFileWriter()
    with open(args.posfile) as posfile:
        traj = pos_reader.read(posfile)
        cif_writer.write(traj)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Test the reading of pos- and writing of cif-files")
    parser.add_argument(
        'posfile',
        type=str,
        help="A pos-filename to read.")
    args = parser.parse_args()
    main(args)
