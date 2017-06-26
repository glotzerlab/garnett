from __future__ import print_function
import sys

from setuptools import setup, find_packages
try:
    from Cython.Build import cythonize
    import numpy as np
except ImportError:
    print("WARNING: Cython not available!", file=sys.stderr)
    CYTHON = False
else:
    CYTHON = True

if not sys.version_info >= (2, 7):
    print("This package requires python version >= 2.7.")
    sys.exit(1)

setup(
    name='glotzformats',
    version='0.4.0',
    packages=find_packages(),

    ext_modules=cythonize('glotzformats/*.pyx') if CYTHON else [],
    include_dirs=[np.get_include()] if CYTHON else [],

    author='Carl Simon Adorf',
    author_email='csadorf@umich.edu',
    description="Samples, parsers, and writers for formats used "
                "in the Glotzer Group",
    keywords=['glotzer formats'],

    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Physics",
    ],

    tests_require=['nose', 'ddt'],
)
