Quickstart
==========

Reading and writing
-------------------

.. code-block:: python

    from glotzformats.reader import PosFileReader
    from glotzformats.writer import PosFileWriter

    pos_reader = PosFileReader()
    pos_writer = PosFileWriter()

    with open('posfile.pos') as file:
        # Access the trajectory
        traj = pos_reader.read(file)

        # Write to standard out:
        pos_writer.write(traj)

        # or directly to a file:
        with open('out.pos', 'w') as posfile:
            pos_writer.write(traj, posfile)


Data access
-----------

Access individual frames or create sub-trajectories by indexing.

.. code-block:: python

    # Select individual frams
    first_frame = traj[0]
    last_frame = traj[-1]
    n_th_frame = traj[n]
    # and so on

    # Create a sub-trajectory from the ith frame
    # to the (j-1)th frame.
    sub_trajectory = traj[i:j]

    # We can use advanced slicing techniques:
    every_second_frame = traj[::2]
    the_last_ten_frames = traj[-10::]

You can iterate over trajectories for fast data access.

.. code-block:: python

    # Iterate over a trajectory directly for data access
    for frame in traj:
      print(frame.positions)

    # Iterate over indeces for data modification
    for i in range(len(traj)):
        traj[i].box = # ...

Access properties of individual frames:

.. code-block:: python

    frame = traj[i]
    frame.box           # 3x3 matrix
    frame.types         # Nx1
    frame.positions     # Nx3
    frame.orientations  # Nx4
    frame.data          # A dictionary of lists for each attribute
    frame.data_key      # A list of strings
    frame.shapedef      # A ordered dictionary of instances of ShapeDefinition.

All matrices are `numpy` arrays.

Efficient trajectory modification
---------------------------------

Modification of big trajectory data without keeping all data in memory requires live reading and writing to disk.
This is an example on how to modify frames in-place:

.. code-block:: python

    import numpy

    from glotzformats.reader import PosFileReader
    from glotzformats.reader import PosFileWriter
    from glotzformats.trajectory import Trajectory

    def center(frame):
        frame.positions -= np.average(frame.positions, axis=0)
        return frame

    pos_reader = PosFileReader()
    pos_writer = PosFileWriter()

    with open('in.pos') as file:
        traj = pos_reader.read(file)
        traj_centered = Trajectory((center(frame) for frame in traj))
        pos_writer.write(traj_centered)


Example use with hoomd-blue
---------------------------

.. code-block:: python

    from hoomd import init
    from glotzformats.reader import PosFileReader

    pos_reader = PosFileReader()
    with open('cube.pos') as posfile:
        traj = pos_reader.read(posfile)

        # Initialize from last frame
        snapshot = traj[-1].make_snapshot()
        system = init.read_snapshot(snapshot)

        # Restore last frame
        snapshot = system.take_snapshot()
        traj[-1].copyto_snapshot(snapshot)


.. note::

    Use hoomd's native pos-file *writer* whenever possible.
