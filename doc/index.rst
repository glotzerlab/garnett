.. glotzformats documentation master file, created by
   sphinx-quickstart on Fri Nov  6 18:00:11 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

============================
glotzformats - documentation
============================

.. automodule:: glotzformats
   :members:

Contents:

.. toctree::
   :maxdepth: 2


Quickstart
==========

Reading and writing
-------------------

.. code-block:: python

    from glotzformats.reader import PosFileReader
    from glotzformats.writer import PosFileWriter

    pos_reader = PosFileReader()
    traj = pos_reader.read(open('posfile.pos'))

    pos_writer = PosFileWriter
    with open('posfile2.pos', 'w') as posfile:
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

Example use with HPMC
---------------------

.. code-block:: python

    pos_reader = PosFileReader()
    with open('cube.pos') as posfile:
        traj = pos_reader.read(posfile)

    # Initialize from last frame
    snapshot = traj[-1].make_snapshot()
    system = init.read_snapshot(snapshot)

    # Restore last frame
    snapshot = system.take_snapshot()
    traj[-1].copyto_snapshot(snapshot)


.. notice::

    Use hoomd's native pos-file _writer_ whenever possible.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

