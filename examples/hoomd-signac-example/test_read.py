# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import signac

import garnett
import gsd
import gsd.fl
import gsd.hoomd


project = signac.get_project()

for job in project:
    print(job)
    with job:
        with garnett.read('dump.gsd') as traj:
            print(traj)

        with garnett.read('dump.dcd') as traj:
            print(traj)

        with garnett.read("dump.gsd", template='dump.pos') as traj:
            print(traj)

        with garnett.read("dump.gsd", template='init.xml') as traj:
            print(traj)
