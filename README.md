# garnett

[![CircleCI](https://img.shields.io/circleci/project/github/glotzerlab/garnett/master.svg)](https://circleci.com/gh/glotzerlab/garnett)
[![RTD](https://img.shields.io/readthedocs/garnett.svg?style=flat)](https://garnett.readthedocs.io/)
[![Contributors](https://img.shields.io/github/contributors-anon/glotzerlab/garnett.svg?style=flat)](https://garnett.readthedocs.io/en/latest/credits.html)
[![License](https://img.shields.io/github/license/glotzerlab/garnett.svg)](https://github.com/glotzerlab/garnett/blob/master/LICENSE.txt)

## About

This is a collection of samples, parsers and writers for formats used in the Glotzer Group at the University of Michigan, Ann Arbor.

## Maintainers

* Luis Y. Rivera-Rivera, lyrivera@umich.edu
* Kelly Wang, kelwang@umich.edu
* Carl Simon Adorf, csadorf@umich.edu
* Bradley Dice, bdice@umich.edu

## Setup

To install this package with pip, execute:

```bash
pip install garnett --user
```

## Documentation

**The package's documentation is available at:** [https://garnett.readthedocs.io/](https://garnett.readthedocs.io/)

To build the documentation yourself using sphinx, execute within the repository:

```bash
cd doc
make html
open _build/html/index.html
```

## Quickstart

### Reading and writing

```python
import garnett

# Autodetects file format for a uniform trajectory API
with garnett.read('gsdfile.gsd') as traj:
    for frame in traj:
        pos = frame.position

# Simple conversion of trajectory formats
with garnett.read('posfile.pos') as traj:
    garnett.write(traj, 'gsdfile.gsd')
```

### Data access

Access individual frames by indexing or create subsets of trajectories with slicing:

```python
first_frame = traj[0]
last_frame = traj[-1]
nth_frame = traj[n]
# and so on

sub_trajectory = traj[i:j]
```

Access properties of trajectories:
```python
traj.load_arrays()
traj.box             # M
traj.N               # M
traj.types           # MxT
traj.type_shapes     # MxT
traj.typeid          # MxN
traj.position        # MxNx3
traj.orientation     # MxNx4
traj.velocity        # MxNx3
traj.mass            # MxN
traj.charge          # MxN
traj.diameter        # MxN
traj.moment_inertia  # MxNx3
traj.angmom          # MxNx4
traj.image           # MxNx3

# M is the number of frames
# T is the number of particle types in a frame
# N is the number of particles in a frame
```

Access properties of individual frames:
```python
frame = traj[i]
frame.box              # garnett.trajectory.Box object
frame.N                # scalar, number of particles
frame.types            # T, string names for each type
frame.type_shapes      # T, list of shapes for each type
frame.typeid           # N, type indices of each particle
frame.position         # Nx3
frame.orientation      # Nx4
frame.velocity         # Nx3
frame.mass             # N
frame.charge           # N
frame.diameter         # N
frame.moment_inertia   # Nx3
frame.angmom           # Nx4
frame.image            # Nx3
frame.data             # Dictionary of lists for each attribute
frame.data_key         # List of strings
```

All matrices are NumPy arrays.

## Example use with HOOMD-blue

See the [examples directory](https://github.com/glotzerlab/garnett/tree/master/examples) for additional examples.

```python
pos_reader = PosFileReader()
with open('cube.pos') as posfile:
    traj = pos_reader.read(posfile)

# Initialize from last frame
snapshot = traj[-1].to_hoomd_snapshot()
system = init.read_snapshot(snapshot)

# Restore last frame
snapshot = system.take_snapshot()
traj[-1].to_hoomd_snapshot(snapshot)
```

## Testing

To run all garnett tests, `ddt`, HOOMD-blue (`hoomd`), and `pycifrw` must be installed in the testing environments.

Execute the tests with:

```bash
python -m unittest discover tests
```
