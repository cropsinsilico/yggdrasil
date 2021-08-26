import shutil
from yggdrasil.components import import_component
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.multitasking import MPI, MPIRequestWrapper


class MPIPartnerModel(ModelDriver):
    r"""Class for shadowing a model run on another MPI process."""

    _schema_subtype_description = ('Model is being run on another MPI '
                                   'process and this driver is used as '
                                   'as stand-in to monitor it on the root '
                                   'process.')
    executable_type = 'other'
    language = 'mpi'
    full_language = False
    base_languages = []
    language_ext = []
    comms_implicit = True

    def __init__(self, *args, **kwargs):
        kwargs.pop('function', None)
        super(MPIPartnerModel, self).__init__(*args, **kwargs)
        self.partner_driver = import_component('model',
                                               self.yml['partner_driver'],
                                               without_schema=True)
        self.partner_driver.mpi_partner_init(self)

    def cleanup(self, *args, **kwargs):
        r"""Remove compile executable."""
        self.partner_driver.mpi_partner_cleanup(self)
        super(MPIPartnerModel, self).cleanup(*args, **kwargs)

    @classmethod
    def is_language_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        return (MPI is not None)

    @classmethod
    def is_configured(cls):
        r"""Determine if the appropriate configuration has been performed (e.g.
        installation of supporting libraries etc.)

        Returns:
            bool: True if the language has been configured.

        """
        return True

    @classmethod
    def is_comm_installed(cls, **kwargs):
        r"""Determine if a comm is installed for the associated programming
        language.

        Args:
            **kwargs: Keyword arguments are ignored.

        Returns:
            bool: True if a comm is installed for this language.

        """
        return True
    
    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        import mpi4py
        return 'mpi4py %s' % mpi4py.__version__
    
    @classmethod
    def language_executable(cls, **kwargs):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        return shutil.which('mpiexec')
        
    def run_model(self, **kwargs):
        r"""Dummy stand-in for ModelDriver run_model method."""
        return None
        
    def before_start(self, **kwargs):
        r"""Actions to perform before the run starts."""
        kwargs['no_queue_thread'] = True
        super(MPIPartnerModel, self).before_start(**kwargs)

    # def init_mpi_env(self):
    #     r"""Send env information to the partner model."""
    #     env = copy.deepcopy(self.env)
    #     env.update(self.get_io_env())
    #     self.send_mpi(env, tag=self._mpi_tags['ENV'])
        
    def init_mpi(self):
        r"""Initialize MPI communicator."""
        self.send_mpi('START', tag=self._mpi_tags['START'])
        self._mpi_requests['stopped'] = MPIRequestWrapper(
            self.recv_mpi(tag=self._mpi_tags['STOP_RANK0'], dont_block=True))

    def stop_mpi_partner(self, **kwargs):
        r"""Send a message to stop the MPI partner model on the main process."""
        kwargs.update(dest=self._mpi_partner_rank,
                      tag=self._mpi_tags['STOP_RANKX'],
                      msg=self.n_sent_messages)
        super(MPIPartnerModel, self).stop_mpi_partner(**kwargs)

    def run_loop(self):
        r"""Loop to check if model is still running."""
        if self.check_mpi_request('stopped'):
            self.set_break_flag()
        else:
            self.sleep()

    def graceful_stop(self):
        r"""Gracefully stop the driver."""
        if self.has_sent_messages:
            self.wait_on_mpi_request('stopped', timeout=10)
        self.set_break_flag()
        super(MPIPartnerModel, self).graceful_stop()
        
    def kill_process(self):
        r"""Kill the process running the model, checking return code."""
        self.set_break_flag()
        if not self.model_process_complete:  # pragma: debug
            self._mpi_requests['stopped'].completed = True
        super(MPIPartnerModel, self).kill_process()
        
    @property
    def model_process_complete(self):
        r"""bool: Has the process finished or not. Returns True if the process
        has not started."""
        return self.check_mpi_request('stopped')
