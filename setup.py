from setuptools import setup, find_packages

setup(
    name = 'glotz-formats',
    version = '0.1.0dev',
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

    install_requires=['numpy'],

    tests_require = ['nose'],
)
