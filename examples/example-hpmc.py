# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

import garnett
import hoomd
import hoomd.hpmc

# Vertices of a cube
cube_verts = [[-1, -1, -1], [-1, -1, 1], [-1, 1, 1], [-1, 1, -1],
              [1, -1, -1], [1, -1, 1], [1, 1, 1], [1, 1, -1]]

with hoomd.context.SimulationContext():
    box = hoomd.data.boxdim(L=10, dimensions=3)
    snapshot = hoomd.data.make_snapshot(N=4, box=box)
    snapshot.particles.position[:] = [
        [2, 0, 0],
        [4, 0, 0],
        [0, 4, 0],
        [0, 0, 4],
    ]
    system = hoomd.init.read_snapshot(snapshot)
    mc = hoomd.hpmc.integrate.convex_polyhedron(seed=452784, d=0.2, a=0.4)
    mc.shape_param.set('A', vertices=cube_verts)
    gsd_dump = hoomd.dump.gsd('cube.gsd', period=10, group=hoomd.group.all())
    gsd_dump.dump_state(mc)
    gsd_dump.dump_shape(mc)
    hoomd.run(1000)

    # Restore a snapshot from saved data
    with garnett.read('cube.gsd') as traj:
        snapshot2 = system.take_snapshot()
        traj[-1].to_hoomd_snapshot(snapshot2)


with hoomd.context.SimulationContext():
    # Create a HOOMD snapshot from a garnett Trajectory frame
    with garnett.read('cube.gsd') as traj:
        snapshot = traj[-1].to_hoomd_snapshot()
        system = hoomd.init.read_snapshot(snapshot)

    mc = hoomd.hpmc.integrate.convex_polyhedron(seed=452784, d=0.2, a=0.4)
    mc.shape_param.set('A', vertices=cube_verts)
    gsd_dump = hoomd.dump.gsd('cube.gsd', period=10, group=hoomd.group.all())
    gsd_dump.dump_state(mc)
    gsd_dump.dump_shape(mc)
    hoomd.run(1000)
