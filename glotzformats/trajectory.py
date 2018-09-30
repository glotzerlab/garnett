"""Trajectories are the path that objects follow
as affected by external forces.

The trajectory module provides classes to store discretized
trajectories."""

import logging
import math
import collections

import numpy as np

import rowan

logger = logging.getLogger(__name__)

SHAPE_DEFAULT_COLOR = '005984FF'
DEFAULT_DTYPE = np.float32

ARRAY_PROPERTIES = ['positions', 'orientations', 'velocities', 'mass',
                    'charge', 'diameter', 'moment_inertia', 'angmom']

HOOMD_SNAPSHOT_PROPERTY_MAP = {
    'positions': 'position',
    'orientations': 'orientation',
    'velocities': 'velocity',
}

def _make_default_array(attr, shape, dtype=DEFAULT_DTYPE):
    if attr == 'types':
        return np.zeros(shape, dtype=np.int_)
    elif attr in ['positions', 'velocities']:
        return np.zeros(shape + (3,), dtype=dtype)
    elif attr == 'orientations':
        orientations = np.zeros(shape + (4,), dtype=dtype)
        orientations[..., 0] = 1
        return orientations
    elif attr == 'angmom':
        return np.zeros(shape + (4,), dtype=dtype)
    elif attr in ['mass', 'diameter']:
        return np.ones(shape, dtype=dtype)
    elif attr == 'charge':
        return np.zeros(shape, dtype=dtype)
    elif attr == 'moment_inertia':
        return np.ones(shape + (3,), dtype=dtype)


class Box(object):
    """A triclinic box class.

    You can access the box size and tilt factors via attributes:

    .. code-block:: python

        # Reading
        length_x = box.Lx
        tilt_xy = box.xy
        # etc.

        # Setting
        box.Lx = 10.0
        box.Ly = box.Lz = 5.0
        box.xy = box.xz = box.yz = 0.01
        # etc.

    .. seealso:: http://hoomd-blue.readthedocs.io/en/stable/box.html"""

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

    def get_box_array(self):
        """Returns the box parameters as a 6-element list."""
        return [self.Lx, self.Ly, self.Lz, self.xy, self.xz, self.yz]

    def __str__(self):
        return "Box(Lx={Lx}, Ly={Ly}, Lz={Lz},"\
            "xy={xy}, xz={xz}, yz={yz}, dimensions={dimensions})".format(
                ** self.__dict__)

    def __repr__(self):
        return str(self)

    def round(self, decimals=0):
        "Return box instance with all values rounded up to the given precision."
        return Box(
            Lx=np.round(self.Lx, decimals),
            Ly=np.round(self.Ly, decimals),
            Lz=np.round(self.Lz, decimals),
            xy=np.round(self.xy, decimals),
            xz=np.round(self.xz, decimals),
            yz=np.round(self.yz, decimals),
            dimensions=self.dimensions)


class FallbackShapeDefinition(str):
    """This shape definition class is used when no specialized
    ShapeDefinition class can be applied.

    The fallback shape definition is a str containing the definition."""
    pass


class ShapeDefinition(object):
    """Initialize a ShapeDefinition instance.

    :param shape_class: The shape class definition, e.g. 'sphere' or 'poly3d'.
    :type shape_class: str
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A hexadecimal color string in format RRGGBBAA.
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
    """Initialize a SphereShapeDefinition instance.

    :param diameter: The diameter of the sphere.
    :type diameter: A floating point number.
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, diameter, color=None):
        super(SphereShapeDefinition, self).__init__(
            shape_class='sphere', color=color)
        self.diameter = diameter

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.diameter, self.color)

    @property
    def json_shape(self):
        return {'type': 'Sphere',
                'color': self.color}


class ArrowShapeDefinition(ShapeDefinition):
    """Initialize an ArrowShapeDefinition instance.

    :param thickness: The thickness of the arrow.
    :type thickness: A floating point number.
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, thickness=0.1, color=None):
        super(ArrowShapeDefinition, self).__init__(
            shape_class='arrow', color=color)
        self.thickness = thickness

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.thickness, self.color)

class SphereUnionShapeDefinition(ShapeDefinition):
    """Initialize a SphereUnionShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'sphere_union'.
    :type shape_class: str
    :param diameters: A list of sphere diameters
    :type diameters: A sequence of floats
    :param centers: A list of vertex vectors, if applicable.
    :type centers: A sequence of 3-tuples of numbers (Nx3).
    :param colors: Definition of a color for every sphere
    :type colors: A sequence of hexadecimal color strings in format RRGGBBAA.
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
    """Initialize a PolyShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'poly3d'.
    :type shape_class: str
    :param vertices: A list of vertice vectors, if applicable.
    :type vertices: A sequence of 3-tuple of numbers (Nx3).
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format RRGGBBAA.
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

    @property
    def json_shape(self):
        return {'type': 'ConvexPolyhedron',
                'color': self.color,
                'rounding_radius': 0,
                'vertices': self.vertices}

class SpheroPolyShapeDefinition(ShapeDefinition):
    """Initialize a SpheroPolyShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'spoly3d'.
    :type shape_class: str
    :param vertices: A list of vertex vectors, if applicable.
    :type vertices: A sequence of 3-tuple of numbers (Nx3).
    :param rounding_radius: Rounding radius applied to the spheropolyhedron.
    :type rounding_radius: A floating-point number.
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, shape_class, vertices=None, rounding_radius=None, color=None):
        super(SpheroPolyShapeDefinition, self).__init__(
            shape_class=shape_class, color=color)
        self.vertices = vertices
        self.rounding_radius = rounding_radius

    def __str__(self):
        return "{} {} {} {} {}".format(
            self.shape_class,
            self.rounding_radius,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            self.color)

    @property
    def json_shape(self):
        return {'type': 'ConvexPolyhedron',
                'color': self.color,
                'rounding_radius': self.rounding_radius,
                'vertices': self.vertices}

class GeneralPolyShapeDefinition(ShapeDefinition):
    """Initialize a GeneralPolyShapeDefinition instance.

    :param shape_class: The shape class definition,
                        e.g. 'polyv'.
    :type shape_class: str
    :param vertices: A list of vertex vectors.
    :type vertices: A sequence of 3-tuple of numbers (Nx3).
    :param faces: A list of lists of vertex indices per face.
    :type faces: A list of lists of integer numbers.
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, shape_class, vertices=None, faces=None, color=None, facet_colors=None):
        super(GeneralPolyShapeDefinition, self).__init__(
            shape_class=shape_class, color=color)
        self.vertices = vertices
        self.faces = faces
        self.facet_colors = facet_colors

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
        self.orientations = None
        "Nx4 matrix of rotational coordinates for N particles represented as quaternions."
        self.velocities = None
        "Nx3 matrix of velocities for N particles in 3 dimensions."
        self.mass = None
        "Nx1 list of masses for N particles."
        self.charge = None
        "Nx1 list of charges for N particles."
        self.diameter = None
        "Nx1 list of diameters for N particles."
        self.moment_inertia = None
        "Nx3 matrix of principal moments of inertia for N particles in 3 dimensions."
        self.angmom = None
        "Nx4 matrix of angular momenta for N particles represented as quaternions."
        self.data = None
        "A dictionary of lists for each attribute."
        self.data_keys = None
        "A list of strings, where each string represents one attribute."
        self.shapedef = collections.OrderedDict()
        "A ordered dictionary of instances of :class:`~.ShapeDefinition`."
        self.view_rotation = None
        "A quaternion specifying a rotation that should be applied for visualization."

    def __len__(self):
        return len(self.types)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        else:  # rigorous comparison required
            comparison = {}

            def compare_attr(attr, array=False):
                selfattr = getattr(self, attr, None)
                otherattr = getattr(other, attr, None)
                if attr == 'box':
                    # Compare boxes
                    comparison[attr] = np.allclose(selfattr.get_box_array(), otherattr.get_box_array())
                elif attr == 'shapedef' and selfattr and otherattr:
                    # Compare shape definitions, irrespective of type order in the OrderedDict
                    comparison[attr] = dict(selfattr) == dict(otherattr)
                elif array and selfattr is not None and otherattr is not None:
                    # Compare array properties like positions, when both frame properties are not None
                    comparison[attr] = np.allclose(selfattr, otherattr)
                elif not array and selfattr and otherattr:
                    # Compare non-array properties, when both frame properties are non-empty
                    comparison[attr] = selfattr == otherattr

            for attr in ['box', 'types', 'data', 'shapedef']:
                compare_attr(attr)
            for attr in ARRAY_PROPERTIES:
                compare_attr(attr, array=True)
            return all(comparison.values())

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
        self.orientations = list()                  # Nx4
        self.velocities = list()                    # Nx3
        self.mass = list()                          # Nx1
        self.charge = list()                        # Nx1
        self.diameter = list()                      # Nx1
        self.moment_inertia = list()                # Nx3
        self.angmom = list()                        # Nx4
        # A dictionary of lists for each attribute
        self.data = None
        self.data_keys = None                       # A list of strings
        # A ordered dictionary of instances of ShapeDefinition
        self.shapedef = collections.OrderedDict()
        # A view rotation (does not affect the actual trajectory)
        self.view_rotation = None


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

    def _raw_frame_to_frame(self, raw_frame, dtype=None):
        """Generate a frame object from a raw frame object."""
        N = len(raw_frame.types)
        ret = FrameData()
        # the box
        positions = np.asarray(raw_frame.positions, dtype=dtype)

        orientations = np.asarray(raw_frame.orientations, dtype=dtype)
        if len(orientations) == 0:
            orientations = None

        velocities = np.asarray(raw_frame.velocities, dtype=dtype)
        if len(velocities) == 0:
            velocities = None

        mass = np.asarray(raw_frame.mass, dtype=dtype)
        if len(mass) == 0:
            mass = None

        charge = np.asarray(raw_frame.charge, dtype=dtype)
        if len(charge) == 0:
            charge = None

        diameter = np.asarray(raw_frame.diameter, dtype=dtype)
        if len(diameter) == 0:
            diameter = None

        moment_inertia = np.asarray(raw_frame.moment_inertia, dtype=dtype)
        if len(moment_inertia) == 0:
            moment_inertia = None

        angmom = np.asarray(raw_frame.angmom, dtype=dtype)
        if len(angmom) == 0:
            angmom = None

        assert raw_frame.box is not None
        if isinstance(raw_frame.box, Box):
            raw_frame.box_dimensions = raw_frame.box.dimensions
            raw_frame.box = np.asarray(raw_frame.box.get_box_matrix(), dtype=dtype)
        box_dimensions = getattr(raw_frame, 'box_dimensions', 3)
        ret.positions, ret.velocities, \
        ret.orientations, ret.angmom, ret.box = _regularize_box(
            positions, velocities, orientations, angmom,
            raw_frame.box, dtype, box_dimensions)
        ret.mass = mass
        ret.charge = charge
        ret.diameter = diameter
        ret.moment_inertia = moment_inertia
        ret.shapedef = raw_frame.shapedef
        ret.types = raw_frame.types
        ret.data = raw_frame.data
        ret.data_keys = raw_frame.data_keys
        ret.view_rotation = raw_frame.view_rotation

        def assert_lengths(attr):
            assert getattr(ret, attr, None) is None or len(getattr(ret, attr)) == N, \
                "Frame property '{}' is not valid. Must be None or have length {}.".format(attr, N)

        assert_lengths('types')
        for attr in ARRAY_PROPERTIES:
            assert_lengths(attr)
        return ret

    def loaded(self):
        "Returns True if the frame is loaded into memory."
        return self.frame_data is not None

    def load(self):
        "Load the frame into memory."
        if self.frame_data is None:
            logger.debug("Loading frame.")
            self.frame_data = self._raw_frame_to_frame(self.read(), dtype=self._dtype)

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
        # Various sanity checks
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Positions can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Positions being set must all be finite numbers.")
        elif not len(value.shape) == 2 or value.shape[1] != self.box.dimensions:
            raise ValueError("Input array must be of shape (N,{}) where N is the number of particles.".format(self.box.dimensions))

        self.load()
        self.frame_data.positions = value

    @property
    def orientations(self):
        "Nx4 matrix of rotational coordinates for N particles represented as quaternions."
        self.load()
        return self.frame_data.orientations

    @orientations.setter
    def orientations(self, value):
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Orientations can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Orientations being set must all be finite numbers.")
        elif not len(value.shape) == 2 or value.shape[1] != 4:
            raise ValueError("Input array must be of shape (N,4) where N is the number of particles.")

        self.load()
        self.frame_data.orientations = value

    @property
    def velocities(self):
        "Nx3 matrix of velocities for N particles in 3 dimensions."
        self.load()
        return self.frame_data.velocities

    @velocities.setter
    def velocities(self, value):
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Velocities can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Velocities being set must all be finite numbers.")
        elif not len(value.shape) == 2 or value.shape[1] != self.box.dimensions:
            raise ValueError("Input array must be of shape (N,{}) where N is the number of particles.".format(self.box.dimensions))
        self.load()
        self.frame_data.velocities = value

    @property
    def mass(self):
        "Nx1 list of masses for N particles."
        self.load()
        return self.frame_data.mass

    @mass.setter
    def mass(self, value):
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Masses can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Masses being set must all be finite numbers.")
        elif not len(value.shape) == 1:
            raise ValueError("Input array must be of shape (N) where N is the number of particles.")
        self.load()
        self.frame_data.mass = value

    @property
    def charge(self):
        "Nx1 list of charges for N particles."
        self.load()
        return self.frame_data.charge

    @charge.setter
    def charge(self, value):
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Charges can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Charges being set must all be finite numbers.")
        elif not len(value.shape) == 1:
            raise ValueError("Input array must be of shape (N) where N is the number of particles.")
        self.load()
        self.frame_data.charge = value

    @property
    def diameter(self):
        "Nx1 list of diameters for N particles."
        self.load()
        return self.frame_data.diameter

    @diameter.setter
    def diameter(self, value):
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Diameters can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Diameters being set must all be finite numbers.")
        elif not len(value.shape) == 1:
            raise ValueError("Input array must be of shape (N) where N is the number of particles.")
        self.load()
        self.frame_data.diameter = value

    @property
    def moment_inertia(self):
        "Nx3 matrix of principal moments of inertia for N particles in 3 dimensions."
        self.load()
        return self.frame_data.moment_inertia

    @moment_inertia.setter
    def moment_inertia(self, value):
        ndof = self.box.dimensions * (self.box.dimensions - 1) / 2
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Moments of inertia can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Moments of inertia being set must all be finite numbers.")
        elif not len(value.shape) == 2 or value.shape[1] != ndof:
            raise ValueError("Input array must be of shape (N,{}) where N is the number of particles.".format(ndof))
        self.load()
        self.frame_data.moment_inertia = value

    @property
    def angmom(self):
        "Nx4 matrix of angular momenta for N particles represented as quaternions."
        self.load()
        return self.frame_data.angmom

    @angmom.setter
    def angmom(self, value):
        try:
            value = np.asarray(value, dtype=self._dtype)
        except ValueError:
            raise ValueError("Angular momenta can only be set to numeric arrays.")
        if not np.all(np.isfinite(value)):
            raise ValueError("Angular momenta being set must all be finite numbers.")
        elif not len(value.shape) == 2 or value.shape[1] != 4:
            raise ValueError("Input array must be of shape (N,4) where N is the number of particles.")

        self.load()
        self.frame_data.angmom = value

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

    @property
    def view_rotation(self):
        self.load()
        return self.frame_data.view_rotation


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
            for x in ('_N', '_types', '_type', '_type_ids',
                      '_positions', '_orientations', '_velocities',
                      '_mass', '_charge', '_diameter',
                      '_moment_inertia', '_angmom'):
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
        self._velocities = None
        self._mass = None
        self._charge = None
        self._diameter = None
        self._moment_inertia = None
        self._angmom = None

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
                    self._orientations is None or
                    self._velocities is None or
                    self._mass is None or
                    self._charge is None or
                    self._diameter is None or
                    self._moment_inertia is None or
                    self._angmom is None)

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
        type_ids = _make_default_array('types', (M, N))
        _type = _generate_type_id_array(types, type_ids)

        props = {attr: _make_default_array(attr, (M, N), self._dtype) for attr in ARRAY_PROPERTIES}

        for i, frame in enumerate(self.frames):
            for prop in ARRAY_PROPERTIES:
                frame_prop = getattr(frame, prop)
                if frame_prop is not None:
                    prop_shape = frame_prop.shape
                    if len(prop_shape) == 1:
                        props[prop][i][:prop_shape[0]] = frame_prop
                    elif len(prop_shape) == 2:
                        props[prop][i][:prop_shape[0], :prop_shape[1]] = frame_prop

        try:
            # Perform swap
            self._N = _N
            self._type = _type
            self._types = types
            self._type_ids = type_ids
            self._positions = props['positions']
            self._orientations = props['orientations']
            self._velocities = props['velocities']
            self._mass = props['mass']
            self._charge = props['charge']
            self._diameter = props['diameter']
            self._moment_inertia = props['moment_inertia']
            self._angmom = props['angmom']
        except Exception:
            # Ensure consistent error state
            self._N = self._type = self._types = self._type_ids = \
                self._positions = self._orientations = self._velocities = \
                self._mass = self._charge = self._diameter = \
                self._moment_inertia = self._angmom = None
            raise

    def set_dtype(self, value):
        """Change the data type of this trajectory.

        This function cannot be called if any frame
        is already loaded.

        :param value: The new data type value."""
        self._dtype = value
        for x in (self._positions, self._orientations, self._velocities,
                  self._mass, self._charge, self._diameter,
                  self._moment_inertia, self._angmom):
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

    @property
    def velocities(self):
        """Access the particle velocities as numpy array.

        :returns: particle velocities as (Nx3) array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        if getattr(self, '_velocities', None) is None:
            raise AttributeError('Velocities are not available for this '
                                 'trajectory.')
        return np.asarray(self._velocities, dtype=self._dtype)

    @property
    def mass(self):
        """Access the particle mass as numpy array.

        :returns: particle mass as (N) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        if getattr(self, '_mass', None) is None:
            raise AttributeError('Masses are not available for this '
                                 'trajectory.')
        return np.asarray(self._mass, dtype=self._dtype)

    @property
    def charge(self):
        """Access the particle charge as numpy array.

        :returns: particle charge as (N) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        if getattr(self, '_charge', None) is None:
            raise AttributeError('Charges are not available for this '
                                 'trajectory.')
        return np.asarray(self._charge, dtype=self._dtype)

    @property
    def diameter(self):
        """Access the particle diameter as numpy array.

        :returns: particle diameter as (N) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        if getattr(self, '_diameter', None) is None:
            raise AttributeError('Diameters are not available for this '
                                 'trajectory.')
        return np.asarray(self._diameter, dtype=self._dtype)

    @property
    def moment_inertia(self):
        """Access the particle principal moment of inertia components as
        numpy array.

        :returns: particle principal moment of inertia components as (Nx3)
                  element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        if getattr(self, '_moment_inertia', None) is None:
            raise AttributeError('Moments of inertia are not available for '
                                 'this trajectory.')
        return np.asarray(self._moment_inertia, dtype=self._dtype)

    @property
    def angmom(self):
        """Access the particle angular momenta as numpy array.

        :returns: particle angular momenta quaternions as (Nx4) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assertarrays_loaded()
        if getattr(self, '_angmom', None) is None:
            raise AttributeError('Angular momenta are not available for this '
                                 'trajectory.')
        return np.asarray(self._angmom, dtype=self._dtype)

def _regularize_box(positions, velocities,
                    orientations, angmom,
                    box_matrix, dtype=None, dimensions=3):
    """ Convert box into a right-handed coordinate frame with
    only upper triangular entries. Also convert corresponding
    positions and orientations."""
    # First use QR decomposition to compute the new basis
    Q, R = np.linalg.qr(box_matrix)
    Q = Q.astype(dtype)
    R = R.astype(dtype)

    if not np.allclose(Q[:dimensions, :dimensions], np.eye(dimensions)):
        # Since we'll be performing a quaternion operation,
        # we have to ensure that Q is a pure rotation
        sign = np.linalg.det(Q)
        Q = Q*sign
        R = R*sign

        # Now we have to ensure that the box is right-handed. We
        # do this as a second step to avoid introducing reflections
        # into the rotation matrix before making the quaternion
        signs = np.diag(np.diag(np.where(R < 0, -np.ones(R.shape), np.ones(R.shape))))
        box = R.dot(signs)

        # If Q is not the identity matrix, then we will be
        # changing data, so we have to copy. This only causes
        # actual failures for non-writeable GSD frames, but could
        # cause unexpected data corruption for other cases.

        # We rotate positions and velocities.
        # Since they are vectors, we can use the matrix directly.
        # Conveniently, instead of transposing Q we can just reverse
        # the order of multiplication here
        if positions is not None:
            positions = np.copy(positions).dot(Q).dot(signs)
        if velocities is not None:
            velocities = np.copy(velocities).dot(Q).dot(signs)

        # For orientations and angular momenta, we use the quaternion
        quat = rowan.from_matrix(Q.T)

        if orientations is not None:
            orientations = np.copy(orientations)
            for i in range(orientations.shape[0]):
                orientations[i, :] = rowan.multiply(quat, orientations[i, :])
        if angmom is not None:
            angmom = np.copy(angmom)
            for i in range(angmom.shape[0]):
                angmom[i, :] = rowan.multiply(quat, angmom[i, :])
    else:
        box = box_matrix

    # Construct the box
    Lx, Ly, Lz = np.diag(box).flatten().tolist()
    xy = box[0, 1]/Ly
    xz = box[0, 2]/Lz
    yz = box[1, 2]/Lz
    box = Box(Lx = Lx, Ly = Ly, Lz = Lz, xy = xy, xz = xz, yz = yz)
    return positions, velocities, orientations, angmom, box

def _generate_type_id_array(types, type_ids):
    "Generate type_id array."
    _type = sorted(set(t_ for t in types for t_ in t))
    for i, t in enumerate(types):
        for j, t_ in enumerate(t):
            type_ids[i][j] = _type.index(t_)
    return _type


def copyto_hoomd_blue_snapshot(frame, snapshot):
    "Copy the frame into a HOOMD-blue snapshot."
    N = len(frame.types)
    for attr in ARRAY_PROPERTIES:
        frameattr = getattr(frame, attr, None)
        if frameattr is not None:
            np.copyto(getattr(snapshot.particles, HOOMD_SNAPSHOT_PROPERTY_MAP.get(attr, attr)), frameattr)
        else:
            _make_default_array(attr, (N,))
    return snapshot


def copyfrom_hoomd_blue_snapshot(frame, snapshot):
    """"Copy the HOOMD-blue snapshot into the frame.

    Note that only the properties listed below will be copied.
    """
    frame.box.__dict__ = snapshot.box.__dict__
    particle_types = list(set(snapshot.particles.types))
    snap_types = [particle_types[i] for i in snapshot.particles.typeid]
    frame.types = snap_types
    for attr in ARRAY_PROPERTIES:
        setattr(frame, attr, getattr(snapshot.particles, HOOMD_SNAPSHOT_PROPERTY_MAP.get(attr, attr)))
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
