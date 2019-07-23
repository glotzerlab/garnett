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
    version='0.4.1',
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

    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, <4',

    install_requires=[
        'rowan>=0.5'
    ],

    tests_require=[
        'nose',
        'ddt'
    ],
)
