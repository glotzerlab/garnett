# README

## About

This is a collection of samples, parsers and writers for formats used in the Glotzer Group at the University of Michigan, Ann Arbor.

## Maintainers

* Luis Y. Rivera-Rivera, lyrivera@umich.edu
* Kelly Wang, kelwang@umich.edu
* Carl Simon Adorf, csadorf@umich.edu
* Bradley Dice, bdice@umich.edu

## Setup

To install this package with pip, execute:

    pip install git+https://github.com/glotzerlab/glotzformats.git#egg=glotzformats --user

## Documentation

**The package's documentation is available at:** [http://glotzerlab.engin.umich.edu/glotzformats/](http://glotzerlab.engin.umich.edu/glotzformats/)

To build the documentation yourself using sphinx, execute within the repository:

    cd doc
    make html
    open _build/html/index.html

## Quickstart

### Reading and writing

``` python
import glotzformats as gf

# Autodetects file format for a uniform trajectory API
with gf.read('gsdfile.gsd') as traj:
    for frame in traj:
        pos = frame.positions

# Simple conversion of trajectory formats
with gf.read('posfile.pos') as traj:
    gf.write(traj, 'gsdfile.gsd')
```

### Data access

Access individual frames by indexing or create sub trajectories with slicing:
```python
first_frame = traj[0]
last_frame = traj[-1]
n_th_frame = traj[n]
# and so on

sub_trajectory = traj[i:j]
```

Access properties of trajectories:
```
traj.load_arrays()
traj.positions       # MxNx3
traj.orientations    # MxNx4
traj.velocities      # MxNx3
traj.mass            # MxN
traj.charge          # MxN
traj.diameter        # MxN
traj.moment_inertia  # MxNx3
traj.angmom          # MxNx4
traj.types           # MxN

# where M=len(traj) and N=max((len(f) for f in traj))
```

Access properties of individual frames:
```
frame = traj[i]
frame.box              # 3x3 matrix (not required to be upper-triangular)
frame.types            # N
frame.positions        # Nx3
frame.orientations     # Nx4
frame.velocities       # Nx3
frame.mass             # N
frame.charge           # N
frame.diameter         # N
frame.moment_inertia   # Nx3
frame.angmom           # Nx4
frame.data             # A dictionary of lists for each attribute
frame.data_key         # A list of strings
frame.shapedef         # A ordered dictionary of instances of ShapeDefinition
```
All matrices are `numpy` arrays.

## Example use with HOOMD-blue

See the [examples directory](https://github.com/glotzerlab/glotzformats/tree/master/examples) for additional examples.

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

To run all glotzformats tests, `ddt`, HOOMD-blue (`hoomd`), and `pycifrw` must be installed in the testing environments.

Execute the tests with

    python -m unittest discover tests
