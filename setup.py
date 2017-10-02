import os
import sys
import shutil
import warnings
from setuptools import setup, find_packages
PY_MAJOR_VERSION = sys.version_info[0]
PY2 = (PY_MAJOR_VERSION == 2)

cis_ver = "0.1.3"
    
try:
    import matlab.engine
    matlab_installed = True
except:
    warnings.warn("Could not import matlab.engine. " +
                  "Matlab features will be disabled.")
    matlab_installed = False
        
# Create config file if one does not exist
usr_config_file = os.path.expanduser(os.path.join('~', '.cis_interface.cfg'))
def_config_file = os.path.join(os.path.dirname(__file__),
                               'cis_interface', 'defaults.cfg')
if not os.path.isfile(usr_config_file):
    shutil.copy(def_config_file, usr_config_file)

# Set coverage options in .coveragerc
cov_installed = False
try:
    from coverage.config import HandyConfigParser
    cov_installed = True
except ImportError:
    pass
if cov_installed:
    # Read options
    covrc = '.coveragerc'
    cp = HandyConfigParser("")
    cp.read(covrc)
    # Exclude rules for all files
    if not cp.has_section('report'):
        cp.add_section('report')
    if cp.has_option('report', 'exclude_lines'):
        excl_list = cp.getlist('report', 'exclude_lines')
    else:
        excl_list = []
    # Funcs to add/rm rules
    def add_excl_rule(excl_list, new_rule):
        if new_rule not in excl_list:
            excl_list.append(new_rule)
        return excl_list
    def rm_excl_rule(excl_list, new_rule):
        if new_rule in excl_list:
            excl_list.remove(new_rule)
        return excl_list
    # Python version
    verlist = [2, 3]
    for v in verlist:
        vincl = 'pragma: Python %d' % v
        if PY_MAJOR_VERSION == v:
            excl_list = rm_excl_rule(excl_list, vincl)
        else:
            excl_list = add_excl_rule(excl_list, vincl)
    # Matlab
    if matlab_installed:
        excl_list = add_excl_rule(excl_list, 'pragma: no matlab')
        excl_list = rm_excl_rule(excl_list, 'pragma: matlab')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: matlab')
        excl_list = rm_excl_rule(excl_list, 'pragma: no matlab')
    # Add new rules
    cp.set('report', 'exclude_lines', '\n'+'\n'.join(excl_list))
    # Write
    with open(covrc, 'w') as fd:
        cp.write(fd)

# Create .rst README from .md and get long description
try:
    import pypandoc
    pypandoc.convert_file('README.md', 'rst', outputfile='README.rst')
    long_description = pypandoc.convert_file('README.md', 'rst')
except (ImportError, IOError):
    if os.path.isfile('README.rst'):
        with open('README.rst', 'r') as file:
            long_description = file.read()
    elif os.path.isfile('README.md'):
        with open('README.md', 'r') as file:
            long_description = file.read()
    else:
        raise IOError("Could not find README.rst or README.md")
    
setup(
    name="cis_interface",
    packages=find_packages(),
    include_package_data=True,
    version=cis_ver,
    description=("A framework for combining interdependent models from "
                 "multiple languages."),
    long_description=long_description,
    author="Meagan Lang",
    author_email="langmm.astro@gmail.com",
    url="https://github.com/cropsinsilico/cis_interface",
    download_url = "https://github.com/cropsinsilico/cis_interface/archive/%s.tar.gz" % cis_ver,
    keywords=["plants", "simulation", "models", "framework"],
    install_requires=["sysv_ipc", "pika", "pyyaml", "pystache", "scipy"],
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
    entry_points = {
        'console_scripts': ['cisrun=cis_interface.command_line:cisrun'],
    },
    license="BSD",
)
