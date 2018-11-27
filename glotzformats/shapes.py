# Copyright (c) 2018 The Regents of the University of Michigan
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
    """Initialize a Shape instance.

    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, shape_class=None, color=None):
        self.shape_class = shape_class
        self.color = SHAPE_DEFAULT_COLOR if color is None else color

    def __str__(self):
        return "{} {}".format(self.shape_class, self.color)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return str(self) == str(other)


class SphereShape(Shape):
    """Initialize a SphereShape instance.

    :param diameter: The diameter of the sphere.
    :type diameter: A floating point number.
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, diameter, color=None):
        super(SphereShape, self).__init__(
            shape_class='sphere', color=color)
        self.diameter = diameter

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.diameter, self.color)

    @property
    def json_shape(self):
        return {'type': 'Sphere'}


class ArrowShape(Shape):
    """Initialize an ArrowShape instance.

    :param thickness: The thickness of the arrow.
    :type thickness: A floating point number.
    :param color: Definition of a color for the
                  particular shape (optional).
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, thickness=0.1, color=None):
        super(ArrowShape, self).__init__(
            shape_class='arrow', color=color)
        self.thickness = thickness

    def __str__(self):
        return "{} {} {}".format(self.shape_class, self.thickness, self.color)


class SphereUnionShape(Shape):
    """Initialize a SphereUnionShape instance.

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
    """Initialize a PolygonShape instance.

    :param vertices: A list of vertex vectors, if applicable.
    :type vertices: A sequence of 3-tuples of numbers (Nx3), where the third component is z=0.
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, vertices=None, color=None):
        super(PolygonShape, self).__init__(
            shape_class='poly', color=color)
        self.vertices = vertices

    def __str__(self):
        return "{} {} {} {}".format(
            self.shape_class,
            len(self.vertices),
            ' '.join((str(v) for xyz in self.vertices for v in xyz)),
            self.color)

    @property
    def json_shape(self):
        return {'type': 'Polygon',
                'rounding_radius': 0,
                'vertices': [v[:2] for v in self.vertices]}


class SpheropolygonShape(Shape):
    """Initialize a SpheropolygonShape instance.

    :param vertices: A list of vertex vectors, if applicable.
    :type vertices: A sequence of 3-tuples of numbers (Nx3), where the third component is z=0.
    :param rounding_radius: Rounding radius applied to the spheropolygon.
    :type rounding_radius: A floating-point number.
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format RRGGBBAA.
    """

    def __init__(self, vertices=None, rounding_radius=None, color=None):
        super(SpheropolygonShape, self).__init__(
            shape_class='spoly', color=color)
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
        return {'type': 'Polygon',
                'rounding_radius': self.rounding_radius,
                'vertices': [v[:2] for v in self.vertices]}


class ConvexPolyhedronShape(Shape):
    """Initialize a ConvexPolyhedronShape instance.

    :param vertices: A list of vertex vectors, if applicable.
    :type vertices: A sequence of 3-tuples of numbers (Nx3).
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format RRGGBBAA.
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
    def json_shape(self):
        return {'type': 'ConvexPolyhedron',
                'rounding_radius': 0,
                'vertices': self.vertices}


class ConvexPolyhedronUnionShape(Shape):
    """Initialize a Shape instance.

    :param vertices: A list of lists of the vertices of the polyhedra in particle coordinates
    :type vertices: A list of lists of 3-tuples
    :param centers: A list of the centers of the polyhedra in particle coordinates
    :type centers: A list of 3-tuples
    :param orientations: A list of the orientations of the polyhedra
    :type orientations: A list of 4-tuples
    :param colors: Definition of a color for every polyhedron
    :type colors: A sequence of str for RGB color definiton.
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
    """Initialize a ConvexSpheropolyhedronShape instance.

    :param vertices: A list of vertex vectors, if applicable.
    :type vertices: A sequence of 3-tuples of numbers (Nx3).
    :param rounding_radius: Rounding radius applied to the spheropolyhedron.
    :type rounding_radius: A floating-point number.
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format RRGGBBAA.
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
    def json_shape(self):
        return {'type': 'ConvexPolyhedron',
                'rounding_radius': self.rounding_radius,
                'vertices': self.vertices}


class GeneralPolyhedronShape(Shape):
    """Initialize a GeneralPolyhedronShape instance.

    :param vertices: A list of vertex vectors.
    :type vertices: A sequence of 3-tuples of numbers (Nx3).
    :param faces: A list of lists of vertex indices per face.
    :type faces: A list of lists of integer numbers.
    :param color: Definition of a color for the particular shape.
    :type color: A hexadecimal color string in format 'RRGGBBAA'.
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
