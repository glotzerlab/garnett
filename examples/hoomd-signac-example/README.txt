# README for the HOOMD/signac example

## About

This example initializes a simple signac project and then
executes a number of HOOMD-blue simulations, which dump
simulation trajectories in various formats.
These trajectories are then read using garnett readers
in various combinations.

# Prerequisites

You need to install HOOMD-blue and signac to run these examples.

You can install these packages for example with:
```
conda install -c conda-forge hoomd signac
```

## How to run the example

Execute the scripts in the following order
```
$ python init.py
$ python run.py
$ python test_read.py
```
