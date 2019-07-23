Trajectory API
==============

Instances of :py:class:`~.trajectory.Trajectory` give access to trajectory data stored in files and *file-like* objects.
In the simplest case, trajectories are just a sequence of :py:class:`~.trajectory.Frame` instances.

Trajectories
------------

.. autoclass:: garnett.trajectory.Trajectory
   :members:
   :undoc-members:
   :inherited-members:

Frames
------

Trajectory data can be accessed via individual frames.

.. autoclass:: garnett.trajectory.Frame
   :members:
   :undoc-members:
   :inherited-members:

Box
---

The box instance gives access to the box of individual frames.

.. autoclass:: garnett.trajectory.Box
   :members:
   :undoc-members:
   :inherited-members:
