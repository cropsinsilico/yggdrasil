import os
import sys
import shutil
import warnings
from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib
import versioneer
import install_matlab_engine
import update_config
import update_coveragerc
IS_WINDOWS = (sys.platform in ['win32', 'cygwin'])


cis_ver = versioneer.get_version()
# print(cis_ver, type(cis_ver))
# with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as version_file:
#     cis_ver = version_file.read().strip()


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

    
# Create config file if one does not exist and update it to reflect the
# system
usr_config_file = os.path.expanduser(os.path.join('~', '.cis_interface.cfg'))
def_config_file = os.path.join(os.path.dirname(__file__),
                               'cis_interface', 'defaults.cfg')
if not os.path.isfile(usr_config_file):
    shutil.copy(def_config_file, usr_config_file)
update_config.update_config(usr_config_file)


# Set coverage options in .coveragerc
update_coveragerc.update_coveragerc()


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
                'pandas; python_version >= "3.5"',
                'pandas; python_version == "2.7"',
                'pandas<0.21; python_version == "3.4"',
                "pint", "unyt"]
test_requirements = ['pytest']
# optional_requirements = ["pika", "astropy"]
if not IS_WINDOWS:
    requirements.append("sysv_ipc")


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
                            'cisschema=cis_interface.command_line:regen_schema'],
    },
    license="BSD",
)
