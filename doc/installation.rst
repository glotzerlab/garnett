Installation
============

Requirements
------------

Installing the **garnett** package requires Python 3.5+, **numpy**, and **rowan**.

.. note::

    If you need high performance when reading DCD files, please install Cython and build the package from source.
    Packages distributed via conda or pip wheels contain only the pure Python DCD reader.

With conda
----------

To install the package with conda_, execute

.. code:: bash

    $ conda install -c conda-forge garnett

To upgrade, execute

.. code:: bash

    $ conda update garnett

.. _conda: https://conda.io/

.. note::

    This is the recommended installation method.

With pip
--------

To install the package with the package manager pip_, execute

.. _pip: https://docs.python.org/3/installing/index.html

.. code:: bash

    $ pip install garnett --user

To upgrade the package, simply execute the same command with the `--upgrade` option.

.. code:: bash

    $ pip install garnett --user --upgrade

From source
-----------

To install from source, you can clone the git repository and use the ``setup.py`` to install the package.
If Cython is installed, the DCD reader extension will be built with Cython for improved performance.

.. code:: bash

  git clone https://github.com/glotzerlab/garnett.git
  cd garnett
  python setup.py install --user
