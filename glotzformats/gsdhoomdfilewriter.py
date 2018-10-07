"""GSD file writer for the Glotzer Group, University of Michigan.

Author: Vyas Ramasubramani

"""

import gsd
import gsd.hoomd
import logging
import numpy as np

from .trajectory import SphereShapeDefinition, PolyShapeDefinition, SpheroPolyShapeDefinition

logger = logging.getLogger(__name__)


def _write_shape_definitions(snap, shapedefs):
    state = {}

    def compute_property(compute=lambda x: x):
        return np.array([compute(shape) for shape in shapedefs.values()])

    n_types = len(shapedefs)
    if n_types > 0:
        # Ensure all shape types are the same
        shape_type = type(next(iter(shapedefs.values())))
        if all([isinstance(shapedef, shape_type) for shapedef in shapedefs.values()]):
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
                _write_shape_definitions(snap, frame.shapedef)
                traj_outfile.append(snap)
                logger.debug("Wrote frame {}.".format(i + 1))
        logger.info("Wrote {} frames.".format(i + 1))
