#
# This should not be used directly by modelers
#
from __future__ import print_function
import time
from logging import debug, warn
from datetime import datetime
import os
import weakref
try:  # pragma: matlab
    import matlab.engine
    _matlab_installed = True
except ImportError:  # pragma: no matlab
    warn("Could not import matlab.engine. " +
         "Matlab support will be disabled.")
    _matlab_installed = False
from cis_interface.drivers.ModelDriver import ModelDriver
from cis_interface import backwards
from cis_interface.tools import TimeOut


_top_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '../'))
_incl_interface = os.path.join(_top_dir, 'interface')
_incl_io = os.path.join(_top_dir, 'io')


def start_matlab():
    r"""Start a Matlab shared engine session inside a detached screen
    session.

    Returns:
        str: Name of the screen session running matlab.

    """
    if _matlab_installed:  # pragma: matlab
        old_matlab = set(matlab.engine.find_matlab())
        screen_session = str('matlab' + datetime.today().strftime("%Y%j%H%M%S") +
                             '_%d' % len(old_matlab))
        os.system(('screen ' +
                   '-dmS %s ' % screen_session +
                   '-c %s ' % os.path.join(os.path.dirname(__file__),
                                           'matlab_screenrc') +
                   'matlab -nodisplay -nosplash -nodesktop -nojvm ' +
                   '-r "matlab.engine.shareEngine"'))
        T = TimeOut(10)
        while ((len(set(matlab.engine.find_matlab()) - old_matlab) == 0) and
               not T.is_out):
            debug('Waiting for matlab engine to start')
            time.sleep(1)  # Usually 3 seconds
        if (len(set(matlab.engine.find_matlab()) - old_matlab) == 0):
            raise Exception("start_matlab timed out at %f s" % T.elapsed)
        new_matlab = list(set(matlab.engine.find_matlab()) - old_matlab)[0]
    else:  # pragma: no matlab
        warn("Matlab not installed. Matlab could not be started.")
        screen_session, new_matlab = None, None
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
    if _matlab_installed:  # pragma: matlab
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
            T = TimeOut(5)
            while ((matlab_session in matlab.engine.find_matlab()) and
                   not T.is_out):
                debug("Waiting for matlab engine to exit")
                time.sleep(1)
            if (matlab_session in matlab.engine.find_matlab()):
                raise Exception("stp[_matlab timed out at %f s" % T.elapsed)
    # else:  # pragma: no matlab
    #     warn("Matlab not installed. Matlab could not be stopped.")


class MatlabModelDriver(ModelDriver):
    r"""Base class for running Matlab models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model in matlab.
            Generally, this should be the full path to a Matlab script.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    Attributes:
        started_matlab (bool): True if the driver had to start a new matlab
            engine. False otherwise.
        screen_session (str): Screen session that Matlab was started in.
        mlengine (object): Matlab engine used to run script.
        mlsession (str): Name of the Matlab session that was started.

    """

    def __init__(self, name, args, **kwargs):
        super(MatlabModelDriver, self).__init__(name, args, **kwargs)

        self.started_matlab = False
        self.screen_session = None
        self.mlengine = None
        self.mlsession = None
        if _matlab_installed:  # pragma: matlab
            # Connect to matlab, start if not running
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
                except matlab.engine.EngineError as e:  # pragma: debug
                    self.error("could not connect to matlab engine")
                    self.raise_error(e)
            # Add things to Matlab environment
            fdir = os.path.dirname(os.path.abspath(self.args[0]))
            self.mlengine.addpath(_top_dir, nargout=0)
            self.mlengine.addpath(_incl_interface, nargout=0)
            self.mlengine.addpath(fdir, nargout=0)
            self.debug(": connected to matlab")
        else:  # pragma: no matlab
            self.screen_session, self.mlsession = start_matlab()

    def cleanup(self):
        r"""Close the Matlab session and engine."""
        try:
            stop_matlab(self.screen_session, self.mlengine,
                        self.mlsession)
        except SystemError as e:  # pragma: debug
            self.error('.cleanup() failed to exit matlab engine')
            self.raise_error(e)
        self.screen_session = None
        self.mlsession = None
        self.started_matlab = False
        self.mlengine = None
        super(MatlabModelDriver, self).cleanup()

    def on_exit(self):
        r"""Cleanup Matlab session and engine on exit."""
        self.cleanup()
        super(MatlabModelDriver, self).on_exit()

    def terminate(self):
        r"""Terminate the driver, including the matlab engine."""
        if self._terminated:
            self.debug(':terminate() Driver already terminated.')
            return
        with self.lock:
            self.cleanup()
        super(MatlabModelDriver, self).terminate()

    def start(self):
        r"""Prevent Popen from standard model driver."""
        super(MatlabModelDriver, self).start(no_popen=True)

    def run(self):
        r"""Run the matlab script in the matlab engine."""
        if _matlab_installed:  # pragma: matlab
            self.debug('.run %s from %s', self.args[0], os.getcwd())

            # Set up IO
            out = backwards.sio.StringIO()
            # err = backwards.sio.StringIO()
            kwargs = dict(nargout=0, stdout=out)  # , stderr=err)
            name = os.path.splitext(os.path.basename(self.args[0]))[0]

            # Add environment variables
            for k, v in self.env.items():
                with self.lock:
                    if self.mlengine is None:  # pragma: debug
                        return
                    self.mlengine.setenv(k, v, nargout=0)

            # Run
            with self.lock:
                if self.mlengine is None:  # pragma: debug
                    return
                try:
                    # TODO: run in separate process to allow termination?
                    func = getattr(self.mlengine, name)
                    func(*self.args[1:], **kwargs)
                except Exception as e:
                    self.error(e)

            # Get output
            line = out.getvalue()
            print(line, end="")

            # Get errors
            # line = err.getvalue()
            # print(line, end="")

            self.debug(".done")
        else:  # pragma: no matlab
            self.error("Matlab not installed. Could not run model.")
