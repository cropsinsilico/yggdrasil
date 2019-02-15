import os
import sys
import warnings
from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib
import versioneer
import install_matlab_engine
import create_coveragerc
cis_ver = versioneer.get_version()
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


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


# Determine if rapidjson installed and parse user defined location
rj_include_dir0 = os.path.join(ROOT_PATH, 'cis_interface', 'rapidjson', 'include')
for idx, arg in enumerate(sys.argv[:]):
    if ((arg.startswith('--rj-include-dir=')
         or arg.startswith('--rapidjson-include-dir='))):
        sys.argv.pop(idx)
        rj_include_dir = os.path.abspath(arg.split('=', 1)[1])
        break
else:
    rj_include_dir = rj_include_dir0
if not os.path.isdir(rj_include_dir):
    raise RuntimeError("RapidJSON sources could not be located. If you "
                       "cloned the git repository, initialize the rapidjson "
                       "git submodule by calling "
                       "'git submodule update --init --recursive' "
                       "from inside the repository.")
if rj_include_dir != rj_include_dir0:
    def_config_file = os.path.join(ROOT_PATH, 'cis_interface', 'defaults.cfg')
    try:
        import ConfigParser as configparser
    except ImportError:
        import configparser
    cfg = configparser.ConfigParser()
    cfg.read(def_config_file)
    if not cfg.has_section('c'):
        cfg.add_section('c')
    cfg.set('c', 'rapidjson_include', rj_include_dir)
    with open(def_config_file, 'w') as fd:
        cfg.write(fd)

    
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
                "pystache", "pyzmq", "psutil",
                "matplotlib<3.0; python_version < '3.5'",
                "matplotlib; python_version >= '3.5'",
                "jsonschema",
                "python-rapidjson; python_version >= '3.4'",
                'pandas<0.21; python_version == "3.4"',
                'pandas; python_version != "3.4"',
                "perf",
                "pint; python_version == '2.7'",
                "unyt; python_version >= '3.4'",
                'sysv_ipc; platform_system != "Windows"']
test_requirements = ['pytest']
# optional_requirements = ["pika<1.0", "astropy"]


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
                            'cistest=cis_interface:run_tsts',
                            'cisschema=cis_interface.command_line:regen_schema',
                            'cisbuildapi_c=cis_interface.command_line:rebuild_c_api',
                            'cisconfig=cis_interface.command_line:update_config',
                            'cistime_comm=cis_interface.command_line:cistime_comm',
                            'cistime_lang=cis_interface.command_line:cistime_lang',
                            'cistime_os=cis_interface.command_line:cistime_os',
                            'cistime_py=cis_interface.command_line:cistime_py',
                            'cisvalidate=cis_interface.command_line:validate_yaml'],
    },
    license="BSD",
)
