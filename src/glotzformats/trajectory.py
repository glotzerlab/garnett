import logging
import math
import collections

import numpy as np

from . import math_utils as mu

logger = logging.getLogger(__name__)

class Box(object):
    """A triclinical box class."""
    
    def __init__(self, Lx, Ly, Lz, xy=0.0, xz=0.0, yz=0.0, dimensions=3):
        self.Lx=Lx
        self.Ly=Ly
        self.Lz=Lz
        self.xy=xy
        self.xz=xz
        self.yz=yz
        self.dimensions=dimensions

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

class FrameData(object):
    """One FrameData instance manages the data of one frame in a trajectory."""

    def __init__(self):
        self.box = None                             # Box object
        self.types = None
        self.positions = None                       # Nx3 matrix
        self.orientations = None                    # Nx3 matrix
        self.data = None                            # so far not parsed
        self.shapedef = collections.OrderedDict()   # A ordered dictionary for str

    def __len__(self):
        return len(self.types)

class RawFrameData(object):
    """Class to capture unprocessed frame data during parsing."""

    def __init__(self):
        self.box = None                                 # 3x3 matrix (not required to be upper-triangular)
        self.types = list()
        self.positions = list()
        self.orientations = list()
        self.data = None
        self.shapedef = collections.OrderedDict()

def rotate_improper_triclinic(positions, orientations, box_matrix, dimensions=3):
    """Transform the box matrix into a upper-triangular matrix and rotate the system accordingly."""
    N = positions.shape[0]
    v = np.zeros((3,3))
    # source: http://codeblue.umich.edu/hoomd-blue/doc/page_box.html
    v[0] = box_matrix[:,0]
    v[1] = box_matrix[:,1]
    v[2] = box_matrix[:,2]
    Lx = np.sqrt(np.dot(v[0], v[0]))
    a2x = np.dot(v[0], v[1]) / Lx
    Ly = np.sqrt(np.dot(v[1],v[1]) - a2x*a2x)
    xy = a2x / Ly
    v0xv1 = np.cross(v[0], v[1])
    v0xv1mag = np.sqrt(np.dot(v0xv1, v0xv1))
    Lz = np.dot(v[2], v0xv1) / v0xv1mag
    a3x = np.dot(v[0], v[2]) / Lx
    xz = a3x / Lz
    yz = (np.dot(v[1],v[2]) - a2x*a3x) / (Ly*Lz)
    # end of source
    assert 1 < dimensions <= 3
    if dimensions == 2:
        assert Lz==1
        assert xz == yz == 0
    box = Box(Lx=Lx,Ly=Ly,Lz=Lz,xy=xy,xz=xz,yz=yz,dimensions=dimensions)

    # unit vectors
    e1 = np.array((1.0, 0, 0))
    e2 = np.array((0, 1.0, 0))
    e3 = np.array((0, 0, 1.0))

    # Transforming particle orientations
    # Rotation of v[0] into direction x, and v[1] into xy plane
    # Rotation of system, so that v[0] is aligned with x and v[1] in xy-plane
    qbox0toe1 = mu.quaternionRotateVectorOntoVector(v[0], e1)

    # Rotate v[0] into x-direction
    v[0] = mu.rotateVector(v[0],qbox0toe1)
    v[1] = mu.rotateVector(v[1],qbox0toe1)
    v[2] = mu.rotateVector(v[2],qbox0toe1)

    # Rotate system about x-axis, so that v[1] is in xy-plane
    theta_yz = math.atan2(v[1][2],v[1][1])  #Angle between v[1] and ex, in the YZ plane
    q_y1intoxy = mu.quaternionAxisAngle(e1,-theta_yz);

    v[0] = mu.rotateVector(v[0],q_y1intoxy)
    v[1] = mu.rotateVector(v[1],q_y1intoxy)
    v[2] = mu.rotateVector(v[2],q_y1intoxy)

    # Rotate system particles by the appropriate quaternion composition of the orientations on the system
    qboth = mu.quaternionMultiply(q_y1intoxy,qbox0toe1);
    for i in range(N):
        positions[i]=mu.rotateVector(positions[i],qboth)
        orientations[i] = mu.quaternionMultiply(qboth, orientations[i])
    return positions, orientations, box

def raw_frame_to_frame(raw_frame):
    """Generate a frame object from a raw frame object."""
    N = len(raw_frame.types)
    ret = FrameData()
    # the box
    positions = np.array(raw_frame.positions)
    orientations = np.array(raw_frame.orientations)
    ret.positions, ret.orientations, ret.box = rotate_improper_triclinic(positions, orientations, raw_frame.box)
    ret.shapedef = raw_frame.shapedef
    ret.types = raw_frame.types
    assert N == len(ret.types) == len(ret.positions) == len(ret.orientations)
    return ret

class Trajectory(object):
    """A trajectory is a sequence of frames."""
    
    def __init__(self, frames=None):
        self.frames = frames or list()

    def __len__(self):
        return len(self.frames)

    def __iter__(self):
        for frame in self.frames:
            yield frame
