Credits
=======

Garnett Developers
------------------

The following people have contributed to the :py:mod:`garnett` package.

Carl Simon Adorf, University of Michigan

    * Original Author
    * Former Maintainer
    * Trajectory classes
    * Shapes classes
    * Testing framework
    * CIF file writer
    * DCD file reader
    * GSD file reader
    * HOOMD XML file reader
    * POS file reader
    * POS file writer

Richmond Newman, University of Michigan

    * Original Author
    * POS file reader

Matthew Spellings, University of Michigan

    * CIF file reader
    * GETAR file reader

Julia Dshemuchadse, University of Michigan

    * CIF file writer

Vyas Ramasubramani, University of Michigan

    * GSD file writer

Bradley Dice, University of Michigan

    * Maintainer
    * GETAR file writer
    * Support for additional frame properties
    * Improved support for parsing and writing particle shapes
    * Refactored ``types``, ``typeid``, ``type_shapes`` to match HOOMD conventions
    * Expanded support for CIF ``_atom_site_label`` types
    * Revised API for interfacing with frame data and HOOMD snapshots

Sophie Youjung Lee, University of Michigan

    * Former Maintainer
    * Universal read and write functions

Luis Y. Rivera-Rivera, University of Michigan

    * Maintainer
    * Various bugs and documentation fixes/updates
    * Implemented error handling for unstored properties
    * Improved dimension detection on GTAR and POS readers
    * Enabled GSD v2.0.0 compatibility
    * Added ``box`` to loadable trajectory attributes

Kelly Wang, University of Michigan

    * Maintainer

Paul Dodd, University of Michigan

Erin Teich, University of Michigan

Pablo Damasceno, University of Michigan

James Proctor, University of Michigan

Jens Glaser, University of Michigan

Mayank Agrawal, University of Michigan

Eric Harper, University of Michigan

Rose Cersonsky, University of Michigan

James Antonaglia, University of Michigan

Chengyu Dai, University of Michigan

Tim Moore, University of Michigan

    * GSD 2.0 compatibility

Source code
-----------

GSD is used to construct trajectory objects from GSD files and is available at https://github.com/glotzerlab/gsd.
The files :code:`garnett/gsdhoomd.py` and :code:`garnett/pygsd.py` are directly copied from the GSD source code.
GSD is used under the BSD license::

    Copyright (c) 2016-2019 The Regents of the University of Michigan
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
