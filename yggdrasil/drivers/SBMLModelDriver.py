import os
from yggdrasil.drivers.DSLModelDriver import DSLModelDriver


class SBMLModelDriver(DSLModelDriver):  # pragma: sbml
    r"""Class for running SBML models.

    Args:
        start_time (float, optional): Time that simulation should be
            started from. If 'reset' is True, the start time will
            always be the provided value, otherwise, the start time
            will be the end of the previous call after the first call.
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
        integrator_settings (dict, optional): Settings for the
            integrator. Defaults to empty dict.
        variable_step (bool, optional): If True, the output steps will
            have a variable spacing. Defaults to False.
        only_output_final_step (bool, optional): If True, only the
            final timestep is output. Defaults to False.
        skip_start_time (bool, optional): If True, the results for the
            initial time step will not be output. Defaults to False.
            This option is ignored if only_output_final_step is True.

    """
    _schema_subtype_description = 'Model is an SBML model.'
    _schema_properties = {
        'start_time': {'type': 'number', 'default': 0.0},
        'steps': {'type': 'integer', 'default': 1},
        'reset': {'type': 'boolean', 'default': False},
        'selections': {'type': 'array', 'items': {'type': 'string'},
                       'default': []},
        'integrator': {'type': 'string', 'default': 'cvode',
                       'enum': ['cvode', 'gillespie', 'rk4', 'rk45']},
        'integrator_settings': {'type': 'object', 'default': {}},
        # 'variable_step': {'type': 'boolean', 'default': False},
        'skip_start_time': {'type': 'boolean', 'default': False},
        'only_output_final_step': {'type': 'boolean', 'default': False}}
    language = 'sbml'
    language_ext = '.xml'
    interface_dependencies = ['roadrunner']

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

    @property
    def model_wrapper_args(self):
        r"""tuple: Positional arguments for the model wrapper."""
        return (self.model_file, self.start_time, self.steps)

    @property
    def model_wrapper_kwargs(self):
        r"""dict: Keyword arguments for the model wrapper."""
        out = super(SBMLModelDriver, self).model_wrapper_kwargs
        out.update(
            {'inputs': self.inputs,
             'outputs': self.outputs,
             'integrator': self.integrator,
             'integrator_settings': self.integrator_settings,
             'working_dir': self.working_dir,
             'reset': self.reset, 'selections': self.selections,
             # 'variable_step': self.variable_step,
             'skip_start_time': self.skip_start_time,
             'only_output_final_step': self.only_output_final_step})
        return out
    
    @classmethod
    def model_wrapper(cls, model_file, start_time, steps,
                      inputs=[], outputs=[],
                      integrator=None, integrator_settings={},
                      env=None, working_dir=None, reset=False,
                      selections=None, variable_step=False,
                      skip_start_time=False,
                      only_output_final_step=False):
        r"""Model wrapper."""
        if env is not None:
            os.environ.update(env)
        if working_dir is not None:
            os.chdir(working_dir)
        curr_time = start_time
        model, input_map, output_map = cls.setup_model(
            model_file, inputs=inputs, outputs=outputs,
            integrator=integrator, integrator_settings=integrator_settings,
        )
        if not selections:
            selections = [k for k in model.keys() if not k.startswith('init(')]
        if 'time' not in selections:
            selections = ['time'] + selections
        for k, v in output_map.items():
            if not v['vars']:
                v['vars'] = selections
        while True:
            time = None
            flag = False
            for k, v in input_map.items():
                flag, value = v['comm'].recv_dict(key_order=v['vars'])
                if not flag:
                    print("No more input from %s" % k)
                    break
                for iv in v['vars']:
                    if iv == 'time':
                        time = value[iv]
                    else:
                        model.setValue(iv, value[iv])
            if not flag:
                break
            if time is None:  # pragma: debug
                raise RuntimeError("No time variable recovered.")
            curr_time, out_value = cls.call_model(
                model, curr_time, time, steps,
                start_time=start_time,
                reset=reset, selections=selections,
                variable_step=variable_step)
            for k, v in output_map.items():
                if only_output_final_step:
                    iout = {iv: out_value[iv][-1] for iv in v['vars']}
                    nele = 1
                elif skip_start_time:
                    iout = {iv: out_value[iv][1:] for iv in v['vars']}
                    nele = steps
                else:
                    iout = {iv: out_value[iv] for iv in v['vars']}
                    nele = steps + 1
                if (nele > 1) and (not v['as_array']):
                    for i in range(nele):
                        iiout = {ik: iv[i] for ik, iv in iout.items()}
                        flag = v['comm'].send_dict(iiout, key_order=v['vars'])
                        if not flag:  # pragma: debug
                            raise RuntimeError("Error sending step %d to %s" % (i, k))
                else:
                    flag = v['comm'].send_dict(iout, key_order=v['vars'])
                    if not flag:  # pragma: debug
                        raise RuntimeError("Error sending to %s" % k)

    @classmethod
    def setup_model(cls, model_file, inputs=[], outputs=[],
                    integrator=None, integrator_settings={}):
        r"""Set up model class instance."""
        import roadrunner
        from yggdrasil.languages.Python.YggInterface import (
            YggInput, YggOutput)
        model = roadrunner.RoadRunner(model_file)
        if integrator is not None:
            model.setIntegrator(integrator)
        for k, v in integrator_settings.items():
            model.getIntegrator().setValue(k, v)
        input_map = {}
        output_map = {}
        for x in inputs:
            input_map[x['name']] = {
                'vars': x.get('vars', []),
                'comm': YggInput(x['name'], new_process=True)}
        for x in outputs:
            output_map[x['name']] = {
                'as_array': x.get('as_array', False),
                'vars': x.get('vars', []),
                'comm': YggOutput(x['name'], new_process=True)}
        return model, input_map, output_map

    @classmethod
    def call_model(cls, model, curr_time, end_time, steps,
                   reset=False, start_time=None, selections=None,
                   variable_step=False):
        r"""Call the model."""
        if reset:
            model.reset()
            curr_time = start_time
        out = model.simulate(float(curr_time), float(end_time),
                             selections=selections,
                             steps=int(steps))
        # Unsupported?
        # variableStep=variable_step)
        # try:
        #     out = {k: out[k] for k in out.colnames}
        # except IndexError:
        #     out = {k: out[:, i] for i, k in enumerate(out.colnames)}
        return end_time, out

    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            **kwargs: Additional keyword arguments are passed to the parent
                class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for driver instance.
                deps (list): Dependencies to install.

        """
        out = super(SBMLModelDriver, cls).get_testing_options(**kwargs)
        out['requires_io'] = True
        return out
