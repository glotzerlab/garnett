#!/usr/bin/env python
# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

import numpy as np
import gtar

N = 100

with gtar.GTAR('libgetar_sample.tar', 'w') as traj:
    traj.writePath('frames/0/position.f32.ind', np.random.rand(N, 3))
    traj.writePath('frames/0/orientation.f32.ind', np.random.rand(N, 4))
    traj.writePath('type.u32.ind', N//2*[0] + (N - N//2)*[1])
    traj.writePath('type_names.json', '["type1", "type2"]')
