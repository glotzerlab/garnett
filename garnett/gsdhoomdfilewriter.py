# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""GSD file writer for the Glotzer Group, University of Michigan.

Author: Vyas Ramasubramani

"""

import gsd
import gsd.hoomd
import logging

from .trajectory import PARTICLE_PROPERTIES

logger = logging.getLogger(__name__)


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

        :param trajectory: The trajectory to serialize.
        :type trajectory: :class:`~garnett.trajectory.Trajectory`
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

                # Set frame properties
                snap.configuration.box = frame.box.get_box_array()
                snap.configuration.dimensions = frame.box.dimensions
                snap.particles.N = N

                # Set type properties
                snap.particles.types = getattr(frame, 'types', ['A'])
                type_shapes = getattr(frame, 'type_shapes', None)
                if type_shapes is not None:
                    snap.particles.type_shapes = [t.type_shape for t in frame.type_shapes]

                # Set particle properties
                for prop in PARTICLE_PROPERTIES:
                    try:
                        setattr(snap.particles, prop, getattr(frame, prop))
                    except AttributeError:
                        pass
                traj_outfile.append(snap)
                logger.debug("Wrote frame {}.".format(i + 1))
