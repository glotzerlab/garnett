Installation
============

Requirements
------------

Installing the **glotzformats** package requires python 2.7.x or 3.x, and **numpy**.

With conda
----------

.. sidebar:: Closed-source

    **glotzformats** is not publicly released, installation via conda therefore requires access to the *private* Glotzer channel.

To install the package with conda_, execute

.. code:: bash

    $ conda install glotzformats

To upgrade, execute

.. code:: bash

    $ conda update glotzformats

.. _conda: http://conda.pydata.org

.. note::

    This is the recommended installation method.

With pip
--------

To install the package with the package manager pip_, execute

.. _pip: https://docs.python.org/3.5/installing/index.html

.. code:: bash

    $ pip install git+https://github.com/glotzerlab/glotzformats.git#egg=glotzformats --user

.. note::
    It is highly recommended to install the package into the user space and not as superuser!

To upgrade the package, simply execute the same command with the `--upgrade` option.

.. code:: bash

    $ pip install git+https://github.com/glotzerlab/glotzformats.git#egg=glotzformats --user --upgrade

With git
--------

Alternatively you can clone the git repository and use the ``setup.py`` to install the package.

.. code:: bash

  git clone https://github.com/glotzerlab/glotzformats.git
  cd glotzformats
  python setup.py install --user
