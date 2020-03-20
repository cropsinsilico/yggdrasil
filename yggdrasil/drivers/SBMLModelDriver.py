import os
from yggdrasil import tools
from yggdrasil.drivers.PythonModelDriver import PythonModelDriver


class SBMLModelDriver(PythonModelDriver):  # pragma: sbml
    r"""Class for running SBML models.

    Args:
        start (float, optional): Time that simulation should be started
            from. If 'reset' is True, the start time will always
            be the provided value, otherwise, the start time will
            be the end of the previous call after the first call.
            Defaults to 0.0.
        steps (int, optional): Number of steps that should be output.
            Defaults to None.
        reset (bool, optional): If True, the simulation will be reset
            to it's initial values before each call (including the
            start time). Defaults to False.
        selections (list, optional): Variables to include in the output.
            Defaults to None and the time/floating selections will be
            returned.
        integrator (str, optional): Name of integrator that should be
            used. Valid options include ['cvode', 'gillespie', 'rk4',
            'rk45']. Defaults to 'cvode'.
        variable_step (bool, optional): If True, the output steps will
            have a variable spacing. Defaults to False.
        integrator_settings (dict, optional): Settings for the
            integrator. Defaults to empty dict.

    """
    _schema_subtype_description = 'Model is an SBML model.'
    _schema_properties = {
        'start': {'type': 'number', 'default': 0.0},
        'steps': {'type': 'integer', 'default': 1},
        'reset': {'type': 'boolean', 'default': False},
        'selections': {'type': 'array', 'items': {'type': 'string'},
                       'default': []},
        'integrator': {'type': 'string', 'default': 'cvode',
                       'enum': ['cvode', 'gillespie', 'rk4', 'rk45']},
        'variable_step': {'type': 'boolean', 'default': False},
        'integrator_settings': {'type': 'object', 'default': {}}}
    language = 'sbml'
    language_ext = '.xml'
    interface_dependencies = ['roadrunner']
    function_param = None

    def __init__(self, *args, **kwargs):
        self.curr_time = None
        self.model = None
        self.input_map = {}
        self.output_map = {}
        super(SBMLModelDriver, self).__init__(*args, **kwargs)
        self.setup_model()

    def setup_model(self):
        r"""Set up model class instance."""
        import roadrunner
        assert(self.model is None)
        self.model = roadrunner.RoadRunner(self.model_file)
        self.model.setIntegrator(self.integrator)
        for k, v in self.integrator_settings.items():
            self.model.getIntegrator().setValue(k, v)
        self.curr_time = self.start
        for x in self.inputs:
            self.input_map[x['name']] = {'vars': x.get('vars', [])}
        for x in self.outputs:
            self.output_map[x['name']] = {'vars': x.get('vars', [])}

    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        try:
            import roadrunner
            return roadrunner.__version__
        except ImportError:  # pragma: debug
            raise RuntimeError("roadrunner not installed.")

    def setup_comms(self):
        r"""Set up model comms."""
        from yggdrasil.languages.Python.YggInterface import (
            YggInput, YggOutput)
        for k, v in self.input_map.items():
            v['comm'] = YggInput(k)
        for k, v in self.output_map.items():
            v['comm'] = YggOutput(k)

    def call_model(self, time):
        r"""Call the model."""
        if self.reset:
            self.model.reset()
            self.curr_time = self.start
        out = self.model.simulate(self.curr_time, time,
                                  selections=self.selections,
                                  steps=self.steps)
        self.curr_time = time
        return out

    def model_wrapper(self, env, working_dir):
        r"""Model wrapper."""
        os.environ.update(env)
        os.chdir(working_dir)
        self.setup_comms()
        while True:
            time = None
            for k, v in self.input_map.items():
                flag, value = v['comm'].recv_dict(key_order=v['vars'])
                if not flag:
                    print("No more input from %s" % k)
                    break
                # TODO: assign things
                time = value['time']
                for iv in v['vars']:
                    if iv == 'time':
                        continue
                    self.model.setValue(iv, value[iv])
            if time is None:
                raise RuntimeError("No time variable recovered.")
            out_value = self.call_model(time)
            for k, v in self.output_map.items():
                flag = v['comm'].send_dict({iv: out_value[iv]
                                            for iv in v['vars']},
                                           key_order=v['vars'])
                if not flag:
                    raise RuntimeError("Error sending to %s" % k)

    def run_model(self, return_process=True, **kwargs):
        r"""Run the model. Unless overridden, the model will be run using
        run_executable.

        Args:
            return_process (bool, optional): If True, the process running
                the model is returned. If False, the process will block until
                the model finishes running. Defaults to True.
            **kwargs: Keyword arguments are passed to run_executable.

        """
        env = self.set_env()
        self.debug('Working directory: %s', self.working_dir)
        self.debug('Model file: %s', self.model_file)
        self.debug('Environment Variables:\n%s', self.pprint(env, block_indent=1))
        p = tools.YggProcess(target=self.model_wrapper,
                             args=(env, self.working_dir))
        p.start()
        if return_process:
            return p
        p.join()
        if p.returncode != 0:
            raise RuntimeError("Model failed.")
        return ''
