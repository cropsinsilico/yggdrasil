import os
import sys
import logging
import warnings
import json
from setuptools import setup, find_namespace_packages, Extension
from distutils.sysconfig import get_python_lib
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
PYRJ_PATH = os.path.join(ROOT_PATH, '_vendor', 'python_rapidjson')
sys.path.insert(0, ROOT_PATH)
import versioneer  # noqa: E402
ygg_ver = versioneer.get_version()
kwargs = {'cmdclass': versioneer.get_cmdclass()}


# Clean up version
if '--force-clean-version' in sys.argv:
    sys.argv.remove('--force-clean-version')
    if '+' in ygg_ver:
        ygg_ver = ygg_ver.split('+')[0]
    kwargs.pop('cmdclass')


print(f"In setup.py: ver={ygg_ver}, sys.argv={sys.argv}, PYRJ_PATH={PYRJ_PATH}")
logging.critical(
    f"In setup.py: ver={ygg_ver}, sys.argv={sys.argv}, PYRJ_PATH={PYRJ_PATH}")


# Get extension options for the vendored python-rapidjson
sys.path.insert(0, PYRJ_PATH)
if not any(x.startswith("--rj-include-dir") for x in sys.argv):
    rj_include_dir = os.path.join('yggdrasil', 'rapidjson', 'include')
    sys.argv.append(f"--rj-include-dir={rj_include_dir}")
pwd = os.getcwd()
os.chdir(PYRJ_PATH)
try:
    import pyrj_setup
    pyrj_ext = pyrj_setup.extension_options
    pyrj_ext.update(
        sources=[os.path.join('yggdrasil', 'rapidjson.cpp')])
finally:
    sys.path.pop(0)
    os.chdir(pwd)
print(f"pyrj_ext = {pyrj_ext}")
logging.critical(f"pyrj_ext = {pyrj_ext}")


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
req_dir = os.path.join("utils", "requirements")
with open("requirements.txt", 'r') as fd:
    requirements = fd.read().splitlines()
with open(os.path.join(req_dir, "requirements_testing.txt"), 'r') as fd:
    test_requirements = fd.read().splitlines()
extras_requirements = json.load(
    open(os.path.join(req_dir, "requirements_extras.json"), 'r'))
with open("console_scripts.txt", 'r') as fd:
    console_scripts = fd.read().splitlines()


# Warn that local install may not have entry points on path
if '--user' in sys.argv:
    script_dir = os.path.realpath(os.path.join(get_python_lib(),
                                               '../../../bin/'))
    warnings.warn("When installing locally, you may need to add the script "
                  + "directory to your path manually in order to have access "
                  + "to the command line entry points (e.g. yggrun). "
                  + "If 'yggrun' is not a recognized command, try adding "
                  + "'%s' to your PATH." % script_dir)
    
    
setup(
    name="yggdrasil-framework",
    packages=find_namespace_packages(
        exclude=["_vendor", "_vendor.*"]),
    include_package_data=True,
    version=ygg_ver,
    description=("A framework for combining interdependent models from "
                 "multiple languages."),
    long_description=long_description,
    author="Meagan Lang",
    author_email="langmm.astro@gmail.com",
    url="https://github.com/cropsinsilico/yggdrasil",
    download_url=(
        "https://github.com/cropsinsilico/yggdrasil/archive/%s.tar.gz" % ygg_ver),
    keywords=["plants", "simulation", "models", "framework"],
    ext_modules=[Extension('yggdrasil.rapidjson', **pyrj_ext)],
    setup_requires=['numpy'],
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require=extras_requirements,
    classifiers=[
        "Programming Language :: C",
        "Programming Language :: C++",
        "Programming Language :: ML",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "Development Status :: 5 - Production/Stable",
    ],
    entry_points={
        'console_scripts': console_scripts,
    },
    license="BSD",
    python_requires='>=3.6',
    **kwargs
)
