#!/bin/sh

conda env remove --yes -n glotzformats-py27-minimal
conda env remove --yes -n glotzformats-py33-minimal
conda env remove --yes -n glotzformats-py34-minimal
conda env remove --yes -n glotzformats-py35-minimal

conda env remove --yes -n glotzformats-py27
conda env remove --yes -n glotzformats-py33
conda env remove --yes -n glotzformats-py34
conda env remove --yes -n glotzformats-py35

echo "Creating environment for python 2.7"
conda create --yes -n glotzformats-py27-minimal python=2.7 numpy
. activate glotzformats-py27-minimal
python setup.py develop
. deactivate
echo "Done."

echo "Creating environment for python 3.3"
conda create --yes -n glotzformats-py33-minimal python=3.3 numpy
. activate glotzformats-py33-minimal
python setup.py develop
. deactivate
echo "Done."

echo "Creating environment for python 3.4"
conda create --yes -n glotzformats-py34-minimal python=3.4 numpy
. activate glotzformats-py34-minimal
python setup.py develop
. deactivate
echo "Done."

echo "Creating environment for python 3.5"
conda create --yes -n glotzformats-py35-minimal python=3.5 numpy
. activate glotzformats-py35-minimal
python setup.py develop
. deactivate
echo "Done."

echo "Creating environment for python 2.7"
conda create --yes -n glotzformats-py27 python=2.7 numpy
. activate glotzformats-py27
pip install git+ssh://git@bitbucket.org/glotzer/libgetar.git#egg=libgetar
python setup.py develop
. deactivate
echo "Done."

echo "Creating environment for python 3.3"
conda create --yes -n glotzformats-py33 python=3.3 numpy
. activate glotzformats-py33
pip install git+ssh://git@bitbucket.org/glotzer/libgetar.git#egg=libgetar
python setup.py develop
. deactivate
echo "Done."

echo "Creating environment for python 3.4"
conda create --yes -n glotzformats-py34 python=3.4 numpy
. activate glotzformats-py34
pip install git+ssh://git@bitbucket.org/glotzer/libgetar.git#egg=libgetar
python setup.py develop
. deactivate
echo "Done."

echo "Creating environment for python 3.5"
conda create --yes -n glotzformats-py35 python=3.5 numpy
. activate glotzformats-py35
pip install git+ssh://git@bitbucket.org/glotzer/libgetar.git#egg=libgetar
python setup.py develop
. deactivate
echo "Done."
