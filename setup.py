import sys

from setuptools import setup, find_packages

if not sys.version_info >= (2,7):
    print("This package requires python version >= 2.7.")
    sys.exit(1)

setup(
    name = 'glotz-formats',
    version = '0.1.8dev1',
    package_dir = {'': 'src'},
    packages = find_packages('src'),

    author = 'Carl Simon Adorf',
    author_email = 'csadorf@umich.edu',
    description = "Samples, parsers and writers for formats used in the Glotzer Group",
    keywords = ['glotzer formats'],

    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Physics",
        ],

    tests_require = ['nose'],
)
