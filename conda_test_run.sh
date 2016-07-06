#!/bin/bash

source activate glotzformats-py27-minimal
python -m unittest discover tests ${@}

source activate glotzformats-py33-minimal
python -m unittest discover tests ${@}

source activate glotzformats-py34-minimal
python -m unittest discover tests ${@}

source activate glotzformats-py35-minimal
python -m unittest discover tests ${@}

source activate glotzformats-py27
python setup.py build_ext --inplace
python -m unittest discover tests ${@}

source activate glotzformats-py33
python setup.py build_ext --inplace
python -m unittest discover tests ${@}

source activate glotzformats-py34
python setup.py build_ext --inplace
python -m unittest discover tests ${@}

source activate glotzformats-py35
python setup.py build_ext --inplace
python -m unittest discover tests ${@}
