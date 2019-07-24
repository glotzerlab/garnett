# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import signac

project = signac.init_project('lj-signac-example')

sps = [{
    'epsilon': 1.0,
    'sigma': 1.0,
    'kT': kT,
    'tau': 0.1,
    'r_cut': 3.0,
    }
    for kT in (0.1, 1.0, 1.5)]

for sp in sps:
    project.open_job(sp).init()
