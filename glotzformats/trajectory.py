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
DEFAULT_DTYPE = np.float32


class Box(object):
    """A triclinical box class.

    You can access the box size and tilt factors via attributes:

    .. code-block:: python

        # Reading
        length_x = box.Lx
        tilt_xy = box.xy
        # etc.

        # Setting
        box.lx = 10.0
        box.ly = box.lz = 5.0
        box.xy = box.xz = box.yz = 0.01
        # etc.

    .. seealso:: https://codeblue.umich.edu/HOOMD-blue/doc/page_box.html"""

    def __init__(self, Lx, Ly, Lz, xy=0.0, xz=0.0, yz=0.0, dimensions=3):
        self.Lx = Lx
        "The box length in x-direction."
        self.Ly = Ly
        "The box length in y-direction."
        self.Lz = Lz
        "The box length in z-direction."
        self.xy = xy
        "The box tilt factor in the xy-plane."
        self.xz = xz
        "The box tilt factor in the xz-plane."
        self.yz = yz
        "The box tilt factor in the yz-plane."
        self.dimensions = dimensions
        "The number of box dimensions (2 or 3)."

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def get_box_matrix(self):
        """Returns the box matrix (3x3).

        The dimensions (Lx,Ly,Lz) are the diagonal."""
        return [[self.Lx, self.xy * self.Ly, self.xz * self.Lz],
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


class ArrowShapeDefinition(ShapeDefinition):
    """Initialize a ShapeDefinition instance.

    :param thickness: The thickness of the arrow.
    :type thickness: A floating point number.
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A str for RGB color definiton."""

    def __init__(self, thickness=0.1, color=None):
        super(ArrowShapeDefinition, self).__init__(
            shape_class='arrow', color=color)
        self.thickness = thickness

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.thickness, self.color)

class SphereUnionShapeDefinition(ShapeDefinition):
    """Initialize a ShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'sphere' or 'poly3d'.
    :type shape_class: str
    :param diameters: A list of sphere diameters
    :type diameters: A sequence of floats
    :param centers: A list of vertex vectors, if applicable.
    :type centers: A sequence of 3-tuple of numbers (Nx3).
    :param colors: Definition of a color for every sphere
    :type colors: A sequence of str for RGB color definiton.
        """

    def __init__(self, shape_class, diameters=None, centers=None, colors=None):
        super(SphereUnionShapeDefinition, self).__init__(
            shape_class=shape_class, color='')
        self.diameters = diameters
        self.centers = centers
        self.colors = colors

    def __str__(self):
        shape_def = '{} {} '.format(self.shape_class,len(self.centers))
        for d,p,c in zip(self.diameters, self.centers, self.colors):
            shape_def += '{0} '.format(d)
            shape_def += '{0} {1} {2} '.format(*p)
            shape_def += '{0} '.format(c)

        return shape_def

class PolyUnionShapeDefinition(ShapeDefinition):
    """Initialize a ShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'sphere' or 'poly3d'.
    :type shape_class: str
    :param vertices: A list of lists of the vertices of the polyhedra in particle coordinates
    :type vertices: A list of lists of 3-tuples
    :param centers: A list of the centers of the polyhedra in particle coordinates
    :type centers: A list of 3-tuples
    :param orientations: A list of the orientations of the polyhedra
    :type orientations: A list of 4-tuples
    :param colors: Definition of a color for every polyhedron
    :type colors: A sequence of str for RGB color definiton.
        """

    def __init__(self, shape_class, vertices=None, centers=None, orientations=None, colors=None):
        super(PolyUnionShapeDefinition, self).__init__(
            shape_class=shape_class, color='')
        self.vertices = vertices
        self.centers = centers
        self.orientations = orientations
        self.colors = colors

    def __str__(self):
        shape_def = '{} {} '.format(self.shape_class,len(self.centers))
        for verts,p,q,c in zip(self.vertices, self.centers, self.orientations, self.colors):
            shape_def += '{0} '.format(len(verts))
            for v in verts:
                shape_def += '{0} {1} {2} '.format(*v)
            shape_def += '{0} {1} {2} '.format(*p)
            shape_def += '{0} {1} {2} {3} '.format(*q)
            shape_def += '{0} '.format(c)

        return shape_def

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

class GeneralPolyShapeDefinition(ShapeDefinition):
    """Initialize a ShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'sphere' or 'poly3d'.
    :type shape_class: str
    :param vertices: A list of vertice vectors.
    :type vertices: A sequence of 3-tuple of numbers (Nx3).
    :param faces: A list of lists of vertex indices per face.
    :type faces: A list of lists of integer numbers.
    :param color: Definition of a color for the particular shape.
    :type color: A str for RGB color definiton.
        """

    def __init__(self, shape_class, vertices=None, faces=None, color=None):
        super(GeneralPolyShapeDefinition, self).__init__(
            shape_class=shape_class, color=color)
        self.vertices = vertices
        self.faces = faces

    def __str__(self):
        return "{} {} {} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            len(self.faces),
            ' '.join((str(fv) for f in self.faces for fv in [len(f)]+f)),
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
        self.velocities = None
        "Nx3 matrix of velocities for N particles in 3 dimensions."
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
                and (self.velocities == other.velocities).all()\
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
        "Create a HOOMD-blue snapshot object from this frame."
        return make_hoomd_blue_snapshot(self)

    def copyto_snapshot(self, snapshot):
        "Copy this frame to a HOOMD-blue snapshot."
        return copyto_hoomd_blue_snapshot(self, snapshot)


class _RawFrameData(object):
    """Class to capture unprocessed frame data during parsing.

    All matrices are numpy arrays."""

    def __init__(self):
        # 3x3 matrix (not required to be upper-triangular)
        self.box = None
        self.box_dimensions = 3
        self.types = list()                         # Nx1
        self.positions = list()                     # Nx3
        self.velocities = list()                     # Nx3
        self.orientations = list()                  # NX4
        # A dictionary of lists for each attribute
        self.data = None
        self.data_keys = None                       # A list of strings
        # A ordered dictionary of instances of ShapeDefinition
        self.shapedef = collections.OrderedDict()


class Frame(object):
    """A frame is a container object for the actual frame data.

    The frame data is read from the origin stream whenever accessed.

    :param dtype: The data type for frame data.
    """

    def __init__(self, dtype=None):
        if dtype is None:
            dtype = DEFAULT_DTYPE
        self.frame_data = None
        self._dtype = dtype

    def loaded(self):
        "Returns True if the frame is loaded into memory."
        return self.frame_data is not None

    def load(self):
        "Load the frame into memory."
        if self.frame_data is None:
            logger.debug("Loading frame.")
            self.frame_data = _raw_frame_to_frame(self.read(), self._dtype)

    def unload(self):
        """Unload the frame from memory.

        Use this method carefully.
        This method removes the frame reference to the frame data,
        however any other references that may still exist, will
        prevent a removal of said data from memory."""
        logger.debug("Removing frame data reference.")
        self.frame_data = None

    @property
    def dtype(self):
        "Return the data type for frame data."
        return self._dtype

    @dtype.setter
    def dtype(self, value):
        """Change the data type for frame data.

        :param value: The data type value.
        :raises RuntimeError: If called for a loaded frame."""
        if self.loaded():
            raise RuntimeError(
                "Cannot change the data type after frame is loaded.")
        self._dtype = value

    def __len__(self):
        "Return the number of particles in this frame."
        self.load()
        return len(self.frame_data)

    def __eq__(self, other):
        self.load()
        other.load()
        return self.frame_data == other.frame_data

    def __ne__(self, other):
        return not self.__eq__(other)

    def make_snapshot(self):
        "Create a HOOMD-blue snapshot object from this frame."
        self.load()
        return make_hoomd_blue_snapshot(self.frame_data)

    def copyto_snapshot(self, snapshot):
        "Copy this frame to a HOOMD-blue snapshot."
        self.load()
        return copyto_hoomd_blue_snapshot(self.frame_data, snapshot)

    @property
    def box(self):
        "Instance of :class:`~.Box`"
        self.load()
        return self.frame_data.box

    @box.setter
    def box(self, value):
        self.load()
        self.frame_data.box = value

    @property
    def types(self):
        "Nx1 list of types represented as strings."
        self.load()
        return self.frame_data.types

    @types.setter
    def types(self, value):
        self.load()
        self.frame_data.types = value

    @property
    def positions(self):
        "Nx3 matrix of coordinates for N particles in 3 dimensions."
        self.load()
        return self.frame_data.positions

    @positions.setter
    def positions(self, value):
        self.load()
        self.frame_data.positions = value

    @property
    def velocities(self):
        "Nx3 matrix of velocities for N particles in 3 dimensions."
        self.load()
        return self.frame_data.velocities

    @velocities.setter
    def velocities(self, value):
        self.load()
        self.frame_data.velocities = value

    @property
    def orientations(self):
        "Nx4 matrix of rotational coordinates represented as quaternions."
        self.load()
        return self.frame_data.orientations

    @orientations.setter
    def orientations(self, value):
        self.load()
        self.frame_data.orientations = value

    @property
    def data(self):
        "A dictionary of lists for each attribute."
        self.load()
        return self.frame_data.data

    @data.setter
    def data(self, value):
        self.load()
        self.frame_data.data = value

    @property
    def data_keys(self):
        "A list of strings, where each string represents one attribute."
        self.load()
        return self.frame_data.data_keys

    @data_keys.setter
    def data_keys(self, value):
        self.load()
        self.frame_data.data_keys = value

    @property
    def shapedef(self):
        "A ordered dictionary of instances of :class:`~.ShapeDefinition`."
        self.load()
        return self.frame_data.shapedef

    @shapedef.setter
    def shapedef(self, value):
        self.load()
        self.frame_data.shapedef = value


class BaseTrajectory(object):

    def __init__(self, frames=None):
        self.frames = frames or list()

    def __str__(self):
        try:
            return "Trajectory(# frames: {})".format(len(self))
        except TypeError:
            return "Trajectory(# frames: n/a)"

    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, index):
        if isinstance(index, slice):
            traj = type(self)(self.frames[index])
            for x in ('_types', '_positions', '_orientations', '_type', '_type_ids', '_N'):
                if getattr(self, x) is not None:
                    setattr(traj, x, getattr(self, x)[index])
            return traj
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


class ImmutableTrajectory(BaseTrajectory):
    """The immutable trajectory class is used internally to
    provide efficient immutable iterators over trajectories."""

    class ImmutableTrajectoryIterator(object):

        def __init__(self, traj):
            self.frame_iter = iter(traj.frames)
            self.frame = None
            self._unload_last = None

        def __iter__(self):
            return self

        def __next__(self):
            if self.frame is not None and self._unload_last:
                self.frame.unload()
            self.frame = next(self.frame_iter)
            self._unload_last = not self.frame.loaded()
            return self.frame

        next = __next__

    def __init__(self, frames=None):
        super(ImmutableTrajectory, self).__init__(frames=frames)

    def __iter__(self):
        return ImmutableTrajectory.ImmutableTrajectoryIterator(self)


class Trajectory(BaseTrajectory):
    """Manages a particle trajectory data resource.

    A trajectory is basically a sequence of :class:`~.Frame` instances.

    Trajectory data can either be accessed as coherent numpy arrays:

    .. code::

        traj.load_arrays()
        M = len(traj)
        traj.N             # M
        traj.positions     # MxNx3
        traj.orientations  # MxNx4
        traj.types         # MxN
        traj.type_ids      # MxN

    or by individual frames:

    .. code::

        first_frame = traj[0]
        last_frame = traj[-1]
        n_th_frame = traj[n]

        first_frame.positions     # Nx3
        first_frame.orientations  # Nx4
        first_frame.types         # Nx1

    You can iterate through individual frames:

    .. code::

        for frame in trajectory:
            print(frame.positions)

    and create a sub-trajectory from the *i'th* to the *(j-1)'th* frame:

    .. code::

        sub_trajectory = traj[i:j]

    :param frames: The individual frames of this trajectory.
    :type frames: :class:`~.Frame`
    :param dtype: The default data type for trajectory data.
    """

    def __init__(self, frames=None, dtype=None):
        super(Trajectory, self).__init__(frames=frames)
        if dtype is None:
            dtype = DEFAULT_DTYPE
        self._dtype = dtype
        self._N = None
        self._type = None
        self._types = None
        self._type_ids = None
        self._positions = None
        self._orientations = None

    def __iter__(self):
        return iter(ImmutableTrajectory(self.frames))

    def load(self):
        """Load all frames into memory.

        By default, only frames which are accessed are loaded
        into memory. Using this function, all frames are loaded
        at once.

        This can be useful, e.g., if the trajectory resource cannot
        remain open, however in all other cases this should be
        avoided.

        See also: :meth:`~.load_arrays`
        """
        self.load_arrays()
        for frame in self.frames:
            frame.load()

    def loaded(self):
        """Returns True if all frames are loaded into memory.

        See also: :meth:`~.Trajectory.load`"""
        return all((f.loaded() for f in self.frames))

    def arrays_loaded(self):
        """Returns true if arrays are loaded into memory.

        See also: :meth:`~.load_arrays`"""
        return not (self._N is None or
                    self._type is None or
                    self._types is None or
                    self._type_ids is None or
                    self._positions is None or
                    self._orientations is None)

    def _assert_loaded(self):
        "Raises a RuntimeError if trajectory is not loaded."
        if not self.loaded():
            raise RuntimeError("Trajectory not loaded! Use load().")

    def _assertarrays_loaded(self):
        "Raises a RuntimeError if trajectory arrays are not loaded."
        if not self.arrays_loaded():
            raise RuntimeError(
                "Trajectory arrays not loaded! Use load_arrays() or load().")

    def _max_N(self):
        "Returns the size of the largest frame within this trajectory."
        return max((len(f) for f in self.frames))

    def load_arrays(self):
        """Load positions, orientations and types into memory.

        After calling this function, positions, orientations
        and types can be accessed as coherent numpy arrays:

        .. code::

            traj.load_arrays()
            traj.N             # M -- frame sizes
            traj.positions     # MxNx3
            traj.orientations  # MxNx4
            traj.types         # MxN
            traj.type_ids      # MxN

        .. note::

            It is not necessary to call this function again when
            accessing sub trajectories:

            .. code::

                traj.load_arrays()
                sub_traj = traj[m:n]
                sub_traj.positions

            However, it may be more efficient to call :meth:`~.load_arrays`
            only for the sub trajectory if other data is not of interest:

            .. code::

                sub_traj = traj[m:n]
                sub_traj.load_arrays()
                sub_traj.positions
        """
        # Determine array shapes
        _N = np.array([len(f) for f in self.frames], dtype=np.int_)
        M = len(self)
        N = _N.max()

        # Types
        types = [f.types for f in self.frames]
        type_ids = np.zeros((M, N), dtype=np.int_)
        _type = _generate_type_id_array(types, type_ids)

        # Coordinates
        pos = np.zeros((M, N, 3), dtype=self._dtype)
        ort = np.zeros((M, N, 4), dtype=self._dtype)
        for i, frame in enumerate(self.frames):
            sp = frame.positions.shape
            pos[i][:sp[0], :sp[1]] = frame.positions
            so = frame.orientations.shape
            ort[i][:so[0], :so[1]] = frame.orientations

        try:
            # Perform swap
            self._N = _N
            self._type = _type
            self._types = types
            self._type_ids = type_ids
            self._positions = pos
            self._orientations = ort
        except Exception:
            # Ensure consistent error state
            self._N = self._type = self._types = self._type_ids = \
                self._positions = self._orientations = None
            raise

    def set_dtype(self, value):
        """Change the data type of this trajectory.

        This function cannot be called if any frame
        is already loaded.

        :param value: The new data type value."""
        self._dtype = value
        for x in (self._positions, self._orientations):
            if x is not None:
                x = x.astype(value)
        for frame in self.frames:
            frame.dtype = value

    @property
    def N(self):
        """Access the frame sizes as numpy array.

        Mostly important when the trajectory has varying size.

        .. code::

            pos_i = traj.positions[i][0:traj.N[i]]

        :returns: frame size as array with length M
        :rtype: :class:`numpy.ndarray` (dtype= :class:`numpy.int_`)
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        return np.asarray(self._N, dtype=np.int_)

    @property
    def types(self):
        """Access the particle types as numpy array.

        :returns: particles types as (MxN) array
        :rtype: :class:`numpy.ndarray` (dtype= :class:`numpy.str_` )
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        return np.asarray(self._types, dtype=np.str_)

    @property
    def type(self):
        """List of type names ordered by type_id.

        Use the type list to map between type_ids and type names:

        .. code::

            type_name = traj.type[type_id]

        See also: :attr:`~.Trajectory.type_ids`

        :returns: particle types in order of type id.
        :rtype: list
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        return self._type

    @property
    def type_ids(self):
        """Access the particle type ids as numpy array.

        See also: :attr:`~.Trajectory.type`

        :returns: particle type ids as (MxN) array.
        :rtype: :class:`numpy.ndarray` (dtype= :class:`numpy.int_` )
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        return np.asarray(self._type_ids, dtype=np.int_)

    @property
    def positions(self):
        """Access the particle positions as numpy array.

        :returns: particle positions as (Nx3) array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        return np.asarray(self._positions, dtype=self._dtype)

    @property
    def orientations(self):
        """Access the particle orientations as numpy array.

        Orientations are stored as quaternions.

        :returns: particle orientations as (Nx4) array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        return np.asarray(self._orientations, dtype=self._dtype)


def _regularize_box(positions, velocities, orientations,
                    box_matrix, dimensions=3):
    """If necessary, transform the box matrix into an
    upper-triangular matrix and rotate the system accordingly."""
    v = np.zeros((3, 3))
    v[0] = box_matrix[:, 0]
    v[1] = box_matrix[:, 1]
    v[2] = box_matrix[:, 2]
    if 0 == v[0][1] == v[0][2] == v[1][2]:
        box, positions, velocities = _flip_if_required(_calc_box(v, dimensions), positions, velocities)
        return positions, velocities, orientations, box
    logger.info("Box matrix is left-handed, rotating.")
    box = _rotate_improper(v, dimensions, positions, velocities, orientations)
    box, positions, velocities = _flip_if_required(box, positions, velocities)
    return positions, velocities, orientations, box


def _rotate_improper(v, dimensions, positions, velocities, orientations):
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
    box = _calc_box(v, dimensions)

    # Rotate system particles by the appropriate
    # quaternion composition of the orientations on the system
    qboth = mu.quaternionMultiply(q_y1intoxy, qbox0toe1)
    for i in range(positions.shape[0]):
        positions[i] = mu.rotateVector(positions[i], qboth)
        velocities[i] = mu.rotateVector(velocities[i], qboth)
        orientations[i] = mu.quaternionMultiply(qboth, orientations[i])

    return box


def _flip_if_required(box, positions, velocities):
    v = np.asarray(box.get_box_matrix())
    m = np.diag(np.where(v < 0, -np.ones(v.shape), np.ones(v.shape)))
    if (m > 0).all():
        return box, positions, velocities
    logger.info("Box has negative dimensions, flipping.")
    v = np.dot(v, np.diag(m))
    positions = np.dot(positions, np.diag(m))
    velocities = np.dot(velocities, np.diag(m))
    return _calc_box(v, box.dimensions), positions, velocities


def _calc_box(v, dimensions):
    # source: http://codeblue.umich.edu/HOOMD-blue/doc/page_box.html
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
    assert 1 < dimensions <= 3
    return Box(Lx=Lx, Ly=Ly, Lz=Lz, xy=xy, xz=xz, yz=yz, dimensions=dimensions)


def _generate_type_id_array(types, type_ids):
    "Generate type_id array."
    _type = sorted(set(t_ for t in types for t_ in t))
    for i, t in enumerate(types):
        for j, t_ in enumerate(t):
            type_ids[i][j] = _type.index(t_)
    return _type


def _raw_frame_to_frame(raw_frame, dtype=None):
    """Generate a frame object from a raw frame object."""
    N = len(raw_frame.types)
    ret = FrameData()
    # the box
    positions = np.asarray(raw_frame.positions, dtype=dtype)
    velocities = np.asarray(raw_frame.velocities, dtype=dtype)
    if len(velocities) == 0:
        velocities = np.asarray([[0, 0, 0]] * len(positions))
    orientations = np.asarray(raw_frame.orientations, dtype=dtype)
    if len(orientations) == 0:
        orientations = np.asarray([[1, 0, 0, 0]] * len(positions))

    if isinstance(raw_frame.box, Box):
        raw_frame.box_dimensions = raw_frame.box.dimensions
        raw_frame.box = np.asarray(raw_frame.box.get_box_matrix(), dtype=dtype)
    box_dimensions = getattr(raw_frame, 'box_dimensions', 3)
    ret.positions, ret.velocities, ret.orientations, ret.box = _regularize_box(
        positions, velocities, orientations, raw_frame.box, box_dimensions)
    ret.shapedef = raw_frame.shapedef
    ret.types = raw_frame.types
    ret.data = raw_frame.data
    ret.data_keys = raw_frame.data_keys
    assert N == len(ret.types) == len(ret.positions) == len(ret.velocities) == len(ret.orientations)
    return ret


def copyto_hoomd_blue_snapshot(frame, snapshot):
    "Copy the frame into a HOOMD-blue snapshot."
    np.copyto(snapshot.particles.position, frame.positions)
    np.copyto(snapshot.particles.orientation, frame.orientations)
    return snapshot


def copyfrom_hoomd_blue_snapshot(frame, snapshot):
    """"Copy the HOOMD-blue snapshot into the frame.

    Note that only the box, types, positions and
    orientations will be copied."""
    frame.box.__dict__ = snapshot.box.__dict__
    particle_types = list(set(snapshot.particles.types))
    snap_types = [particle_types[i] for i in snapshot.particles.typeid]
    frame.types = snap_types
    frame.positions = snapshot.particles.position
    frame.orientations = snapshot.particles.orientation
    return frame


def make_hoomd_blue_snapshot(frame):
    "Create a HOOMD-blue snapshot from the frame instance."
    try:
        from hoomd import data
    except ImportError:
        try:
            # Try importing from hoomd 1.x
            from hoomd_script import data
        except ImportError:
            raise ImportError('hoomd')
    particle_types = list(set(frame.types))
    type_ids = [particle_types.index(t) for t in frame.types]
    snapshot = data.make_snapshot(
        N=len(frame),
        box=data.boxdim(**frame.box.__dict__),
        particle_types=particle_types)
    np.copyto(
        snapshot.particles.typeid,
        np.array(type_ids, dtype=snapshot.particles.typeid.dtype))
    return copyto_hoomd_blue_snapshot(frame, snapshot)
