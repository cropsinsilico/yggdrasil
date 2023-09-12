# flake8: noqa
# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Packaging
# :Author:    Ken Robbins <ken@kenrobbins.com>
# :License:   MIT License
# :Copyright: © 2015 Ken Robbins
# :Copyright: © 2016, 2017, 2018, 2019, 2020, 2021, 2022 Lele Gaifax
#

import os.path
import sys

try:
    from setuptools import setup, Extension
    try:
        # This is needed for some old versions of setuptools
        import packaging.specifiers
    except ImportError:
        pass
    other_setup_options = {'python_requires': '>=3.6'}
except ImportError:
    from distutils.core import setup, Extension
    other_setup_options = {}

from distutils import sysconfig


if sys.version_info < (3, 6):
    raise NotImplementedError("Only Python 3.6+ is supported.")

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))

rj_include_dir = './rapidjson/include'
with_asan = False

for idx, arg in enumerate(sys.argv[:]):
    if arg.startswith('--rj-include-dir='):
        sys.argv.pop(idx)
        rj_include_dir = arg.split('=', 1)[1]
        break
else:
    if not os.path.isdir(os.path.join(ROOT_PATH, 'rapidjson', 'include')):
        raise RuntimeError("RapidJSON sources not found: if you cloned the"
                           " git repository, you should initialize the"
                           " rapidjson submodule as explained in the"
                           " README.rst; in all other cases you may"
                           " want to report the issue.")
for idx, arg in enumerate(sys.argv[:]):
    if arg == '--with-asan':
        sys.argv.pop(idx)
        with_asan = True
        break

with open('version.txt', encoding='utf-8') as f:
    VERSION = f.read()

with open('README.rst', encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

with open('CHANGES.rst', encoding='utf-8') as f:
    CHANGES = f.read()


class get_numpy_include(object):

    def __str__(self):
        import numpy
        return numpy.get_include()


extension_options = {
    'sources': ['./rapidjson.cpp'],
    'include_dirs': [rj_include_dir, get_numpy_include()],
    'define_macros': [('PYTHON_RAPIDJSON_VERSION', VERSION)],
    'depends': ['./rapidjson_exact_version.txt'],
}

if os.path.exists('rapidjson_exact_version.txt'):
    with open('rapidjson_exact_version.txt', encoding='utf-8') as f:
        extension_options['define_macros'].append(
            ('RAPIDJSON_EXACT_VERSION', f.read().strip()))


cxx = sysconfig.get_config_var('CXX')
print(f"SETUP.PY CXX = {cxx}")
if cxx and 'g++' in cxx:
    # Avoid warning about invalid flag for C++
    for varname in ('CFLAGS', 'OPT'):
        value = sysconfig.get_config_var(varname)
        if value and '-Wstrict-prototypes' in value:
            value = value.replace('-Wstrict-prototypes', '')
            sysconfig.get_config_vars()[varname] = value

    # Add -pedantic, so we get a warning when using non-standard features, and
    # -Wno-long-long to pacify old gcc (or Apple's hybrids) that treat
    # "long long" as an error under C++ (see issue #69). C++11 is required
    # since commit
    # https://github.com/Tencent/rapidjson/commit/9965ab37f6cfae3d58a0a6e34c76112866ace0b1
    extension_options['extra_compile_args'] = [
        '-pedantic', '-Wno-long-long', '-std=c++11']

    # Up to Python 3.7, some structures use "char*" instead of "const char*",
    # and ISO C++ forbids assigning string literal constants
    if sys.version_info < (3, 7):
        extension_options['extra_compile_args'].append('-Wno-write-strings')

# Ensure rapidjson is compiled with yggdrasil
extension_options.setdefault('extra_compile_args', [])
extension_options['extra_compile_args'] += ['-DRAPIDJSON_YGGDRASIL',
                                            '-DRAPIDJSON_YGGDRASIL_PYTHON']

if with_asan:
    extension_options.setdefault('extra_link_args', [])
    extension_options['extra_compile_args'] += [
        '-fsanitize=address', '-g', '-O0', '-fsanitize=undefined',
        '-fno-omit-frame-pointer']
    extension_options['extra_link_args'] += [
        '-fsanitize=address', '-fsanitize=undefined',
        '-fno-omit-frame-pointer']
    extension_options['extra_link_args'].append('-shared-libasan')
