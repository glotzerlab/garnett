"""GSD file writer for the Glotzer Group, University of Michigan.

Author: Vyas Ramasubramani

"""

import gsd
import gsd.hoomd
import logging
import numpy as np

from .shapes import SphereShape, ConvexPolyhedronShape, ConvexSpheropolyhedronShape, \
    PolygonShape, SpheropolygonShape, EllipsoidShape
from .errors import GSDShapeError

logger = logging.getLogger(__name__)


def _write_shape_definitions(snap, shapedefs):
    state = {}

    def compute_property(compute=lambda x: x):
        """This helper function iterates over the dictionary of shapedefs
        to produce a numpy array of shape data to save to the frame state."""
        return np.array([compute(shape) for shape in shapedefs.values()])

    try:
        # If the shape types don't all match, there is no valid conversion to the GSD state.
        # To ensure all shape types are the same: Get the first shape's type,
        # and then compare it to all other shape types.
        shape_type = type(next(iter(shapedefs.values())))
        assert all([isinstance(shapedef, shape_type) for shapedef in shapedefs.values()]), 'Not all shape types match.'
    except StopIteration:
        # The shapedefs are empty, so there is nothing to write.
        pass
    except AssertionError as e:
        raise GSDShapeError('Shape definitions could not be written to the GSD snapshot: {}'.format(e))
    else:
        if shape_type is SphereShape:
            state['hpmc/sphere/radius'] = compute_property(lambda shape: 0.5*shape.diameter)
        elif shape_type is ConvexPolyhedronShape:
            state['hpmc/convex_polyhedron/N'] = compute_property(lambda shape: len(shape.vertices))
            vertices = compute_property(lambda shape: shape.vertices)
            vertices = np.concatenate(vertices, axis=0)
            state['hpmc/convex_polyhedron/vertices'] = vertices
        elif shape_type is ConvexSpheropolyhedronShape:
            state['hpmc/convex_spheropolyhedron/N'] = compute_property(lambda shape: len(shape.vertices))
            vertices = compute_property(lambda shape: shape.vertices)
            vertices = np.concatenate(vertices, axis=0)
            state['hpmc/convex_spheropolyhedron/vertices'] = vertices
            state['hpmc/convex_spheropolyhedron/sweep_radius'] = \
                compute_property(lambda shape: shape.rounding_radius)
        elif shape_type is PolygonShape:
            state['hpmc/simple_polygon/N'] = compute_property(lambda shape: len(shape.vertices))
            vertices = compute_property(lambda shape: shape.vertices[:2])
            vertices = np.concatenate(vertices, axis=0)
            state['hpmc/simple_polygon/vertices'] = vertices
        elif shape_type is SpheropolygonShape:
            state['hpmc/convex_spheropolygon/N'] = compute_property(lambda shape: len(shape.vertices))
            vertices = compute_property(lambda shape: shape.vertices[:2])
            vertices = np.concatenate(vertices, axis=0)
            state['hpmc/convex_spheropolygon/vertices'] = vertices
            state['hpmc/convex_spheropolygon/sweep_radius'] = \
                compute_property(lambda shape: shape.rounding_radius)
        elif shape_type is EllipsoidShape:
            state['hpmc/ellipsoid/a'] = compute_property(lambda shape: shape.a)
            state['hpmc/ellipsoid/b'] = compute_property(lambda shape: shape.b)
            state['hpmc/ellipsoid/c'] = compute_property(lambda shape: shape.c)
        else:
            raise GSDShapeError('Unsupported shape: {}'.format(shape_type))

    snap.state = state


class GSDHOOMDFileWriter(object):
    """GSD file writer for the Glotzer Group, University of Michigan.

    Author: Vyas Ramasubramani
    Author: Bradley Dice


    .. code::

        writer = GSDHOOMDFileWriter()
        with open('file.gsd', 'wb') as gsdfile:
            writer.write(trajectory, gsdfile)

        # For appending to the file
        with open('file.gsd', 'ab') as gsdfile:
            writer.write(trajectory, gsdfile)
    """

    def write(self, trajectory, stream):
        """Serialize a trajectory into gsd-format and write it to a file.

        :param trajectory: The trajectory to serialize
        :type trajectory: :class:`~glotzformats.trajectory.Trajectory`
        :param stream: The file to write to.
        :type stream: File stream
        """

        try:
            filename = stream.name
            mode = stream.mode
        except AttributeError:
            raise NotImplementedError(
                "The current implementation of the GSDHOOMDFileWriter requires "
                "file objects with name attribute, such as NamedTemporaryFile, "
                "as the underlying library is reading the file by filename "
                "and not directly from the stream.")

        with gsd.hoomd.open(name=filename, mode=mode) as traj_outfile:
            for i, frame in enumerate(trajectory):
                N = len(frame)
                snap = gsd.hoomd.Snapshot()
                snap.particles.N = N
                try:
                    types = list(set(frame.types))
                except AttributeError:
                    types = ['A']
                snap.particles.types = types
                try:
                    snap.particles.typeid = [types.index(typeid) for typeid in frame.types]
                except AttributeError:
                    snap.particles.typeid = np.zeros(N, dtype=np.uint32)
                try:
                    snap.particles.position = frame.positions
                except AttributeError:
                    snap.particles.position = np.zeros([N, 3], dtype=np.float32)
                try:
                    snap.particles.orientation = frame.orientations
                except AttributeError:
                    snap.particles.orientation = np.array([[1, 0, 0, 0]]*N, dtype=np.float32)
                try:
                    snap.particles.velocity = frame.velocities
                except AttributeError:
                    snap.particles.velocity = np.zeros([N, 3], dtype=np.float32)
                try:
                    snap.particles.mass = frame.mass
                except AttributeError:
                    snap.particles.mass = np.ones(N, dtype=np.float32)
                try:
                    snap.particles.charge = frame.charge
                except AttributeError:
                    snap.particles.charge = np.zeros(N, dtype=np.float32)
                try:
                    snap.particles.diameter = frame.diameter
                except AttributeError:
                    snap.particles.diameter = np.ones(N, dtype=np.float32)
                try:
                    snap.particles.moment_inertia = frame.moment_inertia
                except AttributeError:
                    snap.particles.moment_inertia = np.zeros([N, 3], dtype=np.float32)
                try:
                    snap.particles.angmom = frame.angmom
                except AttributeError:
                    snap.particles.angmom = np.zeros([N, 4], dtype=np.float32)
                snap.configuration.box = frame.box.get_box_array()
                try:
                    _write_shape_definitions(snap, frame.shapedef)
                except AttributeError:
                    _write_shape_definitions(snap, {})
                traj_outfile.append(snap)
                logger.debug("Wrote frame {}.".format(i + 1))
        logger.info("Wrote {} frames.".format(i + 1))
