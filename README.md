# README

## About

This is a collection of samples, parsers and writers for formats used in the Glotzer Group at the University of Michigan, Ann Arbor.

## Authors

* Carl Simon Adorf, csadorf@umich.edu (Maintainer)
* Richmond Newmann, newmanrs@umich.edu

## Setup

To install this package with pip, execute:

    pip install git+https://$USER@bitbucket.org/glotzer/glotz-formats.git#egg=glotzformats --user

## Documentation

**The package's documentation is available at:** [http://glotzerlab.engin.umich.edu/glotzformats/](http://glotzerlab.engin.umich.edu/glotzformats/)

To build the documentation yourself using sphinx, execute within the repository:

    cd doc
    make html
    open _build/html/index.html

## Quickstart

### Reading and writing

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

### Data access

Access individual frames by indexing or create sub trajectories with slicing:
```
#!python
first_frame = traj[0]
last_frame = traj[-1]
n_th_frame = traj[n]
# and so on

sub_trajectory = traj[i:j]
```

Access properties of trajectories:
```
traj.load_arrays()
traj.positions      # MxNx3
traj.orientations   # MxNx4
traj.types          # MxNx1

# where M=len(traj) and N=max((len(f) for f in traj))
```

Access properties of individual frames:
```
frame = traj[i]
frame.box              # 3x3 matrix (not required to be upper-triangular)
frame.types            # Nx1
frame.positions        # Nx3
frame.orientations     # NX4
frame.data             # A dictionary of lists for each attribute
frame.data_key         # A list of strings
frame.shapedef         # A ordered dictionary of instances of ShapeDefinition
```
All matrices are `numpy` arrays.

## Example use with HOOMD-blue

Click [here](https://bitbucket.org/glotzer/glotz-formats/src/master/examples/) for more examples.

```
#!python
pos_reader = PosFileReader()
with open('cube.pos') as posfile:
    traj = pos_reader.read(posfile)

# Initialize from last frame
snapshot = traj[-1].make_snapshot()
system = init.read_snapshot(snapshot)

# Restore last frame
snapshot = system.take_snapshot()
traj[-1].copyto_snapshot(snapshot)

```

## Testing

Ideally, you test with HOOMD-blue installed in your testing environment.

In this case, execute tests with

    hoomd -m unittest discover tests

otherwise, run tests with:

    python -m unittest discover tests

or:

    nosetest
