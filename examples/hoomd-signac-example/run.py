#!/usr/bin/env python
import os
import numpy as np
import warnings
from contextlib import contextmanager

import signac
import hoomd
import hoomd.deprecated
from hoomd import md

hoomd.context.initialize()

@contextmanager
def restart_pos(filename):
    fn_tmp = filename + '.tmp'
    if os.path.isfile(filename):
        os.rename(filename, fn_tmp)
    yield
    with open(fn_tmp, 'a') as tmp:
        with open(filename) as file:
            tmp.write(file.read())
    os.rename(fn_tmp, filename)

project = signac.get_project()


for job in project:
    with job:
        sp = job.statepoint()
        if not job.isfile('init.gsd'):
            print("Initialize system.")
            with hoomd.context.SimulationContext():
                system = hoomd.init.create_lattice(
                    unitcell=hoomd.lattice.sc(a=2.0), n=[4,5,5])
                snapshot = system.take_snapshot()
                np.copyto(
                    snapshot.particles.velocity,
                    np.random.random(snapshot.particles.velocity.shape))

            with hoomd.context.SimulationContext():
                hoomd.init.read_snapshot(snapshot)
                hoomd.dump.gsd(filename='init.gsd', period=None, group=hoomd.group.all())
                hoomd.deprecated.dump.xml(hoomd.group.all(), filename='init.xml', vis=True)

        with hoomd.context.SimulationContext():
            hoomd.init.read_gsd(filename='init.gsd', restart='restart.gsd')

            print("tstep", hoomd.get_step())

            lj = md.pair.lj(r_cut=sp['r_cut'], nlist=md.nlist.cell())
            lj.pair_coeff.set('A', 'A', epsilon=sp['epsilon'], sigma=sp['sigma'])

            group = hoomd.group.all()

            md.integrate.mode_standard(dt=0.01)
            md.integrate.nvt(group, kT=sp['kT'], tau=sp['tau'])

            gsd_restart = hoomd.dump.gsd(filename='restart.gsd', group=group, truncate=True, period=100)
            hoomd.dump.gsd(filename='dump.gsd', group=group, truncate=False, period=100)
            hoomd.dump.dcd(filename='dump.dcd', group=group, period=100)
            with restart_pos('dump.pos'):
                hoomd.deprecated.dump.pos(filename='dump.pos', period=100)
                hoomd.run_upto(1000)
            gsd_restart.write_restart()
