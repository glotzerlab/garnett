import signac

project = signac.get_project()

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
