#!/bin/sh

source activate glotzformats-py27
python -m unittest discover tests ${@}

source activate glotzformats-py33
python -m unittest discover tests ${@}

source activate glotzformats-py34
python -m unittest discover tests ${@}

source activate glotzformats-py35
python -m unittest discover tests ${@}