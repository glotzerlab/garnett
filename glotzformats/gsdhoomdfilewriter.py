"""GSD file writer for the Glotzer Group, University of Michigan.

Author: Vyas Ramasubramani

"""

import gsd
import gsd.hoomd
import logging
import numpy as np

from .trajectory import SphereShapeDefinition, PolyShapeDefinition, SpheroPolyShapeDefinition
from .errors import GSDShapeError

logger = logging.getLogger(__name__)


def _write_shape_definitions(snap, shapedefs, ignore_shape_errors=False):
    state = {}

    def compute_property(compute=lambda x: x):
        """This helper function iterates over the dictionary of shapedefs
        to produce a numpy array of shape data to save to the frame state."""
        return np.array([compute(shape) for shape in shapedefs.values()])

    try:
        # If the shape types don't all match, there is no valid conversion to the GSD state.
        # To ensure all shape types are the same: Get the first shape's type,
        # and then compare it to all other shape types.
        assert len(shapedefs) > 0, 'shapedefs length is not greater than 0.'
        shape_type = type(next(iter(shapedefs.values())))
        assert all([isinstance(shapedef, shape_type) for shapedef in shapedefs.values()]), 'Not all shape types match.'
    except AssertionError as e:
        if not ignore_shape_errors:
            raise GSDShapeError('Shape definitions could not be written to the GSD snapshot: {}'.format(e))
    else:
        if shape_type is SphereShapeDefinition:
            state['hpmc/sphere/radius'] = compute_property(lambda shape: 0.5*shape.diameter)
        elif shape_type is PolyShapeDefinition:
            state['hpmc/convex_polyhedron/N'] = compute_property(lambda shape: len(shape.vertices))
            vertices = compute_property(lambda shape: shape.vertices)
            vertices = np.concatenate(vertices, axis=0)
            state['hpmc/convex_polyhedron/vertices'] = vertices
        elif shape_type is SpheroPolyShapeDefinition:
            state['hpmc/convex_spheropolyhedron/N'] = compute_property(lambda shape: len(shape.vertices))
            vertices = compute_property(lambda shape: shape.vertices)
            vertices = np.concatenate(vertices, axis=0)
            state['hpmc/convex_spheropolyhedron/vertices'] = vertices
            state['hpmc/convex_spheropolyhedron/sweep_radius'] = \
                compute_property(lambda shape: shape.rounding_radius)

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

    def write(self, trajectory, stream, ignore_shape_errors=False):
        """Serialize a trajectory into gsd-format and write it to a file.

        :param trajectory: The trajectory to serialize
        :type trajectory: :class:`~glotzformats.trajectory.Trajectory`
        :param stream: The file to write to.
        :type stream: File stream
        :param ignore_shape_errors: Whether to ignore errors occuring during
            writing shape information to the GSD state (Default: False).
        :type ignore_shape_errors: bool
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
                types = list(set(frame.types))
                snap = gsd.hoomd.Snapshot()
                snap.particles.N = len(frame)
                snap.particles.types = types
                snap.particles.typeid = [types.index(typeid) for typeid in frame.types]
                snap.particles.position = frame.positions
                snap.particles.orientation = frame.orientations
                snap.particles.velocity = frame.velocities
                snap.particles.mass = frame.mass
                snap.particles.charge = frame.charge
                snap.particles.diameter = frame.diameter
                snap.particles.moment_inertia = frame.moment_inertia
                snap.particles.angmom = frame.angmom
                snap.configuration.box = frame.box.get_box_array()
                _write_shape_definitions(snap, frame.shapedef, ignore_shape_errors)
                traj_outfile.append(snap)
                logger.debug("Wrote frame {}.".format(i + 1))
        logger.info("Wrote {} frames.".format(i + 1))
