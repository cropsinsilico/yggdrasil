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
from ModelDriver import ModelDriver
from cis_interface.backwards import sio
import weakref


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


def start_matlab():
    r"""Start a Matlab shared engine session inside a detached screen 
    session.

    Returns:
        str: Name of the screen session running matlab.

    """
    old_matlab = set(matlab.engine.find_matlab())
    screen_session = str('matlab' + datetime.today().strftime("%Y%j%H%M%S") +
                         '_%d' % len(old_matlab))
    os.system(('screen ' +
               '-dmS %s ' % screen_session +
               '-c %s ' % os.path.join(os.path.dirname(__file__),
                                       'matlab_screenrc') +
               'matlab -nodisplay -nosplash -nodesktop -nojvm ' +
               '-r "matlab.engine.shareEngine"'))
    while len(set(matlab.engine.find_matlab()) - old_matlab) == 0:
        debug('Waiting for matlab engine to start')
        time.sleep(1)  # Usually 3 seconds
    new_matlab = list(set(matlab.engine.find_matlab()) - old_matlab)[0]
    return screen_session, new_matlab


def stop_matlab(screen_session, matlab_engine, matlab_session):
    r"""Stop a Matlab shared engine session running inside a detached screen
    session.

    Args:
        screen_session (str): Name of the screen session that the shared
            Matlab session was started in.
        matlab_engine (MatlabEngine): Matlab engine that should be stopped.
        matlab_session (str): Name of Matlab session that the Matlab engine is
            connected to.

    """
    # Remove weakrefs to engine to prevent stopping engine more than once
    if matlab_engine is not None:
        # Remove weak references so engine not deleted on exit
        eng_ref = weakref.getweakrefs(matlab_engine)
        for x in eng_ref:
            if x in matlab.engine._engines:
                matlab.engine._engines.remove(x)
        # Either exit the engine or remove its reference
        if matlab_session in matlab.engine.find_matlab():
            matlab_engine.exit()
        else:  # pragma: no cover
            matlab_engine.__dict__.pop('_matlab')
    # Stop the screen session containing the Matlab shared session
    if screen_session is not None:
        if matlab_session in matlab.engine.find_matlab():
            os.system(('screen -X -S %s quit') % screen_session)
        while matlab_session in matlab.engine.find_matlab():
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
        self.mlsession = None
        if len(matlab.engine.find_matlab()) == 0:
            self.debug(": starting a matlab shared engine")
            self.screen_session, self.mlsession = start_matlab()
            self.started_matlab = True
        else:
            self.mlsession = matlab.engine.find_matlab()[0]
        try:
            self.mlengine = matlab.engine.connect_matlab(self.mlsession)
        except matlab.engine.EngineError:
            self.debug(": starting a matlab shared engine")
            self.screen_session, self.mlsession = start_matlab()
            self.started_matlab = True
            try:
                self.mlengine = matlab.engine.connect_matlab(self.mlsession)
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

    def cleanup(self):
        r"""Close the Matlab session and engine."""
        try:
            stop_matlab(self.screen_session, self.mlengine,
                        self.mlsession)
        except SystemError:  # pragma: debug
            self.error('.terminate failed to exit matlab engine')
            raise
        self.screen_session = None
        self.mlsession = None
        self.started_matlab = False
        self.mlengine = None

    def on_exit(self):
        r"""Cleanup Matlab session and engine on exit."""
        self.cleanup()
        super(MatlabModelDriver, self).on_exit()

    def terminate(self):
        r"""Terminate the driver, including the matlab engine."""
        with self.lock:
            self.cleanup()
        super(MatlabModelDriver, self).terminate()

    def run(self):
        r"""Run the matlab script in the matlab engine."""
        self.debug('.run %s from %s', self.args[0], os.getcwd())
        
        out = sio.StringIO()
        # err = sio.StringIO()

        # Add environment variables
        for k, v in self.env.items():
            with self.lock:
                if self.mlengine is None:
                    return
                self.mlengine.setenv(k, v, nargout=0)
            
        # Construct command
        # Strip the .m off - silly matlab
        name = os.path.splitext(os.path.basename(self.args[0]))[0]
        command = "self.mlengine." + name + "("
        if len(self.args) > 1:
            for a in self.args[1:]:
                if isinstance(a, str):
                    command += "'%s', " % a
                else:
                    command += "%s, " % str(a)
            # command = command + ", ".join(self.args[1:]) +", "
        command += "stdout=out, "
        # command += "stderr=err, "
        command += "nargout=0)"
        self.debug(": command: %s", command)
        
        # Run
        with self.lock:
            if self.mlengine is None:  # pragma: debug
                return
            eval(command)

        # Get otuput
        line = out.getvalue()
        sys.stdout.write(line)
        sys.stdout.flush()

        self.debug(".done")

