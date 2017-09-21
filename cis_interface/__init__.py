r"""This package provides a framework for integrating models across languages
such that they can be run simultaneously, passing input back and forth."""
import os
from cis_interface import backwards
from cis_interface import config
from cis_interface import tools
from cis_interface import interface
from cis_interface import drivers
from cis_interface import dataio
from cis_interface import tests
from cis_interface import examples


# Set paths so that c headers are located
# TODO: Only the CIS_INCLUDE environment variable should be used
cis_base = os.path.dirname(__file__)
cis_include = os.path.join(cis_base, 'interface')
os.environ['CIS_BASE'] = cis_base
os.environ['CIS_INCLUDE'] = cis_include
# path = os.environ.get('PATH', cis_include)
# cpath = os.environ.get('CPATH', cis_include)
# if cis_include not in path:
#     os.environ['PATH'] = cis_include + ':' + path
# if cis_include not in cpath:
#     os.environ['CPATH'] = cis_include + ':' + cpath


__all__ = ['backwards', 'config', 'tools',
           'interface', 'drivers', 'dataio',
           'tests', 'examples']
