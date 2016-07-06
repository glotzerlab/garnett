=================
Readers & Writers
=================

This is the API documentation for all readers and writers provided by **glotzformats**.

General API
===========

Readers and writers are defined in the ``glotzformats.reader`` and ``glotzformats.writer`` modules.
All readers and writers work with **file-like objects** and use the following API:

.. code-block:: python

    reader = glotzformats.reader.Reader()
    writer = glotzformats.writer.Writer()

    with open('trajectory_file') as infile:
        traj = reader.read(infile)

        # Dump to standard out:
        writer.dump(traj)

        # Or to a file:
        with open('dump', 'w') as outfile:
            writer.write(traj, outfile)

.. note::

    Some readers and writers work with **binary** files, which means that when opening those files for reading or writing you need to use a ``rb`` or ``wb`` mode, e.g., ``with open('dump.dcd', 'rb') as infile:``.

File Formats
============

The following collection of readers and writers is ordered by different file formats.

POS-Files
---------

The *POS*-format is a non-standardized *text-based* format for storing trajectory data.
The format is used as primary input/output format for the **injavis** visualization tool.
Its use for large trajectory data is discouraged.

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
HOOMD-blue allows to dump trajectory data in this format.

See also: `<http://gsd.readthedocs.io>`_

.. autoclass:: glotzformats.reader.GSDHOOMDFileReader
    :members:
    :undoc-members:
    :inherited-members:

GeTAR
-----

The *GeTAR*-format is a compressed and highly versatile *binary* format for storing and reading trajectory data.
HOOMD-blue allows to dump trajectory data in this format.

.. autoclass:: glotzformats.reader.GetarFileReader
    :members:
    :undoc-members:
    :inherited-members:

HOOMD-blue XML
--------------

The HOOMD-blue XML-format contains topological information about individual frames and has been depreceated since HOOMD-blue version 2.0.

.. autoclass:: glotzformats.reader.HOOMDXMLFileReader
    :members:
    :undoc-members:
    :inherited-members:

DCD
---

The *dcd*-format is a very storage efficient *binary* format for storing simple trajectory data.
The format contains only data about xyz-positions and the boxes of individual frames.

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
