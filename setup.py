import os
import shutil
from setuptools import setup, find_packages

# Create config file if one does not exist
usr_config_file = os.path.expanduser(os.path.join('~', '.cis_interface.cfg'))
def_config_file = os.path.join(os.path.dirname(__file__),
                               'cis_interface', 'defaults.cfg')
if not os.path.isfile(usr_config_file):
    shutil.copy(def_config_file, usr_config_file)

try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst')
except (ImportError, IOError):
    with open('README.md') as file:
        long_description = file.read()

setup(
    name="cis_interface",
    packages=find_packages(),
    package_data={'cis_interface': [
        'defaults.cfg',
        'dataio/*.h', 'dataio/*.hpp',
        'drivers/matlab_screenrc',
        'interface/*.h', 'interface/*.hpp', 'interface/*.m',
        'tests/scripts/*', 'tests/data/*'],
    include_package_data=True,
    version="0.0.0",
    description=("A framework for combining interdependent models from "
                 "multiple languages."),
    long_description=long_description,
    author="Meagan Lang",
    author_email="langmm.astro@gmail.com",
    # TODO: Update url
    # url="https://github.com/cropsinsilico/cis_interface",
    keywords=["plants", "simulation", "models", "framework"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: C",
        "Programming Language :: C++",
        "Programming Language :: ML",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Development Status :: 3 - Alpha",
    ],
    license="BSD",
)
