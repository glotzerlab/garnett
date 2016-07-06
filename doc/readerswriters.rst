=================
Readers & Writers
=================

This is the API documentation for all readers and writers provided by **glotzformats**.

General API
===========

Readers and writers are defined in the :py:mod:`~.reader` and :py:mod:`~.writer` modules.
All readers and writers work with **file-like objects** and use the following API:

.. code-block:: python

    reader = glotzformats.reader.Reader()
    writer = glotzformats.writer.Writer()

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

        dcd_reader = glotzformats.reader.DCDFileReader()
        with open('dump.dcd', 'rb') as dcdfile:
            dcd_traj = dcd_reader.read(dcdfile)

File Formats
============

The following collection of readers and writers is ordered by different file formats.

POS-Files
---------

The *POS*-format is a non-standardized *text-based* format which is human-readable, but very inefficient for storing of trajectory data.
The format is used as primary input/output format for the **injavis** visualization tool.
HOOMD-blue provides a writer for this format, which is classified as deprecated since version 2.0.

.. autoclass:: glotzformats.reader.PosFileReader
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: glotzformats.writer.PosFileWriter
    :members:
    :undoc-members:
    :inherited-members:

GSD (HOOMD-blue schema)
-----------------------

The *GSD*-format is a highly efficient and versatile *binary* format for storing and reading trajectory data.
HOOMD-blue provides a writer for this format.

See also: `<http://gsd.readthedocs.io>`_

.. autoclass:: glotzformats.reader.GSDHOOMDFileReader
    :members:
    :undoc-members:
    :inherited-members:

GeTAR
-----

The *GeTAR*-format is a highly versatile, *binary* format for storing and reading trajectory data.
HOOMD-blue provides a writer for this format.

.. autoclass:: glotzformats.reader.GetarFileReader
    :members:
    :undoc-members:
    :inherited-members:

HOOMD-blue XML
--------------

The HOOMD-blue XML-format contains topological information about one individual frame.
HOOMD-blue provides a writer for this format, which is classified as deprecated since version 2.0.

.. autoclass:: glotzformats.reader.HOOMDXMLFileReader
    :members:
    :undoc-members:
    :inherited-members:

DCD
---

The *DCD*-format is a very storage efficient *binary* format for storing simple trajectory data.
The format contains only data about xyz-positions and the boxes of individual frames.

HOOMD-blue provides a writer for this format with a special dialect for 2-dimensional systems.
The *glotzformats* dcd-reader is capable of reading both the standard and the 2-dim. dialect.

.. note::
    Unlike most other readers, the :py:class:`~.reader.DCDFileReader` will return an instance
    of :py:class:`~.DCDTrajectory`, which is optimized for the DCD-format.
    This special trajectory class provides the :py:meth:`~.DCDTrajectory.xyz` method for accessing xyz-coordinates with minimal overhead.

.. autoclass:: glotzformats.reader.DCDFileReader
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: glotzformats.dcdfilereader.DCDTrajectory
    :members:

.. autoclass:: glotzformats.reader.PyDCDFileReader

CIF
---

The *cif*-format is a *text-based* format primarily used in the context of crystallography.

.. autoclass:: glotzformats.writer.CifFileWriter
    :members:
    :undoc-members:
    :inherited-members:
