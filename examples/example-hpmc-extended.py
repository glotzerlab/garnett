# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

# Demonstration with the cube example
import garnett
import hoomd
import hoomd.hpmc
import numpy as np

hoomd.context.initialize()

try:
    system = hoomd.init.read_xml('cube.xml')
except RuntimeError:
    snapshot = hoomd.data.make_snapshot(
        N=4, box=hoomd.data.boxdim(L=10, dimensions=3))
    np.copyto(snapshot.particles.position, np.array([
        [2, 0, 0],
        [4, 0, 0],
        [0, 4, 0],
        [0, 0, 4],
    ]))
    system = hoomd.init.read_snapshot(snapshot)
    hoomd.dump.xml('cube.xml', all=True)

mc = hoomd.hpmc.integrate.convex_polyhedron(seed=452784, d=0.2, a=0.4)
mc.shape_param.set('A', vertices=[
    (0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, 0.5)])
pos = hoomd.dump.pos(filename='cube.pos', period=10)
mc.setup_pos_writer(pos)
hoomd.run(1000)


with garnett.read('cube.pos') as traj:
    # Restore a snapshot
    sn2 = system.take_snapshot()
    traj[-1].to_hoomd_snapshot(sn2)

# New system
hoomd.init.reset()

with garnett.read('cube.pos') as traj:
    snapshot = traj[-1].to_hoomd_snapshot()
    system = hoomd.init.read_snapshot(snapshot)

mc = hoomd.hpmc.integrate.convex_polyhedron(seed=452784, d=0.2, a=0.4)
mc.shape_param.set('A', vertices=[
    (0.5, 0.5, 0.5), (0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, 0.5)])
pos = hoomd.dump.pos(filename='cube.pos', period=10)
mc.setup_pos_writer(pos)
hoomd.run(1000)
