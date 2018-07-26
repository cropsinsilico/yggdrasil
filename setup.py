import os
import sys
import shutil
import warnings
from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib
import versioneer
import install_matlab_engine
import create_coveragerc
cis_ver = versioneer.get_version()


# Attempt to install openalea
try:
    from openalea import lpy
    lpy_installed = True
except ImportError:
    warnings.warn("Could not import openalea.lpy. " +
                  "LPy support will be disabled.")
    lpy_installed = False


# Attempt to install matlab engine
if install_matlab_engine.install_matlab(as_user=('--user' in sys.argv)):
    matlab_installed = True
else:
    warnings.warn("Could not import matlab.engine. " +
                  "Matlab features will be disabled.")
    matlab_installed = False

    
# Set coverage options in .coveragerc
create_coveragerc.create_coveragerc(matlab_installed=matlab_installed,
                                    lpy_installed=lpy_installed)


# Create .rst README from .md and get long description
if os.path.isfile('README.rst'):
    with open('README.rst', 'r') as file:
        long_description = file.read()
elif os.path.isfile('README.md'):
    try:
        import pypandoc
        pypandoc.convert_file('README.md', 'rst', outputfile='README.rst')
        long_description = pypandoc.convert_file('README.md', 'rst')
    except (ImportError, IOError):
        with open('README.md', 'r') as file:
            long_description = file.read()
else:
    raise IOError("Could not find README.rst or README.md")


# Create requirements list based on platform
requirements = ['numpy>=1.13.0', "scipy", "pyyaml",
                "pystache", "nose", "zmq", "psutil",
                "matplotlib", "cerberus", "jsonschema",
                'pandas<0.21; python_version == "3.4"',
                'pandas; python_version != "3.4"',
                "pint", "unyt",
                'sysv_ipc; platform_system != "Windows"']
test_requirements = ['pytest', 'nose']
# optional_requirements = ["pika", "astropy"]


# Warn that local install may not have entry points on path
if '--user' in sys.argv:
    script_dir = os.path.realpath(os.path.join(get_python_lib(),
                                               '../../../bin/'))
    warnings.warn("When installing locally, you may need to add the script " +
                  "directory to your path manually in order to have access " +
                  "to the command line entry points (e.g. cisrun). " +
                  "If 'cisrun' is not a recognized command, try adding " +
                  "'%s' to your PATH." % script_dir)
    
setup(
    name="cis_interface",
    packages=find_packages(),
    include_package_data=True,
    version=cis_ver,
    cmdclass=versioneer.get_cmdclass(),
    description=("A framework for combining interdependent models from "
                 "multiple languages."),
    long_description=long_description,
    author="Meagan Lang",
    author_email="langmm.astro@gmail.com",
    url="https://github.com/cropsinsilico/cis_interface",
    download_url=(
        "https://github.com/cropsinsilico/cis_interface/archive/%s.tar.gz" % cis_ver),
    keywords=["plants", "simulation", "models", "framework"],
    install_requires=requirements,
    tests_require=test_requirements,
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
        "Development Status :: 3 - Alpha",
    ],
    entry_points={
        'console_scripts': ['cisrun=cis_interface.command_line:cisrun',
                            'ciscc=cis_interface.command_line:ciscc',
                            'cisccflags=cis_interface.command_line:cc_flags',
                            'cisldflags=cis_interface.command_line:ld_flags',
                            'cistest=cis_interface:run_nose',
                            'cisschema=cis_interface.command_line:regen_schema',
                            'cisconfig=cis_interface.command_line:update_config'],
    },
    license="BSD",
)
