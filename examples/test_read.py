#!/usr/bin/env python
import sys
import os
import glob
import logging

import glotzformats

try:
    import gtar
except ImportError:
    GTAR = False
else:
    GTAR = True
try:
    import mdtraj
except ImportError:
    MDTRAJ=False
else:
    MDTRAJ=True


def test_read(file, reader, *args, **kwargs):
    traj = reader.read(file, *args, **kwargs)
    for frame in traj:
        frame.load()
        print(frame)


class RestrictedFile(glotzformats.formats.FileFormat):
    pass
    

def main():
    if GTAR:
        for fn in glob.glob('../samples/*.tar'):
            with open(fn, 'rb') as file:
                test_read(file, glotzformats.reader.GetarFileReader())
    if MDTRAJ:
        for fn in glob.glob('../samples/*.dcd'):
            with open(glob.glob('../samples/*.xml')[0]) as xmlfile:
                frame = glotzformats.reader.HoomdBlueXMLFileReader().read(xmlfile)[0]
                with open(fn, 'rb') as file:
                    test_read(file, glotzformats.reader.DCDReader(), frame)
    for fn in glob.glob('../samples/*.xml'):
        with open(fn) as file:
            test_read(file, glotzformats.reader.HoomdBlueXMLFileReader())
    for fn in glob.glob('../samples/*.pos'):
        with open(fn) as file:
            test_read(file, glotzformats.reader.PosFileReader())
        with open(fn) as file:
            test_read(RestrictedFile(file), glotzformats.reader.PosFileReader())
    return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
