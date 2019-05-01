# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

"""Abstract shape definitions used to read/write particle shapes."""


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
]


SHAPE_DEFAULT_COLOR = '005984FF'


class FallbackShape(str):
    """This shape definition class is used when no specialized Shape class can be applied.

    The fallback shape definition is a str containing the definition."""
    pass


class Shape(object):
    """Parent class of all shape objects.

    :param color:
        Definition of a color for the particular shape (optional).
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, shape_class=None, color=None):
        self.shape_class = shape_class
        self.color = color if color else SHAPE_DEFAULT_COLOR

    def __str__(self):
        return "{} {}".format(self.shape_class, self.color)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)


class SphereShape(Shape):
    """Shape class for spheres of a specified diameter.

    :param diameter:
        The diameter of the sphere.
    :type diameter:
        A floating point number.
    :param color:
        Definition of a color for the particular shape (optional).
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, diameter, color=None):
        super(SphereShape, self).__init__(
            shape_class='sphere', color=color)
        self.diameter = diameter

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.diameter, self.color)

    @property
    def shape_dict(self):
        return {'type': 'Sphere',
                'diameter': self.diameter}


class ArrowShape(Shape):
    """Shape class for arrows of a specified thickness.

    :param thickness:
        The thickness of the arrow.
    :type thickness:
        A floating point number.
    :param color:
        Definition of a color for the particular shape (optional).
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, thickness=0.1, color=None):
        super(ArrowShape, self).__init__(
            shape_class='arrow', color=color)
        self.thickness = thickness

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.thickness, self.color)


class SphereUnionShape(Shape):
    """Shape class for sphere unions, such as rigid bodies of many spheres.

    :param diameters:
        A list of sphere diameters.
    :type diameters:
        A sequence of numbers.
    :param centers:
        A list of vertex vectors, if applicable.
    :type centers:
        A sequence of 3-tuples of numbers (Nx3).
    :param colors:
        Definition of a color for every sphere.
    :type colors:
        A sequence of hexadecimal color strings in format RRGGBBAA.
    """

    def __init__(self, diameters=None, centers=None, colors=None):
        super(SphereUnionShape, self).__init__(
            shape_class='sphere_union', color='')
        self.diameters = diameters
        self.centers = centers
        self.colors = colors

    def __str__(self):
        shape_def = '{} {} '.format(self.shape_class, len(self.centers))
        for d, p, c in zip(self.diameters, self.centers, self.colors):
            shape_def += '{0} '.format(d)
            shape_def += '{0} {1} {2} '.format(*p)
            shape_def += '{0} '.format(c)

        return shape_def


class PolygonShape(Shape):
    """Shape class for polygons in a 2D plane.

    :param vertices:
        A list of vertex vectors, if applicable.
    :type vertices:
        A sequence of 2-tuples of numbers (Nx2).
    :param color:
        Definition of a color for the particular shape.
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, vertices=None, color=None):
        super(PolygonShape, self).__init__(
            shape_class='poly3d', color=color)
        self.vertices = vertices

    def __str__(self):
        return "{} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join('{} {} 0'.format(v[0], v[1]) for v in self.vertices),
            self.color)

    @property
    def shape_dict(self):
        return {'type': 'Polygon',
                'rounding_radius': 0,
                'vertices': self.vertices}


class SpheropolygonShape(Shape):
    """Shape class for rounded polygons in a 2D plane.

    :param vertices:
        A list of vertex vectors, if applicable.
    :type vertices:
        A sequence of 2-tuples of numbers (Nx2).
    :param rounding_radius:
        Rounding radius applied to the spheropolygon.
    :type rounding_radius:
        A floating-point number.
    :param color:
        Definition of a color for the particular shape.
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, vertices=None, rounding_radius=None, color=None):
        super(SpheropolygonShape, self).__init__(
            shape_class='spoly3d', color=color)
        self.vertices = vertices
        self.rounding_radius = rounding_radius

    def __str__(self):
        return "{} {} {} {} {}".format(
            self.shape_class,
            self.rounding_radius,
            len(self.vertices),
            ' '.join('{} {} 0'.format(v[0], v[1]) for v in self.vertices),
            self.color)

    @property
    def shape_dict(self):
        return {'type': 'Polygon',
                'rounding_radius': self.rounding_radius,
                'vertices': self.vertices}


class ConvexPolyhedronShape(Shape):
    """Shape class for convex polyhedra.

    :param vertices:
        A list of vertex vectors, if applicable.
    :type vertices:
        A sequence of 3-tuples of numbers (Nx3).
    :param color:
        Definition of a color for the particular shape.
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, vertices=None, color=None):
        super(ConvexPolyhedronShape, self).__init__(
            shape_class='poly3d', color=color)
        self.vertices = vertices

    def __str__(self):
        return "{} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            self.color)

    @property
    def shape_dict(self):
        return {'type': 'ConvexPolyhedron',
                'rounding_radius': 0,
                'vertices': self.vertices}


class ConvexPolyhedronUnionShape(Shape):
    """Shape class for unions of convex polyhedra.

    :param vertices:
        A sequence of the vertices of the polyhedra in particle coordinates.
    :type vertices:
        A sequence of sequences of vertex 3-tuples (each shape, each vertex).
    :param centers:
        A sequence of the centers of the polyhedra in particle coordinates.
    :type centers:
        A sequence of coordinate 3-tuples.
    :param orientations:
        A sequence of the orientations of the polyhedra.
    :type orientations:
        A sequence of quaternion 4-tuples.
    :param colors:
        Definition of a color for every polyhedron.
    :type colors:
        A sequence of hexadecimal color strings in format RRGGBBAA.
    """

    def __init__(self, vertices=None, centers=None, orientations=None, colors=None):
        super(ConvexPolyhedronUnionShape, self).__init__(
            shape_class='poly3d_union', color='')
        self.vertices = vertices
        self.centers = centers
        self.orientations = orientations
        self.colors = colors

    def __str__(self):
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
        A list of vertex vectors, if applicable.
    :type vertices:
        A sequence of 3-tuples of numbers (Nx3).
    :param rounding_radius:
        Rounding radius applied to the spheropolyhedron.
    :type rounding_radius:
        A floating-point number.
    :param color:
        Definition of a color for the particular shape.
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, vertices=None, rounding_radius=None, color=None):
        super(ConvexSpheropolyhedronShape, self).__init__(
            shape_class='spoly3d', color=color)
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
    def shape_dict(self):
        return {'type': 'ConvexPolyhedron',
                'rounding_radius': self.rounding_radius,
                'vertices': self.vertices}


class GeneralPolyhedronShape(Shape):
    """Shape class for general polyhedra, such as arbitrary meshes.

    :param vertices:
        A sequence of vertex vectors.
    :type vertices:
        A sequence of 3-tuples of numbers (Nx3).
    :param faces:
        A sequences of sequences representings vertex indices per face.
    :type faces:
        A sequence of sequences of integers.
    :param color:
        Definition of a color for the particular shape.
    :type color:
        A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, vertices=None, faces=None, color=None, facet_colors=None):
        super(GeneralPolyhedronShape, self).__init__(
            shape_class='polyV', color=color)
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

    @property
    def shape_dict(self):
        return {'type': 'Mesh',
                'vertices': self.vertices,
                'indices': self.faces}
