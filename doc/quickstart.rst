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

Access individual frames or create sub-trajectories by slicing:

.. code-block:: python

    # Select individual frames
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

You can access trajectory positions, orientations and types
as numpy arrays:

.. code-block:: python

    traj.load_arrays()
    traj.positions      # MxNx3 array
    traj.orientations   # MxNx4 array
    traj.types          # MxN array

    # where M=len(traj), N=max((len(f) for f in traj))


You can iterate over trajectories for memory-efficient data access:

.. code-block:: python

    # Iterate over a trajectory directly for read-only data access
    for frame in traj:
      print(frame.positions)

    # Iterate over an index for data modification
    for i in range(len(traj)):
        traj[i].box = # ...

Access properties of individual frames:

.. code-block:: python

    frame = traj[i]
    frame.box           # 3x3 array
    frame.positions     # Nx3 array
    frame.orientations  # Nx4 array
    frame.types         # Nx1 array
    frame.data          # A dictionary of lists for each attribute
    frame.data_key      # A list of strings
    frame.shapedef      # A ordered dictionary of instances of ShapeDefinition.

All arrays are instances of :py:class:`numpy.ndarray`.

Efficient trajectory modification
---------------------------------

Memory-efficient modification of large trajectory data requires live reading and writing to disk.
This is an example on how to modify frames in-place:

.. code-block:: python

    import numpy as np

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


Example use with HOOMD-blue
---------------------------

.. code-block:: python

    from hoomd import init
    # For versions <2.x: from hoomd_script import init
    
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
