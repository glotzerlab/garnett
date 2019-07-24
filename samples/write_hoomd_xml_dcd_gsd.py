#!/usr/bin/env python

from hoomd import deprecated, run, dump, context, group

context.initialize()
system = deprecated.init.create_random(N=10, phi_p=0.05)
deprecated.dump.xml(filename='hoomd.xml', vis=True, group=group.all())
dump.gsd(filename='hoomd.gsd', period=1, overwrite=True, group=group.all())
dump.dcd(filename='dump.dcd', period=1, overwrite=True)
run(10)
