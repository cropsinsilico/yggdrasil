from yggdrasil import tools
from yggdrasil.components import import_component
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver


class DSLModelDriver(InterpretedModelDriver):  # pragma: no cover
    r"""Class for running domain specific lanugage models."""

    is_dsl = True
    base_languages = ['python']  # Defaults to Python but can be modified
    executable_type = 'dsl'
    function_param = None

    @classmethod
    def is_language_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        # Dependent only on base languages
        return True

    @classmethod
    def is_library_installed(cls, lib, **kwargs):
        r"""Determine if a dependency is installed.

        Args:
            lib (str): Name of the library that should be checked.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        drv = import_component('model', cls.base_languages[0])
        return drv.is_library_installed(lib, **kwargs)
    
    @classmethod
    def model_wrapper(cls, *args, **kwargs):  # pragma: no cover
        r"""Model wrapper."""
        raise NotImplementedError

    @property
    def model_wrapper_args(self):  # pragma: no cover
        r"""tuple: Positional arguments for the model wrapper."""
        return ()

    @property
    def model_wrapper_kwargs(self):
        r"""dict: Keyword arguments for the model wrapper."""
        return {'env': self.set_env()}

    def queue_recv(self):
        r"""Receive a message from the model process."""
        while not (self.model_process.pipe[0].poll()
                   or self.model_process.pipe[0].closed
                   or self.model_process.pipe[1].closed
                   or (not self.model_process.is_alive())
                   or self.queue_thread.was_break):
            self.sleep()
        if not self.model_process.pipe[0].poll():
            raise RuntimeError("No more messages from model process.")
        out = self.model_process.pipe[0].recv()
        if isinstance(out, str):
            out = out.encode('utf-8')
        return out
        
    def queue_close(self):
        r"""Close the queue for messages from the model process."""
        self.model_process.pipe[0].close()
        self.model_process.pipe[1].close()
        
    def run_model(self, return_process=True, **kwargs):
        r"""Run the model. Unless overridden, the model will be run using
        run_executable.

        Args:
            return_process (bool, optional): If True, the process running
                the model is returned. If False, the process will block until
                the model finishes running. Defaults to True.
            **kwargs: Keyword arguments are passed to run_executable.

        """
        args = self.model_wrapper_args
        kwargs = self.model_wrapper_kwargs
        self.debug('Working directory: %s', self.working_dir)
        self.debug('Model file: %s', self.model_file)
        self.debug('Environment Variables:\n%s',
                   self.pprint(kwargs['env'], block_indent=1))
        p = tools.YggProcess(target=self.model_wrapper,
                             args=args, kwargs=kwargs)
        p.start()
        if return_process:
            return p
        p.join()
        if p.returncode != 0:
            raise RuntimeError("Model failed.")
        return ''
