# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
# Demonstration with the cube example
from __future__ import print_function
from __future__ import division
from hoomd_script import *
from hoomd_plugins import hpmc

import numpy as np

from garnett.reader import PosFileReader
from garnett.writer import PosFileWriter

context.initialize()

import os
try:
    system = init.read_xml('cube.xml')
except RuntimeError:
    snapshot = data.make_snapshot(N=4, box=data.boxdim(L=10, dimensions=3))
    np.copyto(snapshot.particles.position, np.array([
            [2, 0, 0],
            [4, 0, 0],
            [0, 4, 0],
            [0, 0, 4],
        ]))
    system = init.read_snapshot(snapshot)
    dump.xml('cube.xml', all=True)

mc = hpmc.integrate.convex_polyhedron(seed=452784, d=0.2, a=0.4)
mc.shape_param.set('A', vertices=[(0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, 0.5)])
pos = dump.pos(filename='cube.pos', period=10)
mc.setup_pos_writer(pos)
run(1000)

pos_reader = PosFileReader()
with open('cube.pos') as posfile:
    traj = pos_reader.read(posfile)

# Restore a snapshot
sn2 = system.take_snapshot()
traj[-1].to_hoomd_snapshot(sn2)

# New system
init.reset()
with open('cube.pos') as posfile:
    traj = pos_reader.read(posfile)
snapshot = traj[-1].to_hoomd_snapshot()
system = init.read_snapshot(snapshot)

mc = hpmc.integrate.convex_polyhedron(seed=452784, d=0.2, a=0.4)
mc.shape_param.set('A', vertices=[(0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, 0.5)])
pos = dump.pos(filename='cube.pos', period=10)
mc.setup_pos_writer(pos)
run(1000)
