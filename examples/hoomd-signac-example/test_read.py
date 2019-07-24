import signac
import glotzformats as gf

project = signac.get_project()

for job in project:
    print(job)
    with job:
        with gf.read('dump.gsd') as traj:
            print(traj)

        with gf.read('dump.dcd') as traj:
            print(traj)

        with gf.read("dump.gsd", template='dump.pos') as traj:
            print(traj)

        with gf.read("dump.gsd", template='init.xml') as traj:
            print(traj)
