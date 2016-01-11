#!/usr/bin/env python

import sys
import os
import io
import logging
import tarfile

import glotzformats

FN_SAMPLE_ARCHIVE = 'samples.tar.gz'


def test_read_pos(posfile):
    pos_reader = glotzformats.reader.PosFileReader()
    traj = pos_reader.read(posfile)
    for frame in traj:
        print(frame)


def main():
    with tarfile.open(FN_SAMPLE_ARCHIVE) as tar:
        for member in tar.getmembers():
            fd = io.StringIO(tar.extractfile(member).read().decode())
            base, ext = os.path.splitext(member.name)
            if ext == '.pos':
                test_read_pos(fd)
    return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(main())
