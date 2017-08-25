import os
from setuptools import setup

setup(
    name = "cis_interface",
    version = "0.0.0",
    author = "Meagan Lang",
    author_email = "langmm.astro@gmail.com",
    description = ("A framework for combining interdependent models from "
                   "multiple languages."),
    # TODO: propert liscense
    license = "?",
    keywords = "plants simulation models framework",
    # url = "https://github.com/cropsinsilico/cis_interface",
    packages=['cis_interface', 'cis_interface.interface',
              'cis_interface.io', 'cis_interface.drivers'],
    long_description=read('README'),
    # TODO: add classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
