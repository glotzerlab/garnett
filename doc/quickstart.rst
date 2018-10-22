==========
Quickstart
==========

Reading and writing of trajectories
===================================

Reading and writing with automatic filetype detection
-----------------------------------------------------

The :py:meth:`glotzformats.read` and :py:meth:`glotzformats.write` functions will automatically determine the type of a trajectory from its file extension.
This can be used to quickly load and save :py:class:`~.trajectory.Trajectory` objects.

.. code-block:: python

    import glotzformats as gf
    # Load a GSD file...
    with gf.read('dump.gsd') as traj:
        print(len(traj))
        # ...do things with the trajectory, then output a GTAR file
        gf.write(traj, 'output.tar')

Using reader and writer classes
-------------------------------

Readers and writers are defined in the ``reader`` and ``writer`` modules.
The following code uses the :py:class:`~.reader.PosFileReader` and :py:class:`~.writer.PosFileWriter` as an example.

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
===========

Indexing and slicing
--------------------

Once you read a trajectory, access individual frames or sub-trajectories by indexing and slicing:

.. code-block:: python

    # Select individual frames:
    first_frame = traj[0]
    last_frame = traj[-1]
    n_th_frame = traj[n]
    # and so on

    # Create a sub-trajectory from the ith frame
    # to the (j-1)th frame:
    sub_trajectory = traj[i:j]

    # We can use advanced slicing techniques:
    every_second_frame = traj[::2]
    the_last_ten_frames = traj[-10::]

The actual trajectory data is then either accessed on a *per trajectory* or *per frame* basis.

Trajectory array access
-----------------------

Access positions, orientations and types as coherent numpy arrays, by calling the :py:meth:`~.trajectory.Trajectory.load_arrays` method.
This method will load the complete trajectory into memory and make positions, orientations and types available via properties:

.. code-block:: python

    traj.load_arrays()
    traj.N              # M  -- frame sizes
    traj.positions      # MxNx3 array
    traj.orientations   # MxNx4 array
    traj.types          # MxN array
    traj.type_ids       # MxN array
    traj.type           # list of type names ordered by type_id

    # where M=len(traj), N=max((len(f) for f in traj))

Individual frame access
-----------------------

Inidividual frame objects can be accessed via indexing of a (sub-)trajectory object:

.. code-block:: python

    frame = traj[i]
    frame.box           # Instance of trajectory.box
    frame.positions     # Nx3 array
    frame.orientations  # Nx4 array
    frame.types         # Nx1 array
    frame.data          # A dictionary of lists for each attribute
    frame.data_key      # A list of strings
    frame.shapedef      # A ordered dictionary of instances of ShapeDefinition.

Iterating over trajectories
---------------------------

Iterating over trajectories is the most **memory-efficient** form of data access.
Each frame will be loaded *prior* to access and unloaded *post* access, such that there is only one frame loaded into memory at the same time.

.. code-block:: python

    # Iterate over a trajectory directly for read-only data access
    for frame in traj:
        print(frame.positions)

Efficient modification of trajectories
======================================

Use a combination of reading, writing, and iteration for **memory-efficient** modification of large trajectory data.
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

Loading trajectories into memory
================================

The :py:class:`~.trajectory.Trajectory` class is designed to be *memory-efficient*.
This means that loading all trajectory data into memory requires an explicit call of the :py:meth:`~.Trajectory.load` or :py:meth:`~.Trajectory.load_arrays` methods.

.. code-block:: python

    # Make trajectory data accessible via arrays:
    traj.load_arrays()
    traj.positions

    # Load all frames:
    traj.load()
    frame = traj[i]
    traj.positions    # load() also loads arrays

.. note::

    In general, loading all frames with :py:meth:`~.Trajectory.load` is more expensive than just loading arrays with :py:meth:`~.Trajectory.load_arrays`.
    Loading all frames also loads the arrays.

Sub-trajectories inherit already loaded data:

.. code-block:: python

    traj.load_arrays()
    sub_traj = traj[i:j]
    sub_traj.positions

.. tip::

    If you are only interested in sub-trajectory data, consider to call :py:meth:`~.Trajectory.load` or :py:meth:`~.Trajectory.load_arrays` only for the sub-trajectory.


Example use with HOOMD-blue
===========================

The **glotzformats** frames can be used to initialize HOOMD-blue by creating snapshots with the :py:meth:`~.Frame.make_snapshot` method or by copying the frame data to existing snapshots with the :py:meth:`~.Frame.copyto_snapshot` methods:

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
