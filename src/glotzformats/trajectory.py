"""Trajectories are the path that objects follow
as affected by external forces.

The trajectory module provides classes to store discretized
trajectories."""

import logging
import math
import collections

import numpy as np

from . import math_utils as mu

logger = logging.getLogger(__name__)

SHAPE_DEFAULT_COLOR = '005984FF'


class Box(object):
    """A triclinical box class.

    .. seealso:: https://codeblue.umich.edu/hoomd-blue/doc/page_box.html"""

    def __init__(self, Lx, Ly, Lz, xy=0.0, xz=0.0, yz=0.0, dimensions=3):
        self.Lx = Lx
        self.Ly = Ly
        self.Lz = Lz
        self.xy = xy
        self.xz = xz
        self.yz = yz
        self.dimensions = dimensions

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def get_box_matrix(self):
        """Returns the box matrix (3x3).

        The dimensions (Lx,Ly,Lz) are the diagonal."""
        return [[self.Lx, self.xy * self.Lx, self.xz * self.Lz],
                [0, self.Ly, self.yz * self.Lz],
                [0, 0, self.Lz]]

    def __str__(self):
        return "Box(Lx={Lx}, Ly={Ly}, Lz={Lz},"\
            "xy={xy}, xz={xz}, yz={yz}, dimensions={dimensions})".format(
                ** self.__dict__)

    def __repr__(self):
        return str(self)


class FallbackShapeDefinition(str):
    """This shape definition class is used when no specialized
    ShapeDefinition class can be applied.

    The fallback shape definition is a str containing the definition."""
    pass


class ShapeDefinition(object):
    """Initialize a ShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'sphere' or 'poly3d'.
    :type shape_class: str
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A str for RGB color definiton.
    """

    def __init__(self, shape_class, color=None):
        self.shape_class = shape_class
        self.color = color or SHAPE_DEFAULT_COLOR

    def __str__(self):
        return "{} {}".format(self.shape_class, self.color)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)


class SphereShapeDefinition(ShapeDefinition):
    """Initialize a ShapeDefinition instance.

    :param diameter: The diameter of the sphere.
    :type diameter: A floating point number.
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A str for RGB color definiton."""

    def __init__(self, diameter, color=None):
        super(SphereShapeDefinition, self).__init__(
            shape_class='sphere', color=color)
        self.diameter = diameter

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.diameter, self.color)


class PolyShapeDefinition(ShapeDefinition):
    """Initialize a ShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'sphere' or 'poly3d'.
    :type shape_class: str
    :param vertices: A list of vertice vectors, if applicable.
    :type vertices: A sequence of 3-tuple of numbers (Nx3).
    :param color: Definition of a color for the particular shape.
    :type color: A str for RGB color definiton.
        """

    def __init__(self, shape_class, vertices=None, color=None):
        super(PolyShapeDefinition, self).__init__(
            shape_class=shape_class, color=color)
        self.vertices = vertices

    def __str__(self):
        return "{} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            self.color)


class FrameData(object):
    """One FrameData instance manages the data of one frame in a trajectory."""

    def __init__(self):
        self.box = None
        "Instance of :class:`~.Box`"
        self.types = None
        "Nx1 list of types represented as strings."
        self.positions = None
        "Nx3 matrix of coordinates for N particles in 3 dimensions."
        self.orientations = None
        "Nx4 matrix of rotational coordinates represented as quaternions."
        self.data = None
        "A dictionary of lists for each attribute."
        self.data_keys = None
        "A list of strings, where each string represents one attribute."
        self.shapedef = collections.OrderedDict()
        "A ordered dictionary of instances of :class:`~.ShapeDefinition`."

    def __len__(self):
        return len(self.types)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        else:  # rigorous comparison required
            return self.box == other.box \
                and self.types == other.types\
                and (self.positions == other.positions).all()\
                and (self.orientations == other.orientations).all()\
                and self.data == other.data\
                and self.shapedef == other.shapedef

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "Frame(N={})".format(len(self))

    def __repr__(self):
        return str(self)

    def make_snapshot(self):
        "Create a hoomd-blue snapshot object from this frame."
        return make_hoomd_blue_snapshot(self)

    def copyto_snapshot(self, snapshot):
        "Copy this frame to a hoomd-blue snapshot."
        return copyto_hoomd_blue_snapshot(self, snapshot)


class _RawFrameData(object):
    """Class to capture unprocessed frame data during parsing.

    All matrices are numpy arrays."""

    def __init__(self):
        # 3x3 matrix (not required to be upper-triangular)
        self.box = None
        self.types = list()                         # Nx1
        self.positions = list()                     # Nx3
        self.orientations = list()                  # NX4
        # A dictionary of lists for each attribute
        self.data = None
        self.data_keys = None                       # A list of strings
        # A ordered dictionary of instances of ShapeDefinition
        self.shapedef = collections.OrderedDict()


class Trajectory(object):
    """A trajectory is a sequence of :class:`~.FrameData` instances.

    The length of a trajectory is obtained via `len`.

    .. code::

        N = len(trajectory)

    You can iterate through individual frames like this:

    .. code::

        for frame in trajectory:
            # do something

    Access indivdual frames with indeces:

    .. code::

        first_frame = traj[0]
        last_frame = traj[-1]
        n_th_frame = traj[n]


    Create a sub-trajectory from the i'th to the (j-1)'th frame:

    .. code::

        sub_trajectory = traj[i:j]"""

    def __init__(self, frames=None):
        self.frames = frames or list()

    def __str__(self):
        return "Trajectory(# frames: {})".format(len(self))

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self.frames)

    def __iter__(self):
        for frame in self.frames:
            yield frame

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Trajectory(self.frames[index])
        else:
            return self.frames[index]

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for f1, f2 in zip(self, other):
            if f1 != f2:
                return False
        else:
            return True


def rotate_improper_triclinic(positions, orientations,
                              box_matrix, dimensions=3):
    "Transform the box matrix into a upper-triangular matrix \
     and rotate the system accordingly."
    N = positions.shape[0]
    v = np.zeros((3, 3))
    # source: http://codeblue.umich.edu/hoomd-blue/doc/page_box.html
    v[0] = box_matrix[:, 0]
    v[1] = box_matrix[:, 1]
    v[2] = box_matrix[:, 2]
    Lx = np.sqrt(np.dot(v[0], v[0]))
    a2x = np.dot(v[0], v[1]) / Lx
    Ly = np.sqrt(np.dot(v[1], v[1]) - a2x * a2x)
    xy = a2x / Ly
    v0xv1 = np.cross(v[0], v[1])
    v0xv1mag = np.sqrt(np.dot(v0xv1, v0xv1))
    Lz = np.dot(v[2], v0xv1) / v0xv1mag
    a3x = np.dot(v[0], v[2]) / Lx
    xz = a3x / Lz
    yz = (np.dot(v[1], v[2]) - a2x * a3x) / (Ly * Lz)
    # end of source
    assert 1 < dimensions <= 3
    if dimensions == 2:
        assert Lz == 1
        assert xz == yz == 0
    box = Box(Lx=Lx, Ly=Ly, Lz=Lz, xy=xy, xz=xz, yz=yz, dimensions=dimensions)
    triclinic = v[0][1] == v[0][2] == v[1][2] == 0
    if triclinic:
        return positions, orientations, box

    # unit vector
    e1 = np.array((1.0, 0, 0))

    # Transforming particle orientations
    # Rotation of v[0] into direction x, and v[1] into xy plane
    # Rotation of system, so that v[0] is aligned with x and v[1] in xy-plane
    qbox0toe1 = mu.quaternionRotateVectorOntoVector(v[0], e1)

    # Rotate v[0] into x-direction
    v[0] = mu.rotateVector(v[0], qbox0toe1)
    v[1] = mu.rotateVector(v[1], qbox0toe1)
    v[2] = mu.rotateVector(v[2], qbox0toe1)

    # Rotate system about x-axis, so that v[1] is in xy-plane
    # Angle between v[1] and ex, in the YZ plane
    theta_yz = math.atan2(v[1][2], v[1][1])
    q_y1intoxy = mu.quaternionAxisAngle(e1, -theta_yz)

    v[0] = mu.rotateVector(v[0], q_y1intoxy)
    v[1] = mu.rotateVector(v[1], q_y1intoxy)
    v[2] = mu.rotateVector(v[2], q_y1intoxy)

    # Rotate system particles by the appropriate quaternion composition of the
    # orientations on the system
    qboth = mu.quaternionMultiply(q_y1intoxy, qbox0toe1)
    for i in range(N):
        positions[i] = mu.rotateVector(positions[i], qboth)
        orientations[i] = mu.quaternionMultiply(qboth, orientations[i])
    return positions, orientations, box


def _raw_frame_to_frame(raw_frame):
    """Generate a frame object from a raw frame object."""
    N = len(raw_frame.types)
    ret = FrameData()
    # the box
    positions = np.array(raw_frame.positions)
    orientations = np.array(raw_frame.orientations)
    ret.positions, ret.orientations, ret.box = rotate_improper_triclinic(
        positions, orientations, raw_frame.box)
    ret.shapedef = raw_frame.shapedef
    ret.types = raw_frame.types
    ret.data = raw_frame.data
    ret.data_keys = raw_frame.data_keys
    assert N == len(ret.types) == len(ret.positions) == len(ret.orientations)
    return ret


def copyto_hoomd_blue_snapshot(frame, snapshot):
    "Copy the frame into a hoomd-blue snapshot."
    np.copyto(snapshot.particles.position, frame.positions)
    np.copyto(snapshot.particles.orientation, frame.orientations)
    return snapshot


def make_hoomd_blue_snapshot(frame):
    "Create a hoomd-blue snapshot from the frame instance."
    from hoomd_script import data
    snapshot = data.make_snapshot(
        N=len(frame),
        box=data.boxdim(**frame.box.__dict__),
        particle_types=frame.types)
    return copyto_hoomd_blue_snapshot(frame, snapshot)
