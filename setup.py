# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
from setuptools import setup, find_packages
import os
import sys

description = "Samples, parsers, and writers for formats used in the Glotzer Group."

# Import Cython if available and not disabled.
# Cython is disabled for wheel builds so the package is pure Python.
CYTHON = False
try:
    from Cython.Build import cythonize
    import numpy as np
except ImportError:
    print("WARNING: Cython not available!", file=sys.stderr)
else:
    if '--no-cython' in sys.argv:
        print("WARNING: Cython is disabled.", file=sys.stderr)
        sys.argv.remove('--no-cython')
    else:
        CYTHON = True

# Get long description from README.md
try:
    this_path = os.path.dirname(os.path.abspath(__file__))
    fn_readme = os.path.join(this_path, 'README.md')
    with open(fn_readme) as fh:
        long_description = fh.read()
except (IOError, OSError):
    long_description = description


setup(
    name='garnett',
    version='0.7.1',
    packages=find_packages(),

    ext_modules=cythonize('garnett/*.pyx') if CYTHON else [],
    include_dirs=[np.get_include()] if CYTHON else [],

    maintainer='garnett Developers',
    author='Carl Simon Adorf et al.',
    author_email='csadorf@umich.edu',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://garnett.readthedocs.io/",
    download_url="https://pypi.org/project/garnett/",
    keywords='simulation trajectory formats particle',

    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Physics",
    ],

    python_requires='>=3.5, <4',

    install_requires=[
        'deprecation>=2',
        'numpy>=1.14',
        'rowan>=1.2',
        'tqdm>=4.35',
    ],

    tests_require=[
        'ddt',
    ],
)
