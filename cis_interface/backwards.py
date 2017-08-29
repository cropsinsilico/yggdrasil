r"""This module allows for backward compatibility."""
import sys
PY2 = (sys.version_info[0] == 2)
if PY2:  # pragma: Python 2
    import cPickle as pickle
    import ConfigParser as configparser
    import StringIO as sio
else:  # pragma: Python 3
    import pickle
    import configparser
    import sio
    
