#
# This should not be used directly by modelers
#
import time
import importlib
from logging import *
import subprocess
from datetime import datetime
import os
import sys
import matlab.engine
from ModelDriver import ModelDriver, preexec
from cis_interface.backwards import sio


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


def start_matlab():
    r"""Start a Matlab shared engine session inside a detached screen 
    session.

    Returns:
        str: Name of the screen session running matlab.

    """
    screen_session = 'matlab' + datetime.today().strftime("%Y%j%H%M%S")
    os.system(('screen ' +
               '-dmS %s ' % screen_session +
               '-c %s ' % os.path.join(os.path.dirname(__file__), 'matlab_screenrc')+
               'matlab -nodisplay -nosplash -nodesktop -nojvm ' +
               '-r "matlab.engine.shareEngine"'))
               # 'matlab -r "matlab.engine.shareEngine"'))
    while len(matlab.engine.find_matlab()) == 0:
        debug('Waiting for matlab engine to start')
        time.sleep(1) # Usually 3 seconds
    return screen_session


def stop_matlab(screen_session):
    r"""Stop a Matlab shared engine session running inside a detached screen
    session.

    Args:
        screen_session (str): Name of the screen session.

    """
    n0 = len(matlab.engine.find_matlab())
    os.system(('screen -X -S %s quit') % screen_session)
    while len(matlab.engine.find_matlab()) == n0:
        debug("Waiting for matlab engine to exit")
        time.sleep(1)


class MatlabModelDriver(ModelDriver):
    r"""Base class for running Matlab models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model in matlab.
            Generally, this should be the full path to a Matlab script.
        \*\*kwargs: Additional keyword arguments are passed to parent class's 
            __init__ method. 

    Attributes (in additon to parent class's):
        started_matlab (bool): True if the driver had to start a new matlab
            engine. False otherwise.
        mlengine (object): Matlab engine used to run script.

    """

    def __init__(self, name, args, **kwargs):
        super(MatlabModelDriver, self).__init__(name, args, **kwargs)

        # Connect to matlab, start if not running
        self.screen_session = None
        self.started_matlab = False
        self.mlengine = None
        if len(matlab.engine.find_matlab()) == 0:
            self.debug(": starting a matlab shared engine")
            self.screen_session = start_matlab()
            self.started_matlab = True
        try:
            self.mlengine = matlab.engine.connect_matlab(matlab.engine.find_matlab()[0])
        except matlab.engine.EngineError:
            self.exception("could not connect to matlab engine")
            return

        # Add things to Matlab environment
        fdir = os.path.dirname(os.path.abspath(self.args[0]))
        self.mlengine.addpath(_top_dir, nargout=0)
        self.mlengine.addpath(_incl_interface, nargout=0)
        self.mlengine.addpath(fdir, nargout=0)
        self.debug(": connected to matlab")

    def __del__(self):
        self.terminate()

    def terminate(self):
        r"""Terminate the driver, including the matlab engine."""
        if self.started_matlab:
            eng = self.mlengine
            self.mlengine = None
            try:
                if eng is not None:
                    eng.quit()
            except SystemError:
                self.error('.terminate failed to quit matlab engine')
            if self.screen_session is not None:
                stop_matlab(self.screen_session)
            self.screen_session = None
            self.started_matlab = False
        super(MatlabModelDriver, self).terminate()

    def run(self):
        r"""Run the matlab script in the matlab engine."""
        self.debug('.run %s from %s', self.args[0], os.getcwd())
        
        out = sio.StringIO()
        # err = sio.StringIO()

        # Add environment variables
        for k, v in self.env.items():
            if self.mlengine is None:
                return
            self.mlengine.setenv(k, v, nargout=0)
            
        # Construct command
        # Strip the .m off - silly matlab
        name = os.path.splitext(os.path.basename(self.args[0]))[0]
        command = 'self.mlengine.' + name + '('
        if len(self.args) > 1:
            command = command + ', '.join(self.args[1:]) +', '
        command += 'stdout=out, '
        # command += 'stderr=err, '
        command += 'nargout=0)'
        self.debug(": command: %s", command)
        
        # Run
        if self.mlengine is None:
            return
        eval(command)

        # Get otuput
        line = out.getvalue()
        sys.stdout.write(line)
        sys.stdout.flush()

        self.debug(".done")

