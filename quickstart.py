from glotzformats.reader import PosFileReader

pos_reader = PosFileReader()
with open('posfile.pos') as posfile:
    traj = pos_reader.read(posfile)
