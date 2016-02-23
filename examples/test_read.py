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


def test_read(file, reader):
    traj = reader.read(file)
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
    for fn in glob.glob('../samples/*.pos'):
        with open(fn) as file:
            test_read(file, glotzformats.reader.PosFileReader())
        with open(fn) as file:
            test_read(RestrictedFile(file), glotzformats.reader.PosFileReader())
    return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
