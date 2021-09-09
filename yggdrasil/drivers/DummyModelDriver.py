from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver


class DummyModelDriver(InterpretedModelDriver):
    r"""Class that stands-in to act as a model utilizing unmatched
    input/output channels."""
    
    executable_type = 'other'
    language = 'dummy'
    full_language = False
    base_languages = ['python']
    language_ext = []
    no_executable = True
    comms_implicit = True

    def __init__(self, *args, **kwargs):
        self.runner = kwargs['runner']
        super(DummyModelDriver, self).__init__(*args, **kwargs)

    @classmethod
    def is_language_installed(self):
        r"""Determine if this model driver is installed on the current
        machine.

        Returns:
            bool: Truth of if this model driver can be run on the current
                machine.

        """
        # This is being run so python exists
        return True

    @classmethod
    def is_configured(cls):
        r"""Determine if the appropriate configuration has been performed (e.g.
        installation of supporting libraries etc.)

        Returns:
            bool: True if the language has been configured.

        """
        # There are not any config options
        return True

    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        return '0'
    
    def before_start(self):
        r"""Actions to perform before the run starts."""
        pass
                                
    def before_loop(self):
        r"""Actions before loop."""
        pass

    def run_loop(self):
        r"""Loop to check if model is still running and forward output."""
        for drv in self.runner.modeldrivers.values():
            if (drv['name'] != self.name) and drv['instance'].is_alive():
                self.wait_flag_attr('break_flag', timeout=1.0)
                return
        self.set_break_flag()

    @property
    def service_partner(self):
        r"""dict: YAML representation of the dummy model that should
        stand-in for the model client-side."""
        out = {'inputs': [], 'outputs': []}
        dir2opp = {'input': 'output', 'output': 'input'}
        for io1, io2 in dir2opp.items():
            for drv in self.yml['%s_drivers' % io1]:
                name = drv[io1 + 's'][0]['name']
                comm = getattr(drv['instance'], '%scomm' % io2[0])
                x = comm.opp_comm_kwargs(for_yaml=True)
                x['name'] = name.split(
                    drv[io1 + 's'][0]['partner_model'] + ':')[-1]
                out[io2 + 's'].append(x)
                if drv['instance']._connection_type.startswith('rpc_'):
                    assert(io2 == 'input')
                    out[io1 + 's'].append({'name': x['name'] + '_response'})
                    out['is_server'] = {io2: x['name'],
                                        io1: x['name'] + '_response'}
        for io1, io2 in dir2opp.items():
            assert(out[io2 + 's'])
            # TODO: Is there a case where a DummyModelDriver will be created
            # for a model that does not have inputs or outputs?
            # if not out[io2 + 's']:
            #     out.pop(io2 + 's')
        return out
