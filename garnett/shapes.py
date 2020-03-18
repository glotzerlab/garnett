# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

"""Abstract shape definitions used to read/write particle shapes."""

import json
import logging
import numpy as np

__all__ = [
    'FallbackShape',
    'Shape',
    'SphereShape',
    'ArrowShape',
    'SphereUnionShape',
    'PolygonShape',
    'SpheropolygonShape',
    'ConvexPolyhedronShape',
    'ConvexPolyhedronUnionShape',
    'ConvexSpheropolyhedronShape',
    'GeneralPolyhedronShape',
    'EllipsoidShape',
]

logger = logging.getLogger(__name__)

SHAPE_DEFAULT_COLOR = '005984FF'


class _NumpyEncoder(json.JSONEncoder):
    """JSONEncoder class converting NumPy arrays to lists."""
    def default(self, obj):
        if isinstance(obj, np.number):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def _json_sanitize(func):
    """Decorator ensuring that returned data is JSON-encodable."""
    def wrapper(*args, **kwargs):
        data = func(*args, **kwargs)
        return json.loads(json.dumps(data, cls=_NumpyEncoder))
    # Ensure that the decorated function inherits the intended docstring.
    wrapper.__doc__ = func.__doc__
    return wrapper


class FallbackShape(str):
    """This shape definition class is used when no specialized Shape class can be applied.

    The fallback shape definition is a string containing the definition."""
    pass


class Shape(object):
    """Parent class of all shape objects.

    :param shape_class:
        Shape class directive, used for POS format (default: :code:`None`).
    :type shape_class:
        str
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, shape_class=None, color=None):
        self.shape_class = shape_class
        self.color = color if color else SHAPE_DEFAULT_COLOR

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise KeyError(*e.args)

    @property
    def pos_string(self):
        return "{} {}".format(self.shape_class, self.color)

    @property
    @_json_sanitize
    def type_shape(self):
        return {"type": self.shape_class}

    def __str__(self):
        return json.dumps(self.type_shape)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.type_shape == other.type_shape


class SphereShape(Shape):
    """Shape class for spheres of a specified diameter.

    :param diameter:
        Diameter of the sphere.
    :type diameter:
        float
    :param orientable:
         Set to True for spheres with orientation (default: :code:`False`).
    :type orientable:
        bool
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, diameter, orientable=False, color=None):
        super(SphereShape, self).__init__(
            shape_class='sphere', color=color)
        self.diameter = diameter
        self.orientable = orientable

    @property
    def pos_string(self):
        return "{} {} {}".format(self.shape_class, self.diameter, self.color)

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

            >>> SphereShape(2.0).type_shape
            {'type': 'Sphere', 'diameter': 2.0}
        """
        return {'type': 'Sphere',
                'diameter': self.diameter}


class ArrowShape(Shape):
    """Shape class for arrows of a specified thickness.

    :param thickness:
        Thickness of the arrow.
    :type thickness:
        float
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, thickness=0.1, color=None):
        super(ArrowShape, self).__init__(
            shape_class='arrow', color=color)
        self.thickness = thickness

    @property
    def pos_string(self):
        return "{} {} {}".format(self.shape_class, self.thickness, self.color)


class SphereUnionShape(Shape):
    """Shape class for sphere unions, such as rigid bodies of many spheres.

    :param diameters:
        List of sphere diameters.
    :type diameters:
        list
    :param centers:
        List of 3D center vectors.
    :type centers:
        list
    :param colors:
        List of hexadecimal color strings in format :code:`RRGGBBAA` (default: :code:`None`).
    :type colors:
        list
    """

    def __init__(self, diameters, centers, colors=None):
        super(SphereUnionShape, self).__init__(
            shape_class='sphere_union', color='')
        self.diameters = diameters
        self.centers = centers
        self.colors = colors

    @property
    def pos_string(self):
        shape_def = '{} {} '.format(self.shape_class, len(self.centers))
        for d, p, c in zip(self.diameters, self.centers, self.colors):
            shape_def += '{0} '.format(d)
            shape_def += '{0} {1} {2} '.format(*p)
            shape_def += '{0} '.format(c)

        return shape_def

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

           >>> SphereUnionShape([0.5, 0.5, 0.5], [[0, 0, 1.0], [0, 1.0, 0], [1.0, 0, 0]]).type_shape
           {'type': 'SphereUnion', 'diameters': [0.5, 0.5, 0.5],
            'centers': [[0, 0, 1.0], [0, 1.0, 0], [1.0, 0, 0]]}
        """
        return {'type': 'SphereUnion',
                'diameters': self.diameters,
                'centers': self.centers}


class PolygonShape(Shape):
    """Shape class for polygons in a 2D plane.

    :param vertices:
        List of 2D vertex vectors.
    :type vertices:
        list
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, vertices, color=None):
        super(PolygonShape, self).__init__(
            shape_class='poly3d', color=color)
        self.vertices = vertices

    @property
    def pos_string(self):
        return "{} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join('{} {} 0'.format(v[0], v[1]) for v in self.vertices),
            self.color)

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

            >>> PolygonShape([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5]]).type_shape
            {'type': 'Polygon', 'rounding_radius': 0,
             'vertices': [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5]]}
        """
        return {'type': 'Polygon',
                'rounding_radius': 0,
                'vertices': self.vertices}


class SpheropolygonShape(Shape):
    """Shape class for rounded polygons in a 2D plane.

    :param vertices:
        List of 2D vertex vectors.
    :type vertices:
        list
    :param rounding_radius:
        Rounding radius applied to the spheropolygon (default: 0).
    :type rounding_radius:
        float
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, vertices, rounding_radius=0, color=None):
        super(SpheropolygonShape, self).__init__(
            shape_class='spoly3d', color=color)
        self.vertices = vertices
        self.rounding_radius = rounding_radius

    @property
    def pos_string(self):
        return "{} {} {} {} {}".format(
            self.shape_class,
            self.rounding_radius,
            len(self.vertices),
            ' '.join('{} {} 0'.format(v[0], v[1]) for v in self.vertices),
            self.color)

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

            >>> SpheropolygonShape([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5]], 0.1).type_shape
            {'type': 'Polygon', 'rounding_radius': 0.1,
             'vertices': [[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5]]}
        """
        return {'type': 'Polygon',
                'rounding_radius': self.rounding_radius,
                'vertices': self.vertices}


class ConvexPolyhedronShape(Shape):
    """Shape class for convex polyhedra.

    :param vertices:
        List of 3D vertex vectors.
    :type vertices:
        list
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, vertices, color=None):
        super(ConvexPolyhedronShape, self).__init__(
            shape_class='poly3d', color=color)
        self.vertices = vertices

    @property
    def pos_string(self):
        return "{} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            self.color)

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

            >>> ConvexPolyhedronShape([[0.5, 0.5, 0.5], [0.5, -0.5, -0.5],
                                       [-0.5, 0.5, -0.5], [-0.5, -0.5, 0.5]]).type_shape
            {'type': 'ConvexPolyhedron', 'rounding_radius': 0,
             'vertices': [[0.5, 0.5, 0.5], [0.5, -0.5, -0.5],
                          [-0.5, 0.5, -0.5], [-0.5, -0.5, 0.5]]}
        """
        return {'type': 'ConvexPolyhedron',
                'rounding_radius': 0,
                'vertices': self.vertices}


class ConvexPolyhedronUnionShape(Shape):
    """Shape class for unions of convex polyhedra.

    :param vertices:
        List of lists of 3D vertex vectors in particle coordinates (each
        polyhedron, each vertex).
    :type vertices:
        list
    :param centers:
        List of 3D polyhedra center vectors.
    :type centers:
        list
    :param orientations:
        Orientations of the polyhedra, as a list of quaternions.
    :type orientations:
        list
    :param colors:
        List of hexadecimal color strings in format :code:`RRGGBBAA` (default: :code:`None`).
    :type colors:
        list
    """

    def __init__(self, vertices, centers, orientations, colors=None):
        super(ConvexPolyhedronUnionShape, self).__init__(
            shape_class='poly3d_union', color='')
        self.vertices = vertices
        self.centers = centers
        self.orientations = orientations
        self.colors = colors

    @property
    def pos_string(self):
        shape_def = '{} {} '.format(self.shape_class, len(self.centers))
        for verts, p, q, c in zip(self.vertices, self.centers, self.orientations, self.colors):
            shape_def += '{0} '.format(len(verts))
            for v in verts:
                shape_def += '{0} {1} {2} '.format(*v)
            shape_def += '{0} {1} {2} '.format(*p)
            shape_def += '{0} {1} {2} {3} '.format(*q)
            shape_def += '{0} '.format(c)

        return shape_def


class ConvexSpheropolyhedronShape(Shape):
    """Shape class for a convex polyhedron extended by a rounding radius.

    :param vertices:
        List of 3D vertex vectors.
    :type vertices:
        list
    :param rounding_radius:
        Rounding radius applied to the spheropolyhedron (default: 0).
    :type rounding_radius:
        float
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, vertices, rounding_radius=0, color=None):
        super(ConvexSpheropolyhedronShape, self).__init__(
            shape_class='spoly3d', color=color)
        self.vertices = vertices
        self.rounding_radius = rounding_radius

    @property
    def pos_string(self):
        return "{} {} {} {} {}".format(
            self.shape_class,
            self.rounding_radius,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            self.color)

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

            >>> ConvexSpheropolyhedronShape([[0.5, 0.5, 0.5], [0.5, -0.5, -0.5],
                                             [-0.5, 0.5, -0.5], [-0.5, -0.5, 0.5]], 0.1).type_shape
            {'type': 'ConvexPolyhedron', 'rounding_radius': 0.1,
             'vertices': [[0.5, 0.5, 0.5], [0.5, -0.5, -0.5],
                          [-0.5, 0.5, -0.5], [-0.5, -0.5, 0.5]]}
        """
        return {'type': 'ConvexPolyhedron',
                'rounding_radius': self.rounding_radius,
                'vertices': self.vertices}


class GeneralPolyhedronShape(Shape):
    """Shape class for general polyhedra, such as arbitrary meshes.

    :param vertices:
        List of 3D vertex vectors.
    :type vertices:
        list
    :param faces:
        List of lists of integers representing vertex indices for each face.
    :type faces:
        list
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    :param facet_colors:
        List of hexadecimal color strings in format :code:`RRGGBBAA` for each facet (default: :code:`None`).
    :type facet_colors:
        list
    """

    def __init__(self, vertices, faces, color=None, facet_colors=None):
        super(GeneralPolyhedronShape, self).__init__(
            shape_class='polyV', color=color)
        self.vertices = vertices
        self.faces = faces
        self.facet_colors = facet_colors

    @property
    def pos_string(self):
        return "{} {} {} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            len(self.faces),
            ' '.join((str(fv) for f in self.faces for fv in [len(f)]+f)),
            self.color)

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

            >>> GeneralPolyhedronShape([[0.5, 0.5, 0.5], [0.5, -0.5, -0.5],
                                        [-0.5, 0.5, -0.5], [-0.5, -0.5, 0.5]]).type_shape
            {'type': 'Mesh',
             'vertices': [[0.5, 0.5, 0.5], [0.5, -0.5, -0.5],
                          [-0.5, 0.5, -0.5], [-0.5, -0.5, 0.5]],
             'indices': [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]}
        """
        return {'type': 'Mesh',
                'vertices': self.vertices,
                'indices': self.faces}


class EllipsoidShape(Shape):
    """Shape class for ellipsoids of with principal axes a, b, and c.

    :param a:
        Principal axis a of the ellipsoid (radius in the x direction).
    :type a:
        float
    :param b:
        Principal axis b of the ellipsoid (radius in the y direction).
    :type b:
        float
    :param c:
        Principal axis c of the ellipsoid (radius in the z direction).
    :type c:
        float
    :param color:
        Hexadecimal color string in format :code:`RRGGBBAA` (default: :code:`None`).
    :type color:
        str
    """

    def __init__(self, a, b, c, color=None):
        super(EllipsoidShape, self).__init__(
            shape_class='ellipsoid', color=color)
        self.a = a
        self.b = b
        self.c = c

    @property
    def pos_string(self):
        return "{} {} {} {} {}".format(
            self.shape_class,
            self.a,
            self.b,
            self.c,
            self.color
        )

    @property
    @_json_sanitize
    def type_shape(self):
        """Shape as dictionary. Example:

            >>> EllipsoidShape(7.0, 5.0, 3.0).type_shape
            {'type': 'Ellipsoid',
             'a': 7.0,
             'b': 5.0,
             'c': 3.0}

        """
        return {'type': 'Ellipsoid',
                'a': self.a,
                'b': self.b,
                'c': self.c}


def _parse_type_shape(shape):
    """Parses a shape object from a dictionary.

    This method parses the `GSD Shape Visualization Specification
    <https://gsd.readthedocs.io/en/stable/shapes.html>`_, while including
    backwards compatibility with shape definitions that do not adhere to that
    specification but were previously supported by HOOMD's
    :code:`get_type_shapes()` methods.
    """

    if not shape:
        return FallbackShape('')

    type_name = shape['type'].lower()
    type_shape = None

    if type_name in ('sphere', 'disk'):
        # disk support is for backwards compatibility with get_type_shapes()
        # from HOOMD-blue < 2.7
        diameter = shape.get('diameter', 2*shape.get('rounding_radius', 0.5))
        orientable = shape.get('orientable', False)
        type_shape = SphereShape(diameter=diameter, orientable=orientable, color=None)
    elif type_name == 'ellipsoid':
        type_shape = EllipsoidShape(a=shape['a'], b=shape['b'], c=shape['c'], color=None)
    elif type_name == 'polygon':
        rounding_radius = shape.get('rounding_radius', 0)
        if rounding_radius == 0:
            type_shape = PolygonShape(vertices=shape['vertices'], color=None)
        else:
            type_shape = SpheropolygonShape(vertices=shape['vertices'],
                                            rounding_radius=rounding_radius,
                                            color=None)
    elif type_name == 'convexpolyhedron':
        rounding_radius = shape.get('rounding_radius', 0)
        if rounding_radius == 0:
            type_shape = ConvexPolyhedronShape(vertices=shape['vertices'], color=None)
        else:
            type_shape = ConvexSpheropolyhedronShape(vertices=shape['vertices'],
                                                     rounding_radius=rounding_radius,
                                                     color=None)
    elif type_name == 'mesh':
        type_shape = GeneralPolyhedronShape(vertices=shape['vertices'],
                                            faces=shape['indices'],
                                            facet_colors=shape['colors'],
                                            color=None)
    elif type_name == 'polyhedron':
        # polyhedron support is for backwards compatibility with
        # get_type_shapes() from HOOMD-blue < 2.7
        type_shape = GeneralPolyhedronShape(vertices=shape['vertices'],
                                            faces=shape['faces'],
                                            facet_colors=shape['colors'],
                                            color=None)
    elif type_name == 'sphereunion':
        type_shape = SphereUnionShape(diameters=shape['diameters'],
                                      centers=shape['centers'],
                                      color=None)

    if type_shape is None:
        logger.warning("Failed to parse shape definition: shape {} not supported. "
                       "Using fallback mode.".format(type_name))
        type_shape = FallbackShape(json.dumps(shape))

    return type_shape
