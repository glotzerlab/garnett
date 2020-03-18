# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""Trajectories are the path that objects follow
as affected by external forces.

The trajectory module provides classes to store discretized
trajectories."""

import logging
import deprecation
from collections import OrderedDict

import numpy as np
import rowan
from .version import __version__

from .shapes import SphereShape, ConvexPolyhedronShape, \
    ConvexSpheropolyhedronShape, GeneralPolyhedronShape, PolygonShape, \
    SpheropolygonShape, SphereUnionShape


logger = logging.getLogger(__name__)

DEFAULT_DTYPE = np.float32

# Scalar/per-frame properties
FRAME_PROPERTIES = {
    'box': object,
    'N': np.uint,
}

# Properties of length T (number of types)
TYPE_PROPERTIES = {
    'types': str,
    'type_shapes': object,
}

# Properties of length N (number of particles)
PARTICLE_PROPERTIES = {
    'typeid': np.uint,
    'position': DEFAULT_DTYPE,
    'orientation': DEFAULT_DTYPE,
    'velocity': DEFAULT_DTYPE,
    'mass': DEFAULT_DTYPE,
    'charge': DEFAULT_DTYPE,
    'diameter': DEFAULT_DTYPE,
    'moment_inertia': DEFAULT_DTYPE,
    'angmom': DEFAULT_DTYPE,
    'image': np.int_,
}

TRAJECTORY_PROPERTIES = {
    **FRAME_PROPERTIES,
    **TYPE_PROPERTIES,
    **PARTICLE_PROPERTIES
}


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
        return "Box(Lx={Lx}, Ly={Ly}, Lz={Lz}, "\
            "xy={xy}, xz={xz}, yz={yz}, dimensions={dimensions})".format(
                **self.__dict__)

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


class _FrameData(object):
    """One _FrameData instance manages the data of one frame in a trajectory."""

    def __init__(self):
        self.box = None
        "Instance of :class:`~.Box`"
        self.types = None
        "T array of type names represented as strings."
        self.type_shapes = None
        "T array of Shape objects."
        self.typeid = None
        "N array of type indices for N particles."
        self.position = None
        "Nx3 array of coordinates for N particles in 3 dimensions."
        self.orientation = None
        "Nx4 array of rotational coordinates for N particles represented as quaternions."
        self.velocity = None
        "Nx3 array of velocities for N particles in 3 dimensions."
        self.mass = None
        "Nx1 array of masses for N particles."
        self.charge = None
        "Nx1 array of charges for N particles."
        self.diameter = None
        "Nx1 array of diameters for N particles."
        self.moment_inertia = None
        "Nx3 array of principal moments of inertia for N particles in 3 dimensions."
        self.angmom = None
        "Nx4 array of angular momenta for N particles represented as quaternions."
        self.image = None
        "Nx3 array of periodic images for N particles in 3 dimensions."
        self.data = None
        "A dictionary of lists for each attribute."
        self.data_keys = None
        "A list of strings, where each string represents one attribute."
        self.view_rotation = None
        "A quaternion specifying a rotation that should be applied for visualization."

    def __len__(self):
        return len(self.position)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        else:  # rigorous comparison required
            return self.box == other.box \
                and self.types == other.types \
                and np.array_equal(self.typeid, other.typeid) \
                and np.array_equal(self.position, other.position) \
                and np.array_equal(self.orientation, other.orientation) \
                and np.array_equal(self.velocity, other.velocity) \
                and np.array_equal(self.mass, other.mass) \
                and np.array_equal(self.charge, other.charge) \
                and np.array_equal(self.diameter, other.diameter) \
                and np.array_equal(self.moment_inertia, other.moment_inertia) \
                and np.array_equal(self.angmom, other.angmom) \
                and np.array_equal(self.image, other.image) \
                and self.data == other.data \
                and self.type_shapes == other.type_shapes

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "Frame(N={})".format(len(self))

    def __repr__(self):
        return str(self)


class _RawFrameData(object):
    """Class to capture unprocessed frame data during parsing.

    All matrices are NumPy arrays."""

    def __init__(self):
        # 3x3 matrix (not required to be upper-triangular)
        self.box = None
        self.box_dimensions = 3
        self.types = list()                         # T
        self.type_shapes = list()                   # T
        self.typeid = list()                        # N
        self.position = list()                      # Nx3
        self.orientation = list()                   # Nx4
        self.velocity = list()                      # Nx3
        self.mass = list()                          # Nx1
        self.charge = list()                        # Nx1
        self.diameter = list()                      # Nx1
        self.moment_inertia = list()                # Nx3
        self.angmom = list()                        # Nx4
        self.image = list()                         # Nx3
        # A dictionary of lists for each attribute
        self.data = None
        self.data_keys = None                       # A list of strings
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
        self._frame_data = None
        self._dtype = dtype

    def _raise_attributeerror(self, attr):
        value = getattr(self._frame_data, attr, None)
        if value is None:
            raise AttributeError('{} not available for this frame'.format(attr))
        else:
            return value

    def _validate_input_array(self, value, dim, nelem=None, dtype=None):
        if dtype is None:
            dtype = self._dtype
        try:
            value = np.asarray(value, dtype=dtype)
        except ValueError:
            raise ValueError("This property can only be set to values compatible with {}.".format(dtype))
        if np.issubdtype(dtype, np.number) and not np.all(np.isfinite(value)):
            raise ValueError("Property being set must all be finite numbers.")
        elif len(value.shape) != dim:
            raise ValueError("Input array must be {}-dimensional.".format(dim))
        elif dim == 2 and value.shape[1] != nelem:
            raise ValueError("Input array must be of shape (N, {}) where N is the number of particles.".format(nelem))
        return value

    @staticmethod
    def _raw_frame_data_to_frame_data(raw_frame, dtype=None):
        """Generate a _FrameData object from a _RawFrameData object.

        This method performs some normalization and validation on raw input data.
        """
        N = len(raw_frame.position)
        ret = _FrameData()

        mapping = dict()
        for prop, dtype_ in PARTICLE_PROPERTIES.items():
            if dtype_ == DEFAULT_DTYPE:
                dtype_ = dtype
            mapping[prop] = np.asarray(getattr(raw_frame, prop), dtype=dtype_)
            if len(mapping[prop]) == 0:
                mapping[prop] = None

        assert raw_frame.box is not None
        if isinstance(raw_frame.box, Box):
            raw_frame.box_dimensions = raw_frame.box.dimensions
            raw_frame.box = np.asarray(raw_frame.box.get_box_matrix(), dtype=dtype)
        box_dimensions = getattr(raw_frame, 'box_dimensions', 3)
        mapping['position'], mapping['velocity'], mapping['orientation'],\
            mapping['angmom'], ret.box = _regularize_box(mapping['position'],
                                                         mapping['velocity'],
                                                         mapping['orientation'],
                                                         mapping['angmom'],
                                                         raw_frame.box,
                                                         dtype,
                                                         box_dimensions)
        ret.types = raw_frame.types
        ret.type_shapes = raw_frame.type_shapes
        ret.typeid = raw_frame.typeid
        for prop in PARTICLE_PROPERTIES:
            setattr(ret, prop, mapping[prop])
        ret.data = raw_frame.data
        ret.data_keys = raw_frame.data_keys
        ret.view_rotation = raw_frame.view_rotation
        # validate data
        for prop in PARTICLE_PROPERTIES:
            if getattr(ret, prop) is not None:
                assert N == len(getattr(ret, prop))
        return ret

    def loaded(self):
        "Returns True if the frame is loaded into memory."
        return self._frame_data is not None

    def load(self):
        "Load the frame into memory."
        if self._frame_data is None:
            logger.debug("Loading frame.")
            self._frame_data = self._raw_frame_data_to_frame_data(self.read(), dtype=self._dtype)

    def unload(self):
        """Unload the frame from memory.

        Use this method carefully.
        This method removes the frame reference to the frame data,
        however any other references that may still exist, will
        prevent a removal of said data from memory."""
        logger.debug("Removing frame data reference.")
        self._frame_data = None

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
        return self.N

    def __eq__(self, other):
        self.load()
        other.load()
        return self._frame_data == other._frame_data

    def __ne__(self, other):
        return not self.__eq__(other)

    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="Use to_hoomd_snapshot with no argument.")
    def make_snapshot(self):
        "Create a HOOMD-blue snapshot object from this frame."
        return self.to_hoomd_snapshot()

    def to_hoomd_snapshot(self, snapshot=None):
        "Copy this frame to a HOOMD-blue snapshot."
        self.load()
        if snapshot is None:
            try:
                from hoomd import data
            except ImportError:
                try:
                    # Try importing from hoomd 1.x
                    from hoomd_script import data
                except ImportError:
                    raise ImportError('hoomd')
            box = data.boxdim(
                Lx=self.box.Lx,
                Ly=self.box.Ly,
                Lz=self.box.Lz,
                xy=self.box.xy,
                xz=self.box.xz,
                yz=self.box.yz,
                dimensions=self.box.dimensions,
            )
            snapshot = data.make_snapshot(
                N=len(self),
                box=box,
                particle_types=self.types,
            )
            np.copyto(
                snapshot.particles.typeid,
                np.array(self.typeid, dtype=snapshot.particles.typeid.dtype)
            )
        for prop in PARTICLE_PROPERTIES:
            try:
                np.copyto(getattr(snapshot.particles, prop), getattr(self, prop))
            except AttributeError:
                pass
        return snapshot

    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="Use to_hoomd_snapshot.")
    def copyto_snapshot(self, snapshot):
        "Copy this frame to a HOOMD-blue snapshot."
        return self.to_hoomd_snapshot(snapshot)

    @classmethod
    def from_hoomd_snapshot(cls, snapshot):
        """Constructs a Frame object from a HOOMD-blue snapshot.

        :param snapshot: A HOOMD snapshot.
        """
        raw_frame = _RawFrameData()
        raw_frame.box = Box(
            Lx=snapshot.box.Lx,
            Ly=snapshot.box.Ly,
            Lz=snapshot.box.Lz,
            xy=snapshot.box.xy,
            xz=snapshot.box.xz,
            yz=snapshot.box.yz,
            dimensions=snapshot.box.dimensions,
        )
        for prop in {**TYPE_PROPERTIES, **PARTICLE_PROPERTIES}:
            try:
                setattr(raw_frame, prop, getattr(snapshot.particles, prop))
            except AttributeError:
                pass

        frame = cls()
        frame._frame_data = cls._raw_frame_data_to_frame_data(raw_frame)
        return frame

    def to_plato_scene(self, backend, scene=None):
        """Create a plato scene from this frame.

        :param backend: Backend name to use with plato. The backend must
                        support all primitives corresponding to shapes defined
                        in this frame.
        :type backend: str
        :param scene: Scene object to render into. By default, a new scene is
                      created.
        :type scene: :class:`plato.draw.Scene`
        """
        try:
            import importlib
            backend = importlib.import_module('plato.draw.{}'.format(backend))
        except ImportError:
            raise ImportError(
                'Backend plato.draw.{} could not be imported.'.format(backend))

        prims = []

        def make_default_colors(size):
            return np.array([[0.5, 0.5, 0.5, 1]] * size)

        # Create box primitive
        box = self.box
        if self.box.dimensions == 2:
            box.Lz = 0
        prims.append(backend.Box.from_box(box, color=(0, 0, 0, 1)))

        # Create a shape primitive for each type
        for typeid, type_shape in enumerate(self.type_shapes):
            subset = np.where(np.asarray(self.typeid) == typeid)[0]
            N_prim = len(subset)
            dimensions = self.box.dimensions

            if isinstance(type_shape, SphereShape):
                if dimensions == 3:
                    prim = backend.Spheres(
                        positions=self.position[subset],
                        colors=make_default_colors(N_prim),
                        radii=[0.5 * type_shape['diameter']] * N_prim,
                    )
                else:
                    prim = backend.Disks(
                        positions=self.position[subset, :2],
                        colors=make_default_colors(N_prim),
                        radii=[0.5 * type_shape['diameter']] * N_prim,
                    )
            elif isinstance(type_shape, SphereUnionShape):
                if dimensions == 3:
                    prim = backend.SphereUnions(
                        positions=self.position[subset],
                        orientations=self.orientation[subset],
                        colors=make_default_colors(len(type_shape['centers'])),
                        points=type_shape['centers'],
                        radii=[0.5 * d for d in type_shape['diameters']],
                    )
                else:
                    prim = backend.DiskUnions(
                        positions=self.position[subset, :2],
                        orientations=self.orientation[subset],
                        colors=make_default_colors(len(type_shape['centers'])),
                        points=[c[:2] for c in type_shape['centers']],
                        radii=[0.5 * d for d in type_shape['diameters']],
                    )
            elif isinstance(type_shape, ConvexPolyhedronShape):
                prim = backend.ConvexPolyhedra(
                    positions=self.position[subset],
                    orientations=self.orientation[subset],
                    colors=make_default_colors(N_prim),
                    vertices=type_shape['vertices'],
                )
            elif isinstance(type_shape, ConvexSpheropolyhedronShape):
                prim = backend.ConvexSpheropolyhedra(
                    positions=self.position[subset],
                    orientations=self.orientation[subset],
                    colors=make_default_colors(N_prim),
                    vertices=type_shape['vertices'],
                    radius=type_shape['rounding_radius'],
                )
            elif isinstance(type_shape, GeneralPolyhedronShape):
                prim = backend.Mesh(
                    positions=self.position[subset],
                    orientations=self.orientation[subset],
                    colors=make_default_colors(len(type_shape['vertices'])),
                    vertices=type_shape['vertices'],
                    indices=type_shape['faces'],
                    shape_colors=make_default_colors(N_prim),
                )
            elif isinstance(type_shape, PolygonShape):
                prim = backend.Polygons(
                    positions=self.position[subset, :2],
                    orientations=self.orientation[subset],
                    colors=make_default_colors(N_prim),
                    vertices=type_shape['vertices'],
                )
            elif isinstance(type_shape, SpheropolygonShape):
                prim = backend.Spheropolygons(
                    positions=self.position[subset, :2],
                    orientations=self.orientation[subset],
                    colors=make_default_colors(N_prim),
                    vertices=type_shape['vertices'],
                    radius=type_shape['rounding_radius'],
                )
            else:
                logger.warning('Unsupported shape: {}'.format(type_shape))
                continue
            prims.append(prim)

        if scene is None:
            scene = backend.Scene(prims)
        else:
            for prim in prims:
                scene.add_primitive(prim)

        return scene

    @property
    def N(self):
        "Number of particles."
        self.load()
        return len(self._frame_data)

    @property
    def box(self):
        "Instance of :class:`~.Box`"
        self.load()
        return self._frame_data.box

    @box.setter
    def box(self, value):
        self.load()
        self._frame_data.box = value

    @property
    def types(self):
        "T array of type names represented as strings."
        self.load()
        return self._raise_attributeerror('types')

    @types.setter
    def types(self, value):
        value = self._validate_input_array(value, dim=1, dtype=TYPE_PROPERTIES['types'])
        self.load()
        self._frame_data.types = value

    @property
    def type_shapes(self):
        "T list of shape definitions."
        self.load()
        return self._raise_attributeerror('type_shapes')

    @type_shapes.setter
    def type_shapes(self, value):
        value = self._validate_input_array(value, dim=1, dtype=TYPE_PROPERTIES['type_shapes'])
        self.load()
        self._frame_data.type_shapes = value

    @property
    def typeid(self):
        "N array of type indices for N particles."
        self.load()
        return self._frame_data.typeid

    @typeid.setter
    def typeid(self, value):
        value = self._validate_input_array(value, dim=1, dtype=PARTICLE_PROPERTIES['typeid'])
        self.load()
        self._frame_data.typeid = value

    @property
    def position(self):
        "Nx3 array of coordinates for N particles in 3 dimensions."
        self.load()
        return self._raise_attributeerror('position')

    @position.setter
    def position(self, value):
        # Various sanity checks
        value = self._validate_input_array(value, dim=2, nelem=3)
        self.load()
        self._frame_data.position = value

    @property
    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="This property is deprecated, use position instead.")
    def positions(self):
        """
        Nx3 array of coordinates for N particles in 3 dimensions.
        Deprecated alias for position.
        """
        return self.position

    @positions.setter
    def positions(self, value):
        # Various sanity checks
        value = self._validate_input_array(value, dim=2, nelem=3)
        self.load()
        self._frame_data.position = value

    @property
    def orientation(self):
        "Nx4 array of rotational coordinates for N particles represented as quaternions."
        self.load()
        return self._raise_attributeerror('orientation')

    @orientation.setter
    def orientation(self, value):
        value = self._validate_input_array(value, dim=2, nelem=4)
        self.load()
        self._frame_data.orientation = value

    @property
    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="This property is deprecated, use orientation instead.")
    def orientations(self):
        """
        Nx4 array of rotational coordinates for N particles represented as quaternions.
        Deprecated alias for orientation.
        """
        return self.orientation

    @orientations.setter
    def orientations(self, value):
        value = self._validate_input_array(value, dim=2, nelem=4)
        self.load()
        self._frame_data.orientation = value

    @property
    def velocity(self):
        "Nx3 array of velocities for N particles in 3 dimensions."
        self.load()
        return self._raise_attributeerror('velocity')

    @velocity.setter
    def velocity(self, value):
        value = self._validate_input_array(value, dim=2, nelem=3)
        self.load()
        self._frame_data.velocity = value

    @property
    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="This property is deprecated, use velocity instead.")
    def velocities(self):
        """
        Nx3 array of velocities for N particles in 3 dimensions.
        Deprecated alias for velocity.
        """
        return self.velocity

    @velocities.setter
    def velocities(self, value):
        value = self._validate_input_array(value, dim=2, nelem=3)
        self.load()
        self._frame_data.velocity = value

    @property
    def mass(self):
        "Nx1 array of masses for N particles."
        self.load()
        return self._raise_attributeerror('mass')

    @mass.setter
    def mass(self, value):
        value = self._validate_input_array(value, dim=1)
        self.load()
        self._frame_data.mass = value

    @property
    def charge(self):
        "Nx1 array of charges for N particles."
        self.load()
        return self._raise_attributeerror('charge')

    @charge.setter
    def charge(self, value):
        value = self._validate_input_array(value, dim=1)
        self.load()
        self._frame_data.charge = value

    @property
    def diameter(self):
        "Nx1 array of diameters for N particles."
        self.load()
        return self._raise_attributeerror('diameter')

    @diameter.setter
    def diameter(self, value):
        value = self._validate_input_array(value, dim=1)
        self.load()
        self._frame_data.diameter = value

    @property
    def moment_inertia(self):
        "Nx3 array of principal moments of inertia for N particles in 3 dimensions."
        self.load()
        return self._raise_attributeerror('moment_inertia')

    @moment_inertia.setter
    def moment_inertia(self, value):
        ndof = self.box.dimensions * (self.box.dimensions - 1) / 2
        self._validate_input_array(value, dim=2, nelem=ndof)
        self.load()
        self._frame_data.moment_inertia = value

    @property
    def angmom(self):
        "Nx4 array of angular momenta for N particles represented as quaternions."
        self.load()
        return self._raise_attributeerror('angmom')

    @angmom.setter
    def angmom(self, value):
        value = self._validate_input_array(value, dim=2, nelem=4)
        self.load()
        self._frame_data.angmom = value

    @property
    def image(self):
        "Nx3 array of periodic images for N particles in 3 dimensions."
        self.load()
        return self._raise_attributeerror('image')

    @image.setter
    def image(self, value):
        value = self._validate_input_array(value, dim=2, nelem=3, dtype=PARTICLE_PROPERTIES['image'])
        self.load()
        self._frame_data.image = value

    @property
    def data(self):
        "A dictionary of lists for each attribute."
        self.load()
        return self._frame_data.data

    @data.setter
    def data(self, value):
        self.load()
        self._frame_data.data = value

    @property
    def data_keys(self):
        "A list of strings, where each string represents one attribute."
        self.load()
        return self._frame_data.data_keys

    @data_keys.setter
    def data_keys(self, value):
        self.load()
        self._frame_data.data_keys = value

    @property
    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details=("This property is deprecated, use type_shapes instead. "
                                     "Until its removal, shapedef keys should not be individually "
                                     "set, only the entire dictionary at once."))
    def shapedef(self):
        "An ordered dictionary of instances of :class:`~.shapes.Shape`."
        types = self.types
        type_shapes = self.type_shapes
        if len(types) != len(type_shapes):
            raise AttributeError('Number of types and type_shapes is inconsistent.')
        else:
            return OrderedDict(zip(types, type_shapes))

    @shapedef.setter
    def shapedef(self, value):
        self.types = list(value.keys())
        self.type_shapes = list(value.values())

    @property
    def view_rotation(self):
        "A quaternion specifying a rotation that should be applied for visualization."
        self.load()
        return self._frame_data.view_rotation


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
            for prop in TRAJECTORY_PROPERTIES:
                prop_key = '_' + prop
                if getattr(self, prop_key) is not None:
                    setattr(traj, prop_key, getattr(self, prop_key)[index])
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

    Trajectory data can either be accessed as coherent NumPy arrays:

    .. code::

        traj.load_arrays()
        M = len(traj)
        traj.N             # M
        traj.position      # MxNx3
        traj.orientation   # MxNx4
        traj.typeid        # MxN

    or by individual frames:

    .. code::

        first_frame = traj[0]
        last_frame = traj[-1]
        n_th_frame = traj[n]

        first_frame.position      # Nx3
        first_frame.orientation   # Nx4
        first_frame.types         # Nx1

    You can iterate through individual frames:

    .. code::

        for frame in trajectory:
            print(frame.position)

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
        self._box = None
        self._N = None
        self._types = None
        self._type_shapes = None
        self._typeid = None
        self._position = None
        self._orientation = None
        self._velocity = None
        self._mass = None
        self._charge = None
        self._diameter = None
        self._moment_inertia = None
        self._angmom = None
        self._image = None

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
        return any(getattr(self, '_' + key) is not None for key in TRAJECTORY_PROPERTIES)

    def _assert_loaded(self):
        "Raises a RuntimeError if trajectory is not loaded."
        if not self.loaded():
            raise RuntimeError("Trajectory not loaded! Use load().")

    def _assert_arrays_loaded(self):
        "Raises a RuntimeError if trajectory arrays are not loaded."
        if not self.arrays_loaded():
            raise RuntimeError(
                "Trajectory arrays not loaded! Use load_arrays() or load().")

    def _check_nonempty_property(self, attr):
        value = getattr(self, attr, None)
        if value is None:
            raise AttributeError('{} not available for this trajectory'.format(attr[1:]))
        else:
            return value

    def _max_N(self):
        "Returns the size of the largest frame within this trajectory."
        return max((len(f) for f in self.frames))

    def load_arrays(self):
        """Load all available trajectory properties into memory.

        After calling this function, trajectory properties can be accessed as
        coherent NumPy arrays:

        .. code::

            traj.load_arrays()
            traj.N             # M -- frame sizes
            traj.position      # MxNx3
            traj.orientation   # MxNx4
            traj.typeid        # MxN

        .. note::

            It is not necessary to call this function again when
            accessing sub trajectories:

            .. code::

                traj.load_arrays()
                sub_traj = traj[m:n]
                sub_traj.position

            However, it may be more efficient to call :meth:`~.load_arrays`
            only for the sub trajectory if other data is not of interest:

            .. code::

                sub_traj = traj[m:n]
                sub_traj.load_arrays()
                sub_traj.position
        """
        # Set up dictionary of properties with a list of values for each frame.
        props = {prop: [None] * len(self) for prop in TRAJECTORY_PROPERTIES}

        # Copy attributes from frames into props.
        for i, frame in enumerate(self.frames):
            for prop in TRAJECTORY_PROPERTIES:
                props[prop][i] = getattr(frame, prop, None)

        # Build NumPy arrays for properties with no missing values (i.e. None).
        for prop, dtype_ in TRAJECTORY_PROPERTIES.items():
            if any(p is None for p in props[prop]):
                # If the list contains a None value, set property to None
                # in order for AttributeError to be raised properly.
                props[prop] = None
            else:
                try:
                    props[prop] = np.asarray(props[prop], dtype=dtype_)
                except (TypeError, ValueError):
                    props[prop] = np.asarray(props[prop])

        # Copy props data into trajectory's hidden attributes.
        try:
            for prop in TRAJECTORY_PROPERTIES:
                prop_key = '_' + prop
                setattr(self, prop_key, props[prop])
        except Exception:
            # Ensure consistent error state by resetting all properties
            for prop in TRAJECTORY_PROPERTIES:
                prop_key = '_' + prop
                setattr(self, prop_key, None)
            raise

    def set_dtype(self, value):
        """Change the data type of this trajectory.

        This function cannot be called if any frame
        is already loaded.

        :param value: The new data type value."""
        self._dtype = value
        for x in (self._position, self._orientation, self._velocity,
                  self._mass, self._charge, self._diameter,
                  self._moment_inertia, self._angmom):
            if x is not None:
                x = x.astype(value)
        for frame in self.frames:
            frame.dtype = value

    @property
    def box(self):
        """Access the frame boxes as a NumPy array.

        :returns: frame boxes as an (M) element array
        :rtype: :class:`numpy.ndarray` (dtype= :class:`numpy.object_`)
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_box')

    @property
    def N(self):
        """Access the frame sizes as a NumPy array.

        Mostly important when the trajectory has varying size.

        .. code::

            pos_i = traj.position[i][0:traj.N[i]]

        :returns: frame sizes as array with length M
        :rtype: :class:`numpy.ndarray` (dtype= :class:`numpy.int_`)
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_N')

    @property
    def types(self):
        """List of type names ordered by type_id.

        :returns: particles type names as (MxT) array
        :rtype: :class:`numpy.ndarray` (dtype= :class:`numpy.str_` )
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_types')

    @property
    def typeid(self):
        """Access the particle type ids as a NumPy array.

        See also: :attr:`~.Trajectory.type`

        :returns: particle type ids as (MxN) array.
        :rtype: :class:`numpy.ndarray` (dtype= :class:`numpy.int_` )
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_typeid')

    @property
    def position(self):
        """Access the particle positions as a NumPy array.

        :returns: particle positions as (Nx3) array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_position')

    @property
    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="This property is deprecated, use position instead.")
    def positions(self):
        """Deprecated alias for position."""
        return self.position

    @property
    def orientation(self):
        """Access the particle orientations as a NumPy array.

        Orientations are stored as quaternions.

        :returns: particle orientations as (Nx4) array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_orientation')

    @property
    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="This property is deprecated, use orientation instead.")
    def orientations(self):
        """Deprecated alias for orientation."""
        return self.orientation

    @property
    def velocity(self):
        """Access the particle velocities as a NumPy array.

        :returns: particle velocities as (Nx3) array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_velocity')

    @property
    @deprecation.deprecated(deprecated_in="0.7.0",
                            removed_in="0.8.0",
                            current_version=__version__,
                            details="This property is deprecated, use velocity instead.")
    def velocities(self):
        """Deprecated alias for velocity."""
        return self.velocity

    @property
    def mass(self):
        """Access the particle mass as a NumPy array.

        :returns: particle mass as (N) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_mass')

    @property
    def charge(self):
        """Access the particle charge as a NumPy array.

        :returns: particle charge as (N) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_charge')

    @property
    def diameter(self):
        """Access the particle diameter as a NumPy array.

        :returns: particle diameter as (N) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_diameter')

    @property
    def moment_inertia(self):
        """Access the particle principal moment of inertia components as a
        NumPy array.

        :returns: particle principal moment of inertia components as (Nx3)
                  element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_moment_inertia')

    @property
    def angmom(self):
        """Access the particle angular momenta as a NumPy array.

        :returns: particle angular momenta quaternions as (Nx4) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_angmom')

    @property
    def image(self):
        """Access the particle periodic images as a NumPy array.

        :returns: particle periodic images as (Nx3) element array
        :rtype: :class:`numpy.ndarray`
        :raises RuntimeError: When accessed before
            calling :meth:`~.load_arrays` or
            :meth:`~.Trajectory.load`."""
        self._assert_arrays_loaded()
        return self._check_nonempty_property('_image')


def _regularize_box(position, velocity,
                    orientation, angmom,
                    box_matrix, dtype=None, dimensions=3):
    """Convert box into a right-handed coordinate frame with
    only upper triangular entries. Also convert corresponding
    positions and orientations."""
    # First use QR decomposition to compute the new basis
    Q, R = np.linalg.qr(box_matrix)
    Q = Q.astype(dtype)
    R = R.astype(dtype)

    if not np.allclose(Q[:dimensions, :dimensions], np.eye(dimensions)):
        # If Q is not the identity matrix, then we will be
        # changing data, so we have to copy. This only causes
        # actual failures for non-writeable GSD frames, but could
        # cause unexpected data corruption for other cases
        position = np.copy(position)
        if orientation is not None:
            orientation = np.copy(orientation)
        if velocity is not None:
            velocity = np.copy(velocity)
        if angmom is not None:
            angmom = np.copy(angmom)

        # Since we'll be performing a quaternion operation,
        # we have to ensure that Q is a pure rotation
        sign = np.linalg.det(Q)
        Q = Q*sign
        R = R*sign

        # First rotate positions, velocities.
        # Since they are vectors, we can use the matrix directly.
        # Conveniently, instead of transposing Q we can just reverse
        # the order of multiplication here
        position = position.dot(Q)
        if velocity is not None:
            velocity = velocity.dot(Q)

        # For orientations and angular momenta, we use the quaternion
        quat = rowan.from_matrix(Q.T)
        if orientation is not None:
            for i in range(orientation.shape[0]):
                orientation[i, :] = rowan.multiply(quat, orientation[i, :])
        if angmom is not None:
            for i in range(angmom.shape[0]):
                angmom[i, :] = rowan.multiply(quat, angmom[i, :])

        # Now we have to ensure that the box is right-handed. We
        # do this as a second step to avoid introducing reflections
        # into the rotation matrix before making the quaternion
        signs = np.diag(np.diag(np.where(R < 0, -np.ones(R.shape), np.ones(R.shape))))
        box = R.dot(signs)
        position = position.dot(signs)
        if velocity is not None:
            velocity = velocity.dot(signs)
    else:
        box = box_matrix

    # Construct the box
    Lx, Ly, Lz = np.diag(box).flatten().tolist()
    xy = box[0, 1]/Ly
    xz = box[0, 2]/Lz
    yz = box[1, 2]/Lz
    box = Box(Lx=Lx, Ly=Ly, Lz=Lz, xy=xy, xz=xz, yz=yz, dimensions=dimensions)
    return position, velocity, orientation, angmom, box


def _generate_types_typeid(type_strings):
    """Generate types and typeid from list of type strings."""
    types = []
    typeid = []
    for name in map(str, type_strings):
        if name not in types:
            types.append(name)
        typeid.append(types.index(name))
    types = np.asarray(types, dtype=str)
    typeid = np.asarray(typeid, dtype=np.uint)
    return types, typeid


@deprecation.deprecated(deprecated_in="0.7.0",
                        removed_in="0.8.0",
                        current_version=__version__,
                        details="This function is deprecated.")
def copyto_hoomd_blue_snapshot(frame, snapshot):
    "Copy the frame into a HOOMD-blue snapshot."
    return frame.to_hoomd_snapshot(snapshot)


@deprecation.deprecated(deprecated_in="0.7.0",
                        removed_in="0.8.0",
                        current_version=__version__,
                        details="This function is deprecated.")
def copyfrom_hoomd_blue_snapshot(frame, snapshot):
    """"Copy the HOOMD-blue snapshot into the frame."""
    frame = Frame.from_hoomd_snapshot(snapshot)
    return frame


@deprecation.deprecated(deprecated_in="0.7.0",
                        removed_in="0.8.0",
                        current_version=__version__,
                        details="This function is deprecated.")
def make_hoomd_blue_snapshot(frame):
    "Create a HOOMD-blue snapshot from the frame instance."
    return frame.to_hoomd_snapshot()
