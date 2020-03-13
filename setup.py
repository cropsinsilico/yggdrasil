import os
import sys
import logging
import warnings
from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib
import versioneer
import create_coveragerc
ygg_ver = versioneer.get_version()
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
LANG_PATH = os.path.join(ROOT_PATH, 'yggdrasil', 'languages')


# Import script from inside package
sys.path.insert(0, LANG_PATH)
try:
    import install_languages
finally:
    sys.path.pop(0)


print("In setup.py", sys.argv)
logging.critical("In setup.py: %s" % sys.argv)
        

# Don't do coverage or installation of packages for use with other languages
# when building a source distribution
if 'sdist' not in sys.argv:
    # Attempt to install languages
    installed_languages = install_languages.install_all_languages(from_setup=True)
    # Set coverage options in .coveragerc
    create_coveragerc.create_coveragerc(installed_languages)


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
    
    
setup(
    name="yggdrasil-framework",
    packages=find_packages(),
    include_package_data=True,
    version=ygg_ver,
    cmdclass=versioneer.get_cmdclass(),
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
        "Programming Language :: C",
        "Programming Language :: C++",
        "Programming Language :: ML",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "Development Status :: 5 - Production/Stable",
    ],
    entry_points={
        'console_scripts': ['ygginfo=yggdrasil.command_line:ygginfo',
                            'yggrun=yggdrasil.command_line:yggrun',
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
                            'yggvalidate=yggdrasil.command_line:validate_yaml',
                            'ygginstall=yggdrasil.command_line:ygginstall',
                            'yggclean=yggdrasil.command_line:yggclean',
                            'yggmodelform=yggdrasil.command_line:yggmodelform'],
    },
    license="BSD",
    python_requires='>=3.5',
)
