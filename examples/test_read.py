#!/usr/bin/env python
import sys
import glob
import logging

import glotzformats as gf

try:
    import gtar
except ImportError:
    GTAR = False
else:
    GTAR = True
try:
    import gsd
except ImportError:
    GSD = False
else:
    GSD = True


def test_read(file, template=None):
    with gf.read(file, template=template) as traj:
        for frame in traj:
            frame.load()
            print(frame)


def main():
    if GTAR:
        for fn in glob.glob('../samples/*.tar'):
            test_read(fn)

    if GSD:
        for fn in glob.glob('../samples/*.gsd'):
            test_read(fn)

    for fn in glob.glob('../samples/*.dcd'):
        test_read(fn)

    for fn in glob.glob('../samples/*.xml'):
        test_read(fn)

    for fn in glob.glob('../samples/*.pos'):
        test_read(fn)

    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
