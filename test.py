import glotzformats as gf

r = gf.reader.GSDHOOMDFileReader()
with open('../dump.gsd', 'rb') as f:
    t = r.read(f)
    print(dir(t[30]))
    # print(t[30].orientations)
    print(t[30].angmoms)
    
