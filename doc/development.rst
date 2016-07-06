Developer's Guide
=================

Trajectory reader implementation
--------------------------------

To implement a trajectory reader, first keep in mind that a glotzformats trajectory is simply a sequence of frames.
This means that a trajectory reader needs to generate individual instances of frames.

To implement a new reader:

  1. Provide a minimal sample for your format.
  2. Create a new module in `src/glotzformats` with the name `<fileformat>reader.py`.
  3. Specialize a frame class for your format called `<fileformat>Frame`.
  4. Implement the `read()` method for your frame, it should return an instance of :py:class:`glotzformats.trajectory._RawFrameData`.

    .. py:class:: class <fileformat>Frame(trajectory.Frame):

        def read():
            Read the frame data from the stream.

            :returns: :class:`.trajectory._RawFrameData`

  5. Define a class `<fileformat>Reader`, where the constructor may take optional arguments for your reader.
  6. Your `<fileformat>Reader` class needs to implement a `read()` method.

    .. py:class:: class <fileformat>Reader(object):

        def read(stream):
          Read the trajectory from stream.

          .. code::

              # pseudo-example
              frames = list(self.scan(stream))
              return trajectory.Trajectory(frames)

          :stream: A file-like object.
          :returns: :class:`.trajectory.Trajectory`

    7. Add your reader class to the `__all__` directive in the `src/glotzformats/reader.py` module.
    8. Provide a unit test for your reader, that reads a sample and generates a trajectory object accordingly.

For an example, please see the :py:class:`.GSDHOOMDFileReader` implementation.
