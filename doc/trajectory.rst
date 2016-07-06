Trajectory API
==============

Instances of :py:class:`~.trajectory.Trajectory` give access to trajectory data stored in files and *file-like* objects.
In the simplest case, trajectories are just a sequence of :py:class:`~.trajectory.Frame` instances.

Trajectories
------------

.. autoclass:: glotzformats.trajectory.Trajectory
   :members:
   :undoc-members:
   :inherited-members:

Frames
------

Trajectory data can be accessed via individual frames.

.. autoclass:: glotzformats.trajectory.Frame
   :members:
   :undoc-members:
   :inherited-members:

Box
---

The box instance gives access to the box of individual frames.

.. autoclass:: glotzformats.trajectory.Box
   :members:
   :undoc-members:
   :inherited-members:


Shape Definitions
-----------------

Shape definitions contain information about the shape of individual particles.

.. autoclass:: glotzformats.trajectory.ShapeDefinition
   :members:
   :undoc-members:
   :inherited-members:

.. autoclass:: glotzformats.trajectory.SphereShapeDefinition
   :members:
   :undoc-members:
   :inherited-members:

.. autoclass:: glotzformats.trajectory.PolyShapeDefinition
   :members:
   :undoc-members:
   :inherited-members:

.. autoclass:: glotzformats.trajectory.ArrowShapeDefinition
   :members:
   :undoc-members:
   :inherited-members:

.. autoclass:: glotzformats.trajectory.FallbackShapeDefinition
   :members:
