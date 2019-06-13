import os
import sys
import logging
import warnings
from setuptools import setup, find_packages
# from setuptools.command.install import install
# from setuptools.command.develop import develop
from distutils.sysconfig import get_python_lib
import versioneer
import install_matlab_engine
import install_R_interface
import create_coveragerc
ygg_ver = versioneer.get_version()
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


print("In setup.py", sys.argv)
logging.critical("In setup.py: %s" % sys.argv)


# Don't do coverage or installation of packages for use with other languages
# when building a source distribution
if 'sdist' not in sys.argv:
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
                      "Matlab support will be disabled.")
        matlab_installed = False


    # Install R interface
    with_sudo = (('sudo' in sys.argv) or ('--sudoR' in sys.argv)
                 or (os.environ.get('YGG_USE_SUDO_FOR_R', '0') == '1'))
    if install_R_interface.install_R_interface(with_sudo=with_sudo):
        R_installed = True
    else:
        warnings.warn("Could not install R interface. " +
                      "R support will be disabled.")
        R_installed = False


    # Determine if rapidjson installed and parse user defined location
    rj_include_dir0 = os.path.join(ROOT_PATH, 'yggdrasil', 'rapidjson', 'include')
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
        def_config_file = os.path.join(ROOT_PATH, 'yggdrasil', 'defaults.cfg')
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
                                        lpy_installed=lpy_installed,
                                        R_installed=R_installed)


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
with open("requirements.txt", 'r') as fd:
    requirements = fd.read().splitlines()
with open("requirements_testing.txt", 'r') as fd:
    test_requirements = fd.read().splitlines()
# with open("requirements_optional.txt", 'r') as fd:
#     optional_requirements = fd.read().splitlines()


# Warn that local install may not have entry points on path
if '--user' in sys.argv:
    script_dir = os.path.realpath(os.path.join(get_python_lib(),
                                               '../../../bin/'))
    warnings.warn("When installing locally, you may need to add the script " +
                  "directory to your path manually in order to have access " +
                  "to the command line entry points (e.g. yggrun). " +
                  "If 'yggrun' is not a recognized command, try adding " +
                  "'%s' to your PATH." % script_dir)

cmdclass = versioneer.get_cmdclass()
# install_cmdclass = cmdclass.get('install', install)
# develop_cmdclass = cmdclass.get('develop', develop)


# class CommandMixin(object):
#     user_options = [('sudoR', None, None),
#                     ('rj-include-dir=', None, None),
#                     ('rapidjson-include-dir=', None, None)]

#     def initialize_options(self):
#         super(CommandMixin, self).initialize_options()
#         self.sudoR = None

#     def finalize_options(self):
#         print("value of sudoR is", self.sudoR)
#         super(CommandMixin, self).finalize_options()

#     def run(self):
#         global sudoR
#         sudoR = self.sudoR # will be 1 or None
#         super(CommandMixin, self).run()
        

# class InstallCommand(CommandMixin, install_cmdclass):
#     user_options = getattr(install_cmdclass,
#                            'user_options', []) + CommandMixin.user_options
    
    
# class DevelopCommand(CommandMixin, develop_cmdclass):
#     user_options = getattr(develop_cmdclass,
#                            'user_options', []) + CommandMixin.user_options

    
# cmdclass['install'] = InstallCommand
# cmdclass['develop'] = DevelopCommand
    
    
setup(
    name="yggdrasil-framework",
    packages=find_packages(),
    include_package_data=True,
    version=ygg_ver,
    cmdclass=cmdclass,
    description=("A framework for combining interdependent models from "
                 "multiple languages."),
    long_description=long_description,
    author="Meagan Lang",
    author_email="langmm.astro@gmail.com",
    url="https://github.com/cropsinsilico/yggdrasil",
    download_url=(
        "https://github.com/cropsinsilico/yggdrasil/archive/%s.tar.gz" % ygg_ver),
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
        'console_scripts': ['yggrun=yggdrasil.command_line:yggrun',
                            'cisrun=yggdrasil.command_line:yggrun',
                            'yggcc=yggdrasil.command_line:yggcc',
                            'yggccflags=yggdrasil.command_line:cc_flags',
                            'yggldflags=yggdrasil.command_line:ld_flags',
                            'yggtest=yggdrasil:run_tsts',
                            'yggmetaschema=yggdrasil.command_line:regen_metaschema',
                            'yggschema=yggdrasil.command_line:regen_schema',
                            'yggbuildapi_c=yggdrasil.command_line:rebuild_c_api',
                            'yggconfig=yggdrasil.command_line:update_config',
                            'yggtime_comm=yggdrasil.command_line:yggtime_comm',
                            'yggtime_lang=yggdrasil.command_line:yggtime_lang',
                            'yggtime_os=yggdrasil.command_line:yggtime_os',
                            'yggtime_py=yggdrasil.command_line:yggtime_py',
                            'yggtime_paper=yggdrasil.command_line:yggtime_paper',
                            'yggvalidate=yggdrasil.command_line:validate_yaml'],
    },
    license="BSD",
)
