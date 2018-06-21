import os
import sys
import pprint
import shutil
import warnings
import subprocess
import tempfile
from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib
PY_MAJOR_VERSION = sys.version_info[0]
PY2 = (PY_MAJOR_VERSION == 2)
IS_WINDOWS = (sys.platform in ['win32', 'cygwin'])

cis_ver = "0.3"


try:
    from openalea import lpy
    lpy_installed = True
except ImportError:
    warnings.warn("Could not import openalea.lpy. " +
                  "LPy support will be disabled.")
    lpy_installed = False


def install_matlab():
    r"""Attempt to install the MATLAB engine API for Python."""
    # Check to see if its already installed
    try:
        import matlab.engine
        return True
    except ImportError:
        pass
    # Get location of matlab root
    mtl_id = '=MATLABROOT='
    cmd = "fprintf('" + mtl_id + "%s" + mtl_id + "', matlabroot); exit();"
    mtl_cmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
               '-r', '%s' % cmd]
    try:
        mtl_proc = subprocess.check_output(mtl_cmd)
        if PY_MAJOR_VERSION == 3:
            mtl_proc = mtl_proc.decode("utf-8")
    except BaseException:
        return False
    if mtl_id not in mtl_proc:
        return False
    mtl_root = mtl_proc.split(mtl_id)[-2]
    # Install engine API
    mtl_setup = os.path.join(mtl_root, 'extern', 'engines', 'python')
    if not os.path.isdir(mtl_setup):
        return False
    blddir = os.path.join(os.path.expanduser('~'), 'matlab_python_api')
    if not os.path.isdir(blddir):
        os.mkdir(blddir)
    cmd = [sys.executable, 'setup.py',
           'build', '--build-base=%s' % blddir,
           'install']
    if '--user' in sys.argv:
        cmd.append('--user')
    try:
        result = subprocess.check_output(cmd, cwd=mtl_setup)
        if PY_MAJOR_VERSION == 3:
            result = result.decode("utf-8") 
        print(result)
    except subprocess.CalledProcessError:
        return False
    return True


if install_matlab():
    matlab_installed = True
else:
    warnings.warn("Could not import matlab.engine. " +
                  "Matlab features will be disabled.")
    matlab_installed = False

    
# Create config file if one does not exist
usr_config_file = os.path.expanduser(os.path.join('~', '.cis_interface.cfg'))
def_config_file = os.path.join(os.path.dirname(__file__),
                               'cis_interface', 'defaults.cfg')
if not os.path.isfile(usr_config_file):
    shutil.copy(def_config_file, usr_config_file)

# Import config parser
cov_installed = False
try:
    from ConfigParser import RawConfigParser as HandyConfigParser
    cov_installed = True
except ImportError:
    try:
        from configparser import RawConfigParser as HandyConfigParser
        cov_installed = True
    except ImportError:
        pass

# Set paths in config file
if cov_installed and IS_WINDOWS:
    import subprocess
    # Function to fine paths
    def locate(fname, brute_force=False):
        try:
            if brute_force:
                if os.environ.get('APPVEYOR_BUILD_FOLDER', False):
                    warnings.warn("Brute force search disabled on appveyor.")
                    return False
                warnings.warn("Running brute force search for %s" % fname)
                out = subprocess.check_output(["dir", fname, "/s/b"], shell=True,
                                              cwd=os.path.abspath(os.sep))
            else:
                out = subprocess.check_output(["where", fname])
        except subprocess.CalledProcessError:
            if not brute_force:
                return locate(fname, brute_force=True)
            return False
        if out.isspace():
            return False
        matches = out.splitlines()
        first = matches[0].decode('utf-8')
        if len(matches) > 1:
            pprint.pprint(matches)
            warnings.warn("More than one (%d) match to %s. Using first match (%s)" % (
                len(matches), fname, first))
        return first
    # Open config file
    cp = HandyConfigParser("")
    cp.read(usr_config_file)
    if not cp.has_section('windows'):
        cp.add_section('windows')
    # Find paths
    clibs = {'libzmq_include': 'zmq.h', 
             'libzmq_static': 'zmq.lib',
             'czmq_include': 'czmq.h',
             'czmq_static': 'czmq.lib'}  # ,
    for opt, fname in clibs.items():
        if not cp.has_option('windows', opt):
            fpath = locate(fname)
            if fpath:
                print('located %s: %s' % (fname, fpath))
                cp.set('windows', opt, fpath)
            else:
                warnings.warn("Could not locate %s. Please set %s option in %s to correct path."
                              % (fname, opt, usr_config_file))
    with open(usr_config_file, 'w') as fd:
        cp.write(fd)


# Set coverage options in .coveragerc
if cov_installed:
    # Read options
    covrc = '.coveragerc'
    cp = HandyConfigParser("")
    cp.read(covrc)
    # Exclude rules for all files
    if not cp.has_section('report'):
        cp.add_section('report')
    if cp.has_option('report', 'exclude_lines'):
        excl_str = cp.get('report', 'exclude_lines')
        excl_list = excl_str.strip().split('\n')
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
    # Platform
    if IS_WINDOWS:
        excl_list = rm_excl_rule(excl_list, 'pragma: windows')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: windows')
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
    # LPy
    if lpy_installed:
        excl_list = add_excl_rule(excl_list, 'pragma: no lpy')
        excl_list = rm_excl_rule(excl_list, 'pragma: lpy')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: lpy')
        excl_list = rm_excl_rule(excl_list, 'pragma: no lpy')
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

# Create requirements list based on platform
requirements = ["numpy", "scipy", "pyyaml", "pystache", "nose", "zmq", "psutil",
                "matplotlib", "cerberus",
                'pandas; python_version >= "3.5"',
                'pandas; python_version == "2.7"',
                'pandas<0.21; python_version == "3.4"',
                "pint"]  # "unyt"]
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
                  "'%s' to your PATH.")
    
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
    install_requires=requirements,
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
        'console_scripts': ['cisrun=cis_interface.command_line:cisrun',
                            'ciscc=cis_interface.command_line:ciscc',
                            'cisccflags=cis_interface.command_line:cc_flags',
                            'cisldflags=cis_interface.command_line:ld_flags',
                            'cisschema=cis_interface.command_line:regen_schema'],
    },
    license="BSD",
)
