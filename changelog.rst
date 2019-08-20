=========
Changelog
=========

The **garnett** package follows `semantic versioning <https://semver.org/>`_.

Version 0.5
===========

[0.5.0] -- 2019-0x-xx
---------------------
Added
+++++
  - Added `rowan <https://rowan.readthedocs.io/en/latest/>`_ as a dependency.
  - Add GETAR file reader/writer.
  - Add ``shape_dict`` representation to ``Shape`` classes.
  - Add support for particle properties:

    - mass
    - charge
    - diameter
    - image
    - moment of inertia
    - angular momentum

  - Add support for reading/writing shapes in GSD via HOOMD-HPMC state.
  - Add universal reader/writer with format detection.
  - Add orientable attribute to spheres.
  - Extend list of supported shape classes:

    - ellipsoid
    - polygon
    - spheropolygon
    - convex polyhedron
    - convex spheropolyhedron

Changed
+++++++
  - Raise ``AttributeError`` if accessing a frame or trajectory property not defined in the file.
  - Rename several existing shape classes.
  - Improve unit test coverage.
  - Revise documentation.
  - Move shape definitions to separate module.

Deprecated
++++++++++
  - Tests for Python 2 are no longer updated (Python 2 support will be dropped in the next minor release).

Removed
+++++++
  - Remove acceleration as supported property.
  - Remove the ``read_gsd_shape_data`` flag from GSD reader.

Version 0.4
===========

[0.4.1] -- 2017-08-23
---------------------

Fixed
+++++
  - Fix minor bug related to QR check for 2d boxes.

[0.4.0] -- 2017-06-26
---------------------

Added
+++++
  - Add readers/writers:

    - CIF reader
    - GSD writer

  - Support shape definitions:

    - spheropolyhedron
    - polyunion
    - convex polyhedron union

  - Add ``gf2pos`` script - convert to pos-file from any supported format.
  - Add shape definitions to ``GetarFileReader``.
  - Interpret the pos-file rotation key word.

Changed
+++++++
  - ``GetarFileReader`` skips records that have a non-empty group field.
  - Improve algorithm for the normalization of frames with non-standard box.
  - Various documentation updates.

Version 0.3
===========

[0.3.9] -- 2017-01-30
---------------------

Added
+++++
  - The ``GSDReader`` now reads velocities.
  - Support ``PolyV`` shape definitions.

Changed
+++++++
  - Update documentation concerning the conversion of rotations from quaternions to euler angles.

Fixed
+++++
  - Fix bug related to trajectory arrays when slicing the array.

[0.3.8] -- 2016-12-21
---------------------

Fixed
+++++
  - Hot fix: Negative euler angles were not read correctly in skewed boxes using the ``DCDFileReader``.

[0.3.7] -- 2016-11-07
---------------------

Added
+++++
  - Add the ``whence`` argument to the file format's seek method.

Fixed
+++++
  - Fix bug in ``DCDfilereader`` leading to incorrect box dimensions to be read for skewed boxes. Cubic or squared boxes are not affected.

[0.3.6] -- 2016-10-20
---------------------

Fixed
+++++
  - Fix quaternion to euler angle conversion example in the DCD file reader documentation.

[0.3.5] -- 2016-09-20
---------------------

Changed
+++++++
  - ``GSDHOOMDFileReader`` uses the native GSD library if installed.
  - Reduced warning verbosity.

Fixed
+++++
  - Fix bug that caused the ``GSDHOOMDFileReader`` to ignore dimensions specified in the GSD file.

[0.3.4] -- 2016-09-08
---------------------

Added
+++++
  - Support velocities in HOOMD-blue XML files.
  - Support ``SphereUnionShape`` in ``PosFileReader``.

Changed
+++++++
  - Support Pos-Files using the keyword 'box' instead of 'boxMatrix'

Fixed
+++++
  - Fix bug in ``PosFileReader`` which occured with non-standard pos-file in python 3.5
  - Fix bug, which occured when constructing frames from raw frames using box instances instead of a box matrix.

[0.3.3] -- 2016-07-19
---------------------

Fixed
+++++
  - Fix bug related to 2-dimensional systems and a box z-dimensions not equal to 1.

[0.3.2] -- 2016-07-15
---------------------

Added
+++++
  - Add ``trajectory.N``, ``trajectory.type`` and ``trajectory.type_ids`` as an alternative mode to access frame length and type information.

Fixed
+++++
  - Fix bug in ``GSDHOOMDFileReader`` when not providing template frame.

[0.3.1] -- 2016-07-08
---------------------

Changed
+++++++
  - Update the GSD hoomd module.

[0.3.0] -- 2016-07-06
---------------------

Added
+++++
  - Provide a highly optimized cythonized ``DCDFileReader``.
  - Allow trajectory data acess via coherent numpy arrays.
  - Make snapshot creation and copying HOOMD-blue 2.0 compatible.

Changed
+++++++

  - Update the GSD module.
  - Improve the ``Box`` class documentation.
  - Overall improvement of the documentation.

Fixed
+++++
  - Fix and optimize the pure-python ``DCDFileReader``.

Version 0.2
===========

[0.2.1] -- 2016-07-10
---------------------

Fixed
+++++
  - Fix an issue with injavis pos-files causing parser errors.

[0.2.0] -- 2016-04-28
---------------------

Fixed
+++++
  - Fix HOOMD-blue snapshot type issue.

Version 0.1
===========

[0.1.9] -- 2016-04-09
---------------------

Added
+++++
  - Add ``GSDHoomdFileReader``.

Fixed
+++++
  - Fix type issue in ``HoomdBlueXMLFileReader``.

[0.1.8] -- 2016-04-04
---------------------

Added
+++++
  - Add ``HoomdBlueXMLFileReader``.
  - Add ``DCDFileReader``.
  - Add ``CifFileWriter``.
  - Add ``GetarFileReader``.

Fixed
+++++
  - Fix type issue in DCD.


[0.1.6] -- 2016-01-28
---------------------

Changed
+++++++
  - Extend FileFormat API to increase file-like compatibility.

Fixed
+++++
  - Fixed ``box_matrix`` calculation.

[0.1.5] -- 2016-01-11
---------------------

Changed
+++++++
  - Frames only loaded into memory on demand.
  - Improved trajectory iteration logic.

No change logs prior to v0.1.5
------------------------------
