# Copyright (c) 2019 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
from __future__ import print_function
from setuptools import setup, find_packages
import sys

try:
    from Cython.Build import cythonize
    import numpy as np
except ImportError:
    print("WARNING: Cython not available!", file=sys.stderr)
    CYTHON = False
else:
    CYTHON = True

setup(
    name='garnett',
    version='0.6.0',
    packages=find_packages(),

    ext_modules=cythonize('garnett/*.pyx') if CYTHON else [],
    include_dirs=[np.get_include()] if CYTHON else [],

    author='Carl Simon Adorf',
    author_email='csadorf@umich.edu',
    description="Samples, parsers, and writers for formats used in the Glotzer Group",
    keywords='simulation trajectory formats particle',

    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Physics",
    ],

    python_requires='>=3.5, <4',

    install_requires=[
        'rowan>=0.5'
    ],

    tests_require=[
        'nose',
        'ddt'
    ],
)
