# Demonstration with the cube example
from __future__ import print_function
from __future__ import division
from hoomd_script import *
from hoomd_plugins import hpmc

import numpy as np

from glotzformats.reader import PosFileReader
from glotzformats.writer import PosFileWriter

context.initialize()
system = init.read_xml('cube.xml')

mc = hpmc.integrate.convex_polyhedron(seed=452784, d=0.2, a=0.4)
mc.shape_param.set('A', vertices=[(0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, 0.5)])
pos = dump.pos(filename='cube.pos', period=10)
mc.setup_pos_writer(pos)
run(1000)

pos_reader = PosFileReader()
with open('cube.pos') as posfile:
    traj = pos_reader.read(posfile)

# Restore the snapshot
sn2 = system.take_snapshot()
traj[-1].copyto_snapshot(sn2)

# Initializing from pos-file
init.reset()
with open('cube.pos') as posfile:
    traj = pos_reader.read(posfile)
snapshot = traj[-1].make_snapshot()
system = init.read_snapshot(snapshot)
