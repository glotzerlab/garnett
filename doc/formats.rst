=======
Formats
=======

The FileFormat wrapper class
============================

The **glotzformats** package contains classes which can be used as file format definitions in the :py:mod:`~.formats` module.
All of these classes inherit from the :py:class:`~.formats.FileFormat` class, which is a wrapper around a *file-like* object.

.. code-block:: python
    
    class MyFormat(glotzformats.format.FileFormat)
        pass

    my_file = MyFormat(open('myfile.txt'))


.. autoclass:: glotzformats.formats.FileFormat
    :members:

Overview of format classes
==========================

The following list contains all file format classes defined wihtin the :py:mod:`~.formats` module:

.. autoclass:: glotzformats.formats.XMLFile
    :members:

.. autoclass:: glotzformats.formats.SnapshotFile
    :members:

.. autoclass:: glotzformats.formats.TrajectoryFile
    :members:

.. autoclass:: glotzformats.formats.HOOMDXMLSnapshotFile
    :members:

.. autoclass:: glotzformats.formats.HoomdXMLSnapshotFile
    :members:

.. autoclass:: glotzformats.formats.GSDTrajectoryFile
    :members:

.. autoclass:: glotzformats.formats.HOOMDGSDTrajectoryFile
    :members:

.. autoclass:: glotzformats.formats.PosTrajectoryFile
    :members:

.. autoclass:: glotzformats.formats.DCDTrajectoryFile
    :members:

.. autoclass:: glotzformats.formats.GetarTrajectoryFile
    :members:

.. autoclass:: glotzformats.formats.CifTrajectoryFile
    :members:

.. autoclass:: glotzformats.formats.LogFile
    :members:

.. autoclass:: glotzformats.formats.AnalysisLogFile
    :members:

.. autoclass:: glotzformats.formats.SourceCodeFile
    :members:

.. autoclass:: glotzformats.formats.SourceCodeHeaderFile
    :members:

.. autoclass:: glotzformats.formats.ScriptFile
    :members:

.. autoclass:: glotzformats.formats.SimulationInputFile
    :members:

.. autoclass:: glotzformats.formats.HoomdInputFile
    :members:

.. autoclass:: glotzformats.formats.PolyhedraVertices
    :members:
