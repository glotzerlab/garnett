=================
Readers & Writers
=================

This is the API documentation for all readers and writers provided by **garnett**.

Automatic reader/writer
=======================

.. autofunction:: garnett.read

.. autofunction:: garnett.write


General API
===========

Readers and writers are defined in the :py:mod:`~.reader` and :py:mod:`~.writer` modules.
All readers and writers work with **file-like objects** and use the following API:

.. code-block:: python

    reader = garnett.reader.Reader()
    writer = garnett.writer.Writer()

    with open('trajectory_file') as infile:
        traj = reader.read(infile)

        # Dump to a string:
        pos = writer.dump(traj)

        # Write to standard out:
        writer.write(traj)

        # or directly to a file:
        with open('dump', 'w') as outfile:
            writer.write(traj, outfile)

.. important::

    Some readers and writers work with **binary** files, which means that when opening those files for reading or writing you need to use the ``rb`` or ``wb`` mode.
    This applies for example to DCD-files:

    .. code-block:: python

        dcd_reader = garnett.reader.DCDFileReader()
        with open('dump.dcd', 'rb') as dcdfile:
            dcd_traj = dcd_reader.read(dcdfile)

File Formats
============

This table outlines the supported properties of each format reader and writer.

+--------+-----------+-----+--------------+------------+-------+-----------------------------------+
| Format | Position | Box | Orientation | Velocity | Shape | Additional Properties (See below) |
+--------+-----------+-----+--------------+------------+-------+-----------------------------------+
|    POS |     RW    |  RW |      RW      |    N/A+    |   RW  |                N/A                |
+--------+-----------+-----+--------------+------------+-------+-----------------------------------+
|    GSD |     RW    |  RW |      RW      |     RW     |   RW  |                RW                 |
+--------+-----------+-----+--------------+------------+-------+-----------------------------------+
|   GTAR |     RW    |  RW |      RW      |     RW     |   RW  |                RW                 |
+--------+-----------+-----+--------------+------------+-------+-----------------------------------+
|    CIF |     RW    |  RW |      N/A     |     N/A    |  N/A  |                N/A                |
+--------+-----------+-----+--------------+------------+-------+-----------------------------------+
|    DCD |     R     |  R  |       R      |      R     |  N/A  |                N/A                |
+--------+-----------+-----+--------------+------------+-------+-----------------------------------+
|    XML |     R     |  R  |       R      |      R     |  N/A  |                N/A                |
+--------+-----------+-----+--------------+------------+-------+-----------------------------------+

* RW indicates garnett can read and write on this format.
* R indicates garnett can only read.
* N/A indicates the format does not support storing this property.
* Additional Properties:
    - Mass
    - Charge
    - Diameter
    - Angular momentum
    - Moment of inertia
    - Image

The following collection of readers and writers is ordered by different file formats.

POS-Files
---------

The *POS*-format is a non-standardized *text-based* format which is human-readable, but very inefficient for storing of trajectory data.
The format is used as primary input/output format for the **injavis** visualization tool.
HOOMD-blue provides a writer for this format, which is classified as deprecated since version 2.0.

.. autoclass:: garnett.reader.PosFileReader
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: garnett.writer.PosFileWriter
    :members:
    :undoc-members:
    :inherited-members:

GSD (HOOMD-blue schema)
-----------------------

The *GSD*-format is a highly efficient and versatile *binary* format for storing and reading trajectory data.
HOOMD-blue provides a writer for this format.

See also: `<http://gsd.readthedocs.io>`_

.. autoclass:: garnett.reader.GSDHOOMDFileReader
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: garnett.writer.GSDHOOMDFileWriter
    :members:
    :undoc-members:
    :inherited-members:

GeTAR
-----

The *GeTAR*-format is a highly versatile, *binary* format for storing and reading trajectory data.
HOOMD-blue provides a writer for this format.

See also: `<https://libgetar.readthedocs.io>`_

.. autoclass:: garnett.reader.GetarFileReader
    :members:
    :undoc-members:
    :inherited-members:

HOOMD-blue XML
--------------

The HOOMD-blue XML-format contains topological information about one individual frame.
HOOMD-blue provides a writer for this format, which is classified as deprecated since version 2.0.

.. autoclass:: garnett.reader.HOOMDXMLFileReader
    :members:
    :undoc-members:
    :inherited-members:

DCD
---

The *DCD*-format is a very storage efficient *binary* format for storing simple trajectory data.
The format contains only data about particle positions and the simulation boxes of individual frames.

HOOMD-blue provides a writer for this format with a special dialect for 2-dimensional systems.
The *garnett* dcd-reader is capable of reading both the standard and the 2-dim. dialect.

.. note::
    Unlike most other readers, the :py:class:`~.reader.DCDFileReader` will return an instance
    of :py:class:`~.DCDTrajectory`, which is optimized for the DCD-format.
    This special trajectory class provides the :py:meth:`~.DCDTrajectory.xyz` method for accessing xyz-coordinates with minimal overhead.

.. autoclass:: garnett.reader.DCDFileReader
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: garnett.dcdfilereader.DCDTrajectory
    :members:

.. autoclass:: garnett.reader.PyDCDFileReader

CIF
---

The *cif*-format is a *text-based* format primarily used in the context of crystallography.

.. autoclass:: garnett.reader.CifFileReader
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: garnett.writer.CifFileWriter
    :members:
    :undoc-members:
    :inherited-members:
