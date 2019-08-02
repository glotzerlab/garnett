Installation
============

Requirements
------------

Installing the **garnett** package requires Python 2.7 or 3.5+, **numpy**, and **rowan**.

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

.. _pip: https://docs.python.org/3.5/installing/index.html

.. code:: bash

    $ pip install git+https://github.com/glotzerlab/garnett.git#egg=garnett --user

To upgrade the package, simply execute the same command with the `--upgrade` option.

.. code:: bash

    $ pip install git+https://github.com/glotzerlab/garnett.git#egg=garnett --user --upgrade

With git
--------

Alternatively you can clone the git repository and use the ``setup.py`` to install the package.

.. code:: bash

  git clone https://github.com/glotzerlab/garnett.git
  cd garnett
  python setup.py install --user
