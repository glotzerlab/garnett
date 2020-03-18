# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""getar-file writer for the Glotzer Group, University of Michigan.

Authors: Bradley Dice

.. code::

    writer = GetarFileWriter()
    with open('trajectory.tar', 'wb') as gtarfile:
        writer.write(trajectory, gtarfile)
"""

from gtar import GTAR, Record
import json
import logging
logger = logging.getLogger(__name__)


class GetarFileWriter(object):
    """getar-file writer for the Glotzer Group, University of Michigan.

    Authors: Bradley Dice

    Write GEneric Trajectory ARchive files, a binary format designed
    for efficient, extensible storage of trajectory data.

    This class provides a wrapper for the gtar library.

    .. code::

        writer = GetarFileWriter()
        with open('trajectory.tar', 'wb') as gtarfile:
            writer.write(trajectory, gtarfile)

        # For appending to the file
        with open('trajectory.tar', 'ab') as gtarfile:
            writer.write(trajectory, gtarfile)
    """

    property_record_map = {
        'typeid': 'type.u32.ind',
        'position': 'position.f32.ind',
        'orientation': 'orientation.f32.ind',
        'velocity': 'velocity.f32.ind',
        'mass': 'mass.f32.ind',
        'charge': 'charge.f32.ind',
        'diameter': 'diameter.f32.ind',
        'moment_inertia': 'moment_inertia.f32.ind',
        'angmom': 'angular_momentum_quat.f32.ind',
        'image': 'image.i32.ind',
        }

    def makeRecord(self, name, index=None, prefix=None):
        if index is not None:
            frame = 'frames/{}'.format(index)
        else:
            frame = None
        path_parts = [prefix, frame, name]
        path = '/'.join(filter(lambda x: x is not None, path_parts))
        return Record(path)

    def writeFrame(self, bulkwriter, frame, index=None, skip_props=False):
        """Write the frame data for an index using a bulk writer."""

        # Type names
        types_rec = self.makeRecord('type_names.json', index=index)
        types_contents = json.dumps(frame.types)
        bulkwriter.writeRecord(rec=types_rec, contents=types_contents)

        if not skip_props:
            # Particle properties
            for prop, recname in type(self).property_record_map.items():
                rec = self.makeRecord(recname, index=index)
                contents = getattr(frame, prop)
                bulkwriter.writeRecord(rec=rec, contents=contents)

        # Box and dimensions
        box_rec = self.makeRecord('box.f32.uni', index=index)
        bulkwriter.writeRecord(rec=box_rec, contents=frame.box.get_box_array())
        dim_rec = self.makeRecord('dimensions.u32.uni', index=index)
        bulkwriter.writeRecord(rec=dim_rec, contents=[frame.box.dimensions])

        # Shape definitions
        type_shapes = getattr(frame, 'type_shapes', None)
        if type_shapes is not None:
            shape_rec = self.makeRecord('type_shapes.json', index=index)
            type_shapes = json.dumps([t.type_shape for t in type_shapes])
            bulkwriter.writeRecord(rec=shape_rec, contents=type_shapes)

    def write(self, trajectory, stream, static_frame=None):
        """Serialize a trajectory into gtar-format and write it to a file.

        :param trajectory: The trajectory to serialize
        :type trajectory: :class:`~garnett.trajectory.Trajectory`
        :param filename: The file to write to."""

        try:
            filename = stream.name
            mode = stream.mode
        except AttributeError:
            raise NotImplementedError(
                "The current implementation of the GetarFileWriter requires "
                "file objects with name attribute, such as NamedTemporaryFile "
                "as the underlying library is reading the file by filename "
                "and not directly from the stream.")
        with GTAR(path=filename, mode=mode) as t, \
                t.getBulkWriter() as t_writer:

            for index, frame in enumerate(trajectory):

                if index == 0:  # avoid indexing to allow tqdm(trajectory)
                    if static_frame is None:
                        # Write the first frame of the trajectory as static data
                        # so that box, type, and shape information is accessible
                        self.writeFrame(t_writer, frame,
                                        index=None, skip_props=True)
                    else:
                        self.writeFrame(t_writer, static_frame,
                                        index=None, skip_props=True)

                self.writeFrame(t_writer, frame, index)

                logger.debug("Wrote frame {}.".format(index + 1))

        logger.info("Wrote {} frames.".format(index + 1))
