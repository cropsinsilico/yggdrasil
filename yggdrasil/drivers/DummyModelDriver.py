from collections import OrderedDict
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
    _schema_properties = {
        'client_id': {'type': 'string'},
        'service': {'type': 'string'},
        'service_address': {'type': 'string'},
        'service_models': {
            'type': 'array', 'items': {'type': 'string'},
        },
    }

    def __init__(self, *args, **kwargs):
        self.runner = kwargs['runner']
        super(DummyModelDriver, self).__init__(*args, **kwargs)
        self.service_cli = None
        if self.service:
            from yggdrasil.services import IntegrationServiceManager
            self.service_cli = IntegrationServiceManager(
                for_request=True, address=self.service_address,
                client_id=self.client_id)

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
    def configuration_steps(cls):
        r"""Get a list of configuration steps with tuples of flags and
        boolean values.

        Returns:
            OrderedDict: Pairs of descriptions and states for
                different steps in the configuration all steps must be
                True for the language to be configured.

        """
        return OrderedDict()

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
        if self.service and not self.service_alive():
            self.debug("Service is not running")
            self.set_break_flag()
            return
        for drv in self.runner.modeldrivers.values():
            if (drv['name'] != self.name) and drv['instance'].is_alive():
                self.wait_flag_attr('break_flag', timeout=1.0)
                return
        self.set_break_flag()

    def close_connections(self):
        r"""Perform model exits for connections to this model."""
        if self.service_alive():
            request = {'action': 'stop', 'name': self.service}
            self.service_cli.send_request(**request)
        return super(DummyModelDriver, self).close_connections()

    def service_alive(self):
        r"""bool: True if this dummy driver is a service partner and the
        service is still alive."""
        if not self.service_cli:
            return False
        from yggdrasil.services import ServerError, ClientError
        request = {'action': 'ping', 'name': self.service}
        try:
            response = self.service_cli.send_request(**request)
            if response['status'] == 'stopping':
                self.service_cli = None
            return (response['status'] == 'running')
        except (ServerError, ClientError):
            return False

    @property
    def service_partner(self):
        r"""dict: YAML representation of the dummy model that should
        stand-in for the model client-side."""
        from yggdrasil.communication import strip_model_prefix
        out = {
            'name': f'{self.name}-PARTNER',
            'args': f'{self.name}-PARTNER',
            'language': 'dummy',
            'inputs': [],
            'outputs': [],
            'service_models': [],
        }
        dir2opp = {'input': 'output', 'output': 'input'}
        for io1, io2 in dir2opp.items():
            for drv in self.yml[f'{io1}_drivers']:
                service_model = drv[f'{io1}s'][0]['partner_model']
                name = strip_model_prefix(
                    drv[io1 + 's'][0]['name'], service_model)
                comm = getattr(drv['instance'], f'{io2[0]}comm')
                x = comm.opp_comm_kwargs(for_yaml=True)
                x.pop('model', None)
                if service_model not in out['service_models']:
                    out['service_models'].append(service_model)
                x.update(
                    name=name,
                    service_model=service_model,
                )
                out[f'{io2}s'].append(x)
                if drv['instance']._connection_type.startswith('rpc_'):
                    assert io2 == 'input'
                    out[io1 + 's'].append({'name': x['name'] + '_response'})
                    out['is_server'] = {io2: x['name'],
                                        io1: x['name'] + '_response'}
        for io1, io2 in dir2opp.items():
            assert out[io2 + 's']
            # TODO: Is there a case where a DummyModelDriver will be created
            # for a model that does not have inputs or outputs?
            # if not out[io2 + 's']:
            #     out.pop(io2 + 's')
        return out
