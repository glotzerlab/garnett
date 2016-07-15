import signac

import glotzformats as gf
import gsd
import gsd.fl
import gsd.hoomd


project = signac.get_project()

for job in project.find_jobs():
    print(job)
    with job:
        with open('dump.gsd', 'rb') as file:
            traj = gf.reader.GSDHOOMDFileReader().read(file)
            print(traj)

        f = gsd.fl.GSDFile('dump.gsd', 'rb')
        t = gsd.hoomd.HOOMDTrajectory(f)


        with open('dump.pos') as posfile:
            top_traj = gf.reader.PosFileReader().read(posfile)
            print(top_traj)

            with open('dump.dcd', 'rb') as dcdfile:
                traj = gf.reader.DCDFileReader().read(dcdfile, top_traj[0])
                traj.load()
                print(traj)

            with open('dump.gsd', 'rb') as gsdfile:
                traj = gf.reader.GSDHOOMDFileReader().read(gsdfile, top_traj[0])
                traj.load()
                print(traj)
                

        with open('init.xml') as xmlfile:
            top_traj = gf.reader.HOOMDXMLFileReader().read(xmlfile)
            print(top_traj)

            with open('dump.dcd', 'rb') as dcdfile:
                traj = gf.reader.DCDFileReader().read(dcdfile, top_traj[0])
                traj.load()
                print(traj)

            with open('dump.gsd', 'rb') as gsdfile:
                traj = gf.reader.GSDHOOMDFileReader().read(gsdfile, top_traj[0])
                traj.load()
                print(traj)
