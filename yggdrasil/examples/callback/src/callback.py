import os
from yggdrasil import units, constants
fname = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     'outputCallback.txt')
if os.path.isfile(fname):
    os.remove(fname)


def callback_function(msg):
    with open(fname, 'ab') as fd:
        fd.write((str(units.get_data(msg.args))
                  + constants.DEFAULT_NEWLINE_STR).encode("utf-8"))
