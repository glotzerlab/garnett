#!/usr/bin/env python

import sys
import numpy
from freud import trajectory
import newmanrs_mathutils as nmu
import math
import string
import argparse
import logging
from collections import OrderedDict

class FrameData:
    def __init__(self):
        self.position=None;
        self.quaternion=None;
        self.type=None;
        self.box=None;
        self.dataline=None;
        self.shapedef=None;

#Container class for the posfile reader to return
class PosData:
    def __init__(self):
        self.positions = [];   # (N,3) Numpy arrays, one per frame in list
        self.quaternions = []; # (N,4) Numpy arrays, one per frame in list
        self.types = [];       # List of lists;
        self.boxes = [];       # freud::trajectory::Box, one per frame in list
        self.data = [];   #
        self.shapedefs = [];   # List of list of string.  For each frame, so types can even change if need be.

    #Most of these are ideas
    def getFrameData(self,frameid):
        fd = FrameData();
        if frameid<len(self.positions):
            fd.position = self.positions[frameid];
            fd.quaternion = self.quaternions[frameid];
            fd.type = self.types[frameid];
            fd.box = self.boxes[frameid];
            fd.data = self.data[frameid];
            fd.shapedef = self.shapedefs[frameid];
        return fd;
    def print(self):
        print("Posdata Minimal Summary: ");
        print(" Number of frames is: {}".format(len(self.positions)));

#Reader for posfiles. Optional argument framelist takes a list of the desired
# frame indices as integer, zero based indexing, OR string 'lastframe' to use
# only the last frame
def readposfile(filename, framelist=None):

    posdata = PosData();

    #Determine number of frames, and the line locations at which these occur.

    eof  = []; #store lines of eof
    data = []; #store lines of #[data]
    done = []; #store lines of #[done]
    boxl= []; #store lines matching box.
    with open(filename,'r') as f:
        line_index = 0;
        for line in f:
            line=line.rstrip(); #Kill newlines
            if(line == 'eof'):
                eof.append(line_index);
            elif(line[0:7] == '#[data]'):
                data.append(line_index);
            elif(line[0:7] == '#[done]'):
                done.append(line_index);
            elif(line[0:3] == 'box'):
                boxl.append(line_index);
            line_index+=1;

        #Attempt a fix of a half-written frame or trailing data fields w/ no frame
        #if(len(data)!=0):
        #    while(max(data) > max(eof)):
        #        del lb[-1];

        #    #Assert that all frames have the same numbers of data, eof, done tags.
            #if len(eof) != len(data) or len(data) != len(done) or len(done) !=len(eof):
             #   raise Exception("Counts of eof, #[Data] and #[Done] unequal.  The input file may be corrupt");

        numframes = len(eof);

        #Now that lines are known...  and frames... time to attempt to parse I suppose.
        if framelist is None:
            framelist = range(numframes);
        elif framelist == 'lastframe':
            print("Number of frames is {}, but reading only last one".format(numframes));
            framelist = [numframes-1];

        #Okay, we know the start of each frame is #[data].  End is #[eof].
        
        #Per frame resets
        framedata = []; #Data, timestep, whatever metadata associated w/ frame        
        line_index = -1; #Increment to zero on loop entrance
        frame_index = 0;
        readmode = None;
        particle_index = 0;
        f.seek(0);  #Reset iterator.  Seriously?
        for line in f:  #Iterating the file...
            line_index+=1;
            line = line.rstrip();

            if not line:
                continue;

            if frame_index not in framelist:  #Don't bother reading
                if line == 'eof':
                    frame_index+=1;
                readmode = None;  #reset frame read mode
                continue;

            elif line == 'eof':
                frame_index+=1;
                readmode = None;

                #First do cleanup of prior frame
                #print(posdata.boxes);
                if isinstance(posdata.boxes[-1],numpy.ndarray): #Support for legacy incsim non-uppertriangular box matrices.  Ugggh (must rotate system).
                    [posdata.positions[-1],posdata.quaternions[-1],posdata.boxes[-1]] = rotateImproperTriclinic(posdata.positions[-1],posdata.quaternions[-1],posdata.boxes[-1]);

                #Parse framedata;
                #d = dict();
                d = OrderedDict();
                if framedata != []:
                    #print(framedata);
                    #print(framedata[1])
                    #print("\n\n\n\n\n\n\n");
                    #print(framedata[-3]);
                    #if frame_index > 4:
                    #    raise NotImplementedError
                    tmp0 = framedata[0].split();
                    tmp1 = framedata[-3].split(); #Uh, boxmatrix, other shit in here, [-3] is the last one, from 1 to -3 for all of the frames, but I only return the one most adjacent to frame, incase there are several.  Nest lists deeper I guess if there are more than one? (Not implemented);
                    for i in range(len(tmp1)):
                        try:
                            cast = int(tmp1[i]);
                        except ValueError:
                            cast = float(tmp1[i]);
                        d[tmp0[i+1]] = cast;
                    posdata.data.append(d);
                else:
                    posdata.data.append(None);

                #Reset per frame temp variables, etc.
                framedata = []; #Data, timestep, whatever metadata associated w/ frame
                #frame_index +=1;
                readmode = None;

            #Header stuff
            if(line[0:7] == '#[data]'):
                #print("found a data line");
                readmode = 'data';
            if readmode == 'data':
                framedata.append(line); #Either [#data], or line thereafter.
            if (line[0:3] =='box'):
                readmode = 'header';
                #print("found a header start line (done)");
                posdata.shapedefs.append([]);

            if readmode == 'header':  #either Done itself, or boxmatrix, or def something
                if 'boxMatrix' in line:
                    #print("Boxmatrix specified on line {} {}".format(line_index,line));
                    #TODO: PARSE BOXMATRIX, add to posdata
                    tmp = line.split();
                    boxv = []
                    for j in range(9):
                        boxv.append(float(tmp[j+1])); #boxMatrix 0 1, so +1;
                    v1 = (boxv[0],boxv[1],boxv[2])
                    v2 = (boxv[3],boxv[4],boxv[5])
                    v3 = (boxv[6],boxv[7],boxv[8])
                    box = numpy.ndarray( (3,3) );
                    box[0,:] = v1;
                    box[1,:] = v2;
                    box[2,:] = v3;
                    posdata.boxes.append(box);

                elif 'box' in line:
                    #print("Box specified on line {} {}".format(line_index,line));
                    tmp = line.split(); del tmp[0];
                    tmp = [float(t) for t in tmp]
                    posdata.boxes.append(trajectory.Box(tmp[-3],tmp[-2],tmp[-1]));
                elif ('def' in line) or ('poly3d' in line):
                    #print("Particle def identified on line {} {}".format(line_index,line));
                    posdata.shapedefs[-1].append(line);
                elif ('shape' in line):
                    posdata.shapedefs[-1].append(line);
                else:
                    if line[0:7]!='#[done]':
                        #print("An instance of particle data has been detected on line {} {}".format(line_index,line));
                        readmode = 'particledata';
                        #Calculate length of particle data, and allocate the numpy array!
                        N = eof[frame_index] - line_index;
                        #print("Guestimate of N is {}".format(N));
                        posdata.positions.append(numpy.zeros((N,3),dtype=numpy.float32));
                        posdata.quaternions.append(numpy.zeros((N,4),dtype=numpy.float32));
                        posdata.types.append([]);
                        particle_index = 0;

            #Particle data is most of the lines so check that case first.
            #Now that lines are known...  and frames... time to attempt to parse I suppose.
            if readmode == 'particledata':
                tmp = line.split();
                #print(tmp);
                if len(tmp) >= 8: #There's probably both type and quaternion data, maybe color. Whatever.
                    posdata.types[-1].append(tmp[0]);
                    quat = (tmp[-4], tmp[-3],tmp[-2],tmp[-1])
                    xyz = (tmp[-7],tmp[-6],tmp[-5])
                    posdata.positions[-1][particle_index]=xyz;
                    posdata.quaternions[-1][particle_index]=quat;
                    particle_index+=1;
                elif (len(tmp) == 7):
                    posdata.types[-1].append(None);
                    quat = (tmp[-4], tmp[-3],tmp[-2],tmp[-1])
                    xyz = (tmp[-7],tmp[-6],tmp[-5])
                    posdata.positions[-1][particle_index]=xyz;
                    posdata.quaternions[-1][particle_index]=quat;
                    particle_index+=1;
                elif (len(tmp) == 5):  #Type color X Y Z 
                    posdata.types[-1].append(tmp[0]);
                    quat = (1,0,0,0)
                    xyz = (tmp[-3],tmp[-2],tmp[-1])
                    posdata.positions[-1][particle_index]=xyz;
                    posdata.quaternions[-1][particle_index]=quat;
                    particle_index+=1;
                elif (len(tmp) == 4):
                    if 'def' in posdata.shapedefs[-1][-1]:  #Then types must be defined
                        posdata.types[-1].append(tmp[0]);
                    quat = (1,0,0,0)
                    xyz = (tmp[-3],tmp[-2],tmp[-1])
                    posdata.positions[-1][particle_index]=xyz;
                    posdata.quaternions[-1][particle_index]=quat;
                    particle_index+=1;
                elif (len(tmp) == 3):
                    posdata.types[-1].append(None);
                    quat = (1,0,0,0);
                    xyz = (tmp[-3],tmp[-2],tmp[-1])
                    posdata.positions[-1][particle_index]=xyz;
                    posdata.quaternions[-1][particle_index]=quat;
                    particle_index+=1;
                elif len(tmp) == 6 and "sphere" in line:
                    posdata.types[-1].append(None);
                    quat = (1,0,0,0);
                    xyz = (tmp[-3],tmp[-2],tmp[-1])
                    posdata.positions[-1][particle_index]=xyz;
                    posdata.quaternions[-1][particle_index]=quat;
                    particle_index+=1;

                else:
                    raise ValueError("In readmode particle data, confused on line={}".format(line));
                    #raise NotImplementedError("Particle xyz quat or whatever parser not written yet if <8 columns");
    return posdata;

# Note that for files not outputted by HPMC, a full rotation from an arbitrary triclinic dense box matrix
# to upper triangular may be required.  Therefore, we do so.  Here.  Always.
def rotateImproperTriclinic(positions,quats,boxMatrix):
    
    # boxMatrix contains an arbitrarily oriented right-handed box matrix.
    N = positions.shape[0];
    v = numpy.ndarray(shape=(3,3));
    v[0] = boxMatrix[:,0]
    v[1] = boxMatrix[:,1]
    v[2] = boxMatrix[:,2]
    Lx = numpy.sqrt(numpy.dot(v[0], v[0]))
    a2x = numpy.dot(v[0], v[1]) / Lx
    Ly = numpy.sqrt(numpy.dot(v[1],v[1]) - a2x*a2x)
    xy = a2x / Ly
    v0xv1 = numpy.cross(v[0], v[1])
    v0xv1mag = numpy.sqrt(numpy.dot(v0xv1, v0xv1))
    Lz = numpy.dot(v[2], v0xv1) / v0xv1mag
    a3x = numpy.dot(v[0], v[2]) / Lx
    xz = a3x / Lz
    yz = (numpy.dot(v[1],v[2]) - a2x*a3x) / (Ly*Lz)


    #Shove into freudbox
    box = trajectory.Box(Lx,Ly,Lz,xy,xz,yz);

    #Begin long calculation to transform box and system orientation
    # from injavis/incsim compatible pos format to HOOMD upper
    # triangular coordinates.
    
    #Unit Vectors
    e1=numpy.array([1.0,0,0]);
    e2=numpy.array([0,1.0,0]);
    e3=numpy.array([0,0,1.0]);
    
    #Need to transform box and particle orientations for HOOMD.
    #We need v[0] to point in direction of x, and v[1] in xy plane.  
    qbox0toe1 = nmu.quaternionRotateVectorOntoVector(v[0],e1);

    #Rotate box so v[0] = (val,0,0).
    v[0] = nmu.rotateVector(v[0],qbox0toe1)
    v[1] = nmu.rotateVector(v[1],qbox0toe1)
    v[2] = nmu.rotateVector(v[2],qbox0toe1)

    #Rotate system about x axis, so that v[1] is in xy plane.
    theta_yz = math.atan2(v[1][2],v[1][1])  #Angle between v[1] and ex, in the YZ plane
    q_y1intoxy = nmu.quaternionAxisAngle(e1,-theta_yz);

    v[0] = nmu.rotateVector(v[0],q_y1intoxy)
    v[1] = nmu.rotateVector(v[1],q_y1intoxy)
    v[2] = nmu.rotateVector(v[2],q_y1intoxy)

    #Rotate the particles by the appropriate quaternion composition of the rotations on the box
    qboth = nmu.quaternionMultiply(q_y1intoxy,qbox0toe1);
    for i in range(N):
        positions[i]=nmu.rotateVector(positions[i],qboth)
        quats[i] = nmu.quaternionMultiply(qboth,quats[i])

    return [positions, quats, box]

class ShapeDefinitionPoly3DData:
    def __init__(self):	
        self.type = None;   #Particle type
        self.N =None;
        self.vertices = None;
        self.color = None;
        self.stringdef = None; #Original shape definition line as string
        self.stringdefnocolor = None; #Without hex color.

    def print(self):
        self.printContents();

    def printContents(self):
        print("Printing ShapeDefinitionPoly3DData Contents");
        print(" Original unparsed string: {}".format(self.stringdef));
        print(" Definition string w/o color: {}".format(self.stringdefnocolor));
        print(" Particle Type is {}".format(self.type));
        print(" Particle Color is {}".format(self.color));
        print(" Number of Vertices is {}".format(self.N));
        print(" Vertices are {}".format(self.vertices)); 

def parsePoly3DShapeDefinition(sd):
    if not 'poly3d' in sd:
        raise ValueError("Definition does not declare poly3d.  Uh oh");
    data = ShapeDefinitionPoly3DData();
    tmp = sd.split();
    tmp = [t.strip('"') for t in tmp]; #Strip "
    tmp = [t.rstrip() for t in tmp];  #hopefully strips \n
    data.stringdef = sd;

    if 'shape' in sd:
        data.type = None;  #No type will be defined.
        data.N = int(tmp[2]);
        if len(tmp) == 3*data.N +3:
            data.color = None;
        elif len(tmp) == 3*data.N +4:
            data.color = tmp[-1];
        else:
            raise ValueError("Unexpected pos file length.  NOoooooooo");
        data.vertices = numpy.zeros(shape=(data.N,3),dtype=numpy.float32);
        for v in range(data.N):
            data.vertices[v] = ( float(tmp[3*v+3]), float(tmp[3*v+4]),float(tmp[3*v+5]) )
    elif 'def' in sd:
        data.type = tmp[1];
        data.N = int(tmp[3]);
        if len(tmp) == 3*data.N +4:
            data.color = None;
        elif len(tmp) == 3*data.N +5:
            data.color = tmp[-1];
        else:
            raise ValueError("Unexpected pos file length, apparently, in: {}".format(sd));
        data.vertices = numpy.zeros(shape=(data.N,3),dtype=numpy.float32);
        for v in range(data.N):
            data.vertices[v] = ( float(tmp[3*v+4]), float(tmp[3*v+5]),float(tmp[3*v+6]) ) 
    else:
        raise ValueError("Neither 'def' nor 'shape' appears in shapedef.  Wat");

    if data.color is not None:
        tmp2 = sd.rstrip().split();
        #del tmp2[-1]  #Commenting out, seems unpythonic
        tmp2.pop();  #At least object oriented?!
        reconstruct = '';
        for item in tmp2:
            reconstruct+=item+' ';
        reconstruct+='"'
        data.stringdefnocolor = reconstruct;
    else:
        data.stringdefnocolor = data.stringdef;
    return data;

#Example usage.
if __name__ == "__main__":
    readexample = False;
    parsepoly3dexample = True;
    if(readexample):
        #Read
        a = readposfile('test.pos','lastframe');
        #Get frame 0
        print(a.positions[0])
        print(a.quaternions[0]);
        print(a.types[0])
        print(a.boxes[0]);
        print(a.data[0]);
        print(a.shapedefs[0]);
        #Get all frames
        f4 = a.getFrameData(0);
        print(f4.data);
    if(parsepoly3dexample):
        sd = 'shape "poly3d 6 1 0 0 -1 0 0 0 1 0 0 -1 0 0 0 1 0 0 -1"'	
        data = parsePoly3DShapeDefinition(sd);
        data.printContents();

        sd = 'shape "poly3d 6 1 0 0 -1 0 0 0 1 0 0 -1 0 0 0 1 0 0 -1 ff0000ff"'	
        data = parsePoly3DShapeDefinition(sd);
        data.printContents();

        sd = 'def alpha "poly3d 6 1 0 0 -1 0 0 0 1 0 0 -1 0 0 0 1 0 0 -1"'	
        data = parsePoly3DShapeDefinition(sd);
        data.printContents();

        sd = 'def omega "poly3d 6 1 0 0 -1 0 0 0 1 0 0 -1 0 0 0 1 0 0 -1 ff00ff00"'	
        data = parsePoly3DShapeDefinition(sd);
        data.printContents();

def main(args):
    return readposfile(args.posfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = "POS-file reader by Carl Simon Adorf.")
    parser.add_argument(
        'posfile',
        type = str,
        help = "The path to the pos-file to read.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(main(args))
