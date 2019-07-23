import signac

import garnett
import gsd
import gsd.fl
import gsd.hoomd


project = signac.get_project()

for job in project.find_jobs():
    print(job)
    with job:
        with open('dump.gsd', 'rb') as file:
            traj = garnett.reader.GSDHOOMDFileReader().read(file)
            print(traj)

        f = gsd.fl.GSDFile('dump.gsd', 'rb')
        t = gsd.hoomd.HOOMDTrajectory(f)


        with open('dump.pos') as posfile:
            top_traj = garnett.reader.PosFileReader().read(posfile)
            print(top_traj)

            with open('dump.dcd', 'rb') as dcdfile:
                traj = garnett.reader.DCDFileReader().read(dcdfile, top_traj[0])
                traj.load()
                print(traj)

            with open('dump.gsd', 'rb') as gsdfile:
                traj = garnett.reader.GSDHOOMDFileReader().read(gsdfile, top_traj[0])
                traj.load()
                print(traj)


        with open('init.xml') as xmlfile:
            top_traj = garnett.reader.HOOMDXMLFileReader().read(xmlfile)
            print(top_traj)

            with open('dump.dcd', 'rb') as dcdfile:
                traj = garnett.reader.DCDFileReader().read(dcdfile, top_traj[0])
                traj.load()
                print(traj)

            with open('dump.gsd', 'rb') as gsdfile:
                traj = garnett.reader.GSDHOOMDFileReader().read(gsdfile, top_traj[0])
                traj.load()
                print(traj)
