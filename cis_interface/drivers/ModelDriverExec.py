#
# This should not be used directly by modelers
#

from Driver import Driver
import importlib
from logging import *
import subprocess
import os

class ModelDriver(Driver):

    def __init__(self, name, args):
        Driver.__init__(self, name)
        debug(args)
        self.args = args
        self.name = name

    def __del(self, name, args):
        Driver.__del__(self)


    def run(self):
        debug('ModelDriver.run  %s from %s', self.args, os.getcwd())
        subprocess.call(self.args)
        debug('ModelDriver.done' )
        return
    
