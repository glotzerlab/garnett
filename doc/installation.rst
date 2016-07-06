Installation
============

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

    $ pip install git+https://$USER@bitbucket.org/glotzer/glotz-formats.git#egg=glotzformats --user

.. note::
    It is highly recommended to install the package into the user space and not as superuser!

To upgrade the package, simply execute the same command with the `--upgrade` option.

.. code:: bash

    $ pip install git+https://$USER@bitbucket.org/glotzer/glotz-formats.git#egg=glotzformats --user --upgrade

With git
--------

Alternatively you can clone the git repository and use the ``setup.py`` to install the package.

.. code:: bash

  git clone https://$USER@bitbucket.org/glotzer/glotz-formats.git
  cd glotz-formats
  python setup.py install --user
