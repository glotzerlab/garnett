"""GSD file writer for the Glotzer Group, University of Michigan.

Author: Vyas Ramasubramani

"""

import gsd
import gsd.hoomd
import logging
logger = logging.getLogger(__name__)


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
        :param filename: The file to write to.
        """

        try:
            filename = stream.name
            mode = stream.mode
        except AttributeError:
            raise NotImplementedError(
                "The current implementation of the GSDFileWriter requires "
                "file objects with name attribute, such as NamedTemporaryFile "
                "as the underlying library is reading the file by filename "
                "and not directly from the stream.")

        with gsd.hoomd.open(name=filename, mode=mode) as traj_outfile:
            for i, frame in enumerate(trajectory):
                types = list(set(frame.types))
                snap = gsd.hoomd.Snapshot()
                snap.particles.N = len(frame)
                snap.particles.types = types
                snap.particles.typeid = [types.index(typeid)
                                         for typeid in frame.types]
                snap.particles.position = frame.positions
                snap.particles.orientation = frame.orientations
                snap.particles.velocity = frame.velocities
                snap.particles.mass = frame.mass
                snap.particles.charge = frame.charge
                snap.particles.diameter = frame.diameter
                snap.particles.moment_inertia = frame.moment_inertia
                snap.particles.angmom = frame.angmom
                box = frame.box
                snap.configuration.box = [box.Lx, box.Ly, box.Lz,
                                          box.xy, box.xz, box.yz]
                traj_outfile.append(snap)
                logger.debug("Wrote frame {}.".format(i + 1))
        logger.info("Wrote {} frames.".format(i + 1))
