#!/usr/bin/env python

import logging

import garnett

logger = logging.getLogger(__name__)


def main(args):
    pos_writer = garnett.writer.PosFileWriter()
    xml_reader = garnett.reader.HoomdBlueXMLFileReader()
    dcd_reader = garnett.reader.DCDFileReader()

    with open(args.xmlfile) as xmlfile:
        frame = xml_reader.read(xmlfile)[0]
        with open(args.dcdfile) as dcdfile:
            traj = dcd_reader.read(dcdfile, frame)
            pos_writer.write(traj)
    return 0

if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Write pos-files from dcd-trajectory files.")
    parser.add_argument(
        'xmlfile',
        type=str,
        help="Filename of a hoomd-blue xml file.")
    parser.add_argument(
        'dcdfile',
        type=str,
        help="Filename of a dcd-file.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    sys.exit(main(args))
