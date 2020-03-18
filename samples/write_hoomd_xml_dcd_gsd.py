#!/usr/bin/env python
# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

from hoomd import deprecated, run, dump, context, group

context.initialize()
system = deprecated.init.create_random(N=10, phi_p=0.05)
deprecated.dump.xml(filename='hoomd.xml', vis=True, group=group.all())
dump.gsd(filename='hoomd.gsd', period=1, overwrite=True, group=group.all())
dump.dcd(filename='dump.dcd', period=1, overwrite=True)
run(10)
