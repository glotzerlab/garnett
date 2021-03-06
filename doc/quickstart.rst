==========
Quickstart
==========

Reading and writing of trajectories
===================================

Reading and writing with automatic filetype detection
-----------------------------------------------------

The :py:meth:`garnett.read` and :py:meth:`garnett.write` functions will automatically determine the type of a trajectory from its file extension.
This can be used to quickly load and save :py:class:`~.trajectory.Trajectory` objects.

.. code-block:: python

    import garnett
    # Load a GSD file...
    with garnett.read('dump.gsd') as traj:
        print(len(traj))
        # ...do things with the trajectory, then output a GTAR file
        garnett.write(traj, 'output.tar')

Using reader and writer classes
-------------------------------

Readers and writers are defined in the :py:mod:`~.reader` and :py:mod:`~.writer` modules.
The following code uses the :py:class:`~.reader.PosFileReader` and :py:class:`~.writer.PosFileWriter` as an example.

.. code-block:: python

    from garnett.reader import PosFileReader
    from garnett.writer import PosFileWriter

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

The complete trajectory may be loaded into memory by calling the :py:meth:`~.trajectory.Trajectory.load_arrays` method.
This will allow access to fields such as position, orientation, and velocity across all frames and particles.
Supported properties are listed below:

.. code-block:: python

    traj.load_arrays()
    traj.box             # M
    traj.N               # M
    traj.types           # MxT
    traj.type_shapes     # MxT
    traj.typeid          # MxN
    traj.position        # MxNx3
    traj.orientation     # MxNx4
    traj.velocity        # MxNx3
    traj.mass            # MxN
    traj.charge          # MxN
    traj.diameter        # MxN
    traj.moment_inertia  # MxNx3
    traj.angmom          # MxNx4
    traj.image           # MxNx3

    # M is the number of frames
    # T is the number of particle types in a frame
    # N is the number of particles in a frame

Individual frame access
-----------------------

Individual frames can be accessed via indexing a (sub-)trajectory object:

.. code-block:: python

    frame = traj[i]
    frame.box              # garnett.trajectory.Box object
    frame.N                # scalar, number of particles
    frame.types            # T, string names for each type
    frame.type_shapes      # T, list of shapes for each type
    frame.typeid           # N, type indices of each particle
    frame.position         # Nx3
    frame.orientation      # Nx4
    frame.velocity         # Nx3
    frame.mass             # N
    frame.charge           # N
    frame.diameter         # N
    frame.moment_inertia   # Nx3
    frame.angmom           # Nx4
    frame.image            # Nx3
    frame.data             # Dictionary of lists for each attribute
    frame.data_key         # List of strings

Iterating over trajectories
---------------------------

Iterating over trajectories is the most **memory-efficient** form of data access.
Each frame will be loaded *prior* to access and unloaded *post* access, such that there is only one frame loaded into memory at the same time.

.. code-block:: python

    # Iterate over a trajectory directly for read-only data access
    for frame in traj:
        print(frame.position)

Efficient modification of trajectories
======================================

Use a combination of reading, writing, and iteration for **memory-efficient** modification of large trajectory data.
This is an example on how to modify frames in-place:

.. code-block:: python

    import numpy as np
    import garnett

    def center(frame):
        frame.position -= np.average(frame.position, axis=0)
        return frame

    with garnett.read('in.pos') as traj:
        traj_centered = Trajectory((center(frame) for frame in traj))
        garnett.write(traj_centered, 'out.pos')

Loading trajectories into memory
================================

The :py:class:`~.trajectory.Trajectory` class is designed to be *memory-efficient*.
This means that loading all trajectory data into memory requires an explicit call of the :py:meth:`~.Trajectory.load` or :py:meth:`~.Trajectory.load_arrays` methods.

.. code-block:: python

    # Make trajectory data accessible via arrays:
    traj.load_arrays()
    traj.position

    # Load all frames:
    traj.load()
    frame = traj[i]
    traj.position    # load() also loads arrays

.. note::

    In general, loading all frames with :py:meth:`~.Trajectory.load` is more expensive than just loading arrays with :py:meth:`~.Trajectory.load_arrays`.
    Loading all frames also loads the arrays.

Sub-trajectories inherit already loaded data:

.. code-block:: python

    traj.load_arrays()
    sub_traj = traj[i:j]
    sub_traj.position

.. tip::

    If you are only interested in sub-trajectory data, consider to call :py:meth:`~.Trajectory.load` or :py:meth:`~.Trajectory.load_arrays` only for the sub-trajectory.


Example use with HOOMD-blue
===========================

The **garnett** frames can be used to initialize HOOMD-blue simulations by creating snapshots or copying the frame data to existing snapshots with the :py:meth:`~.Frame.to_hoomd_snapshot` method:

.. code-block:: python

    import garnett
    import hoomd

    with garnett.read('cube.pos') as traj:

        # Initialize from last frame
        snapshot = traj[-1].to_hoomd_snapshot()
        system = hoomd.init.read_snapshot(snapshot)

        # Restore last frame
        snapshot = system.take_snapshot()
        traj[-1].to_hoomd_snapshot(snapshot)
