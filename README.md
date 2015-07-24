# README

## About

This is a collection of samples, parsers and writers for formats used in the Glotzer Group at the University of Michigan, Ann Arbor.

## Authors

* Carl Simon Adorf, csadorf@umich.edu (Maintainer)
* Richmond Newmann, newmanrs@umich.edu

## Setup

To install this package with pip, execute:

    pip install git+https://$USER@bitbucket.org/glotzer/glotz-formats.git#egg=glotzformats --user

## Quickstart

```
#!python
from glotzformats.reader import PosFileReader
from glotzformats.writer import PosFileWriter

pos_reader = PosFileReader()
with open('posfile.pos') as posfile:
    traj = pos_reader.read(posfile)

pos_writer = PosFileWriter()
with open('posfile2.pos', 'w') as posfile:
    pos_writer.write(traj, posfile)
```

## Example use with HPMC

```
#!python
pos_reader = PosFileReader()
with open('cube.pos') as posfile:
    traj = pos_reader.read(posfile)

# Initializing from last frame
snapshot = traj[-1].make_snapshot()
system = init.read_snapshot(snapshot)

# Restore last frame from pos-file
sn2 = system.take_snapshot()
traj[-1].copyto_snapshot(sn2)

```

## Testing

Ideally, you test with hoomd and hpmc in the testing environment.

In this case, execute tests with

    hoomd -m unittest discover tests

otherwise, run tests with:

    python -m unittest discover tests

or:

    nosetest
