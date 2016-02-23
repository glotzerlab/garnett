#!/usr/bin/env python

import hoomd_script as hoomd

system = hoomd.init.create_random(N=10, phi_p=0.05)
hoomd.dump.xml(filename='hoomd.xml', vis=True)
hoomd.dump.dcd(filename='dump.dcd', period=1)
hoomd.run(10)
