import os
import copy
import pytest
import itertools
import shutil
from yggdrasil.services import (
    ServerError, validate_model_submission)
from yggdrasil.examples import yamls as ex_yamls
from yggdrasil import runner, import_as_function


def _make_ids(ids):
    return ','.join([str(x) for x in ids])


@pytest.mark.remote_service
@pytest.mark.language('c')
@pytest.mark.language('c++')
def test_call_integration_remote(remote_model_service_address,
                                 remote_model_service):
    r"""Test with remote integration service."""
    name = 'photosynthesis'
    test_yml = ex_yamls['fakeplant']['python']
    copy_yml = ex_yamls['fakeplant']['c'][0]
    remote_yml = '_remote'.join(os.path.splitext(test_yml))
    yamls = copy.copy(ex_yamls['fakeplant']['all_nomatlab'])
    yamls.remove(test_yml)
    yamls.remove(copy_yml)
    yamls.append(remote_yml)
    try:
        shutil.copy(copy_yml, remote_yml)
        with open(remote_yml, 'a') as fd:
            fd.write('\n'.join([
                'service:',
                f'    name: {name}',
                '    type: flask',
                f'    address: {remote_model_service_address}'
            ]))
        r = runner.get_runner(yamls)
        r.run()
        assert not r.error_flag
    finally:
        if os.path.isfile(remote_yml):
            os.remove(remote_yml)
        remote_model_service.send_request(name, action='stop')


class TestServices(object):
    r"""Class to test integration services."""

    @pytest.fixture(params=itertools.product(['flask'], [None]),
                    ids=_make_ids, scope="class", autouse=True)
    def running_service(self, request, running_service):
        track_memory = (request.param[0] == 'flask'
                        and request.param[1] is None)
        with running_service(request.param[0], request.param[1],
                             track_memory=track_memory) as cli:
            self.cli = cli
            yield cli
            self.cli = None

    def call_integration_service(self, cli, yamls, test_yml, copy_yml=None,
                                 name='test', yaml_param=None):
        r"""Call an integration that includes a service."""
        remote_yml = '_remote'.join(os.path.splitext(test_yml))
        yamls = copy.copy(yamls)
        yamls.remove(test_yml)
        if copy_yml:
            yamls.remove(copy_yml)
        yamls.append(remote_yml)
        service_type = cli.service_type
        try:
            address = cli.address
            if copy_yml:
                shutil.copy(copy_yml, remote_yml)
                remote_code = 'a'
            else:
                remote_code = 'w'
            lines = ['service:',
                     f'    name: {name}',
                     f'    yamls: [{test_yml}]',
                     f'    type: {service_type}',
                     f'    address: {address}']
            if yaml_param:
                lines.append('    yaml_param:')
                for k, v in yaml_param.items():
                    lines.append(f'        {k}: "{v}"')
            with open(remote_yml, remote_code) as fd:
                fd.write('\n'.join(lines))
            r = runner.get_runner(yamls)
            r.run()
            assert not r.error_flag
        finally:
            if os.path.isfile(remote_yml):
                os.remove(remote_yml)

    def test_git_fails(self, running_service):
        r"""Test that sending a request for a git YAML fails."""
        cli = running_service
        test_yml = ("git:https://github.com/cropsinsilico/example-fakemodel/"
                    "fakemodel3.yml")
        assert not os.path.isfile(
            "cropsinsilico/example-fakemodel/fakemodel3.yml")
        with pytest.raises(ServerError):
            cli.send_request(yamls=test_yml, action='start')

    def test_integration_service(self, running_service):
        r"""Test starting/stopping an integration service via flask/rmq."""
        cli = running_service
        test_yml = ex_yamls['fakeplant']['python']
        with pytest.raises(ServerError):
            cli.send_request(test_yml, action='invalid')
        print(cli.send_request(test_yml))
        cli.printStatus()
        if cli.service_type == 'flask':
            import requests
            r = requests.get(cli.address)
            r.raise_for_status()
        cli.send_request(test_yml, action='status')
        cli.send_request(action='status', client_id=None)
        cli.send_request(test_yml, yamls=test_yml, action='stop')
        with pytest.raises(ServerError):
            cli.send_request(['invalid'], action='stop')
        cli.printStatus(return_str=True)
        cli.send_request([test_yml])
        cli.send_request([test_yml], action='stop')

    def test_registered_service(self, running_service):
        r"""Test registering an integration service."""
        if (((running_service.commtype != 'rest')
             or (running_service.service_type != 'flask'))):
            pytest.skip("redundent test")
        cli = running_service
        test_yml = ex_yamls['fakeplant']['python']
        assert not os.path.isfile('test')
        with pytest.raises(KeyError):
            cli.registry.remove('test')
        with pytest.raises(ServerError):
            cli.send_request('test')
        print(cli.send_request('FakePlant'))
        cli.registry.add('test', test_yml, namespace='remote')
        print(cli.send_request('test'))
        with pytest.raises(ValueError):
            cli.registry.add('test', [test_yml])
        cli.send_request('test', action='stop')
        # cli.stop_server()
        cli.registry.remove('test')
        with pytest.raises(KeyError):
            cli.registry.remove('test')
        # Register from file
        reg_coll = os.path.join(os.path.dirname(test_yml),
                                'registry_collection.yml')
        test_yml_base = os.path.basename(test_yml)
        with open(reg_coll, 'w') as fd:
            fd.write(f'photosynthesis:\n  - {test_yml_base}')
        try:
            cli.registry.add(reg_coll)
            print(cli.send_request('photosynthesis', namespace='phot'))
            with pytest.raises(ValueError):
                cli.registry.add('photosynthesis', [test_yml], invalid=1)
            cli.send_request('photosynthesis', action='stop')
            cli.registry.remove(reg_coll)
            with pytest.raises(KeyError):
                cli.registry.remove('photosynthesis')
        finally:
            os.remove(reg_coll)

    @pytest.mark.language('c')
    @pytest.mark.language('c++')
    def test_calling_integration_service(self, running_service):
        r"""Test calling an integrations as a service in an integration."""
        self.call_integration_service(
            running_service,
            ex_yamls['fakeplant']['all_nomatlab'],
            ex_yamls['fakeplant']['python'],
            copy_yml=ex_yamls['fakeplant']['c'][0])

    @pytest.mark.language('c')
    @pytest.mark.language('c++')
    def test_calling_server_as_service(self, running_service):
        r"""Test calling an integration service that is a server in an
        integration."""
        if (((running_service.commtype != 'rest')
             or (running_service.service_type != 'flask'))):
            pytest.skip("redundent test")  # pragma: testing
        yaml_param = dict(FIB_ITERATIONS='3',
                          FIB_SERVER_SLEEP_SECONDS='0.01')
        os.environ.update(yaml_param)
        yamls = ex_yamls['rpcFib']['all_nomatlab']
        service = None
        for x in yamls:
            if 'Srv' in x:
                service = x
                break
        self.call_integration_service(running_service, yamls, service,
                                      name='rpcFibSrv',
                                      yaml_param=yaml_param)

    def test_calling_service_as_function(self, running_service):
        r"""Test calling an integrations as a service in an integration."""
        # if running_service.commtype != None:
        #     pytest.skip("redundent test")
        cli = running_service
        name = 'test'
        test_yml = ex_yamls['fakeplant']['python']
        try:
            cli.registry.add(name, test_yml)
            fmodel = import_as_function(name, cli.address)
            input_args = {}
            for x in fmodel.arguments:
                input_args[x] = 1.0
            fmodel.model_info()
            result = fmodel(**input_args)
            for x in fmodel.returns:
                assert x in result
            result = fmodel(*list(input_args.values()))
            for x in fmodel.returns:
                assert x in result
            fmodel.stop()
            fmodel.stop()
        finally:
            cli.registry.remove(name)

    def test_calling_model_as_service(self, running_service):
        r"""Test calling a model as a service."""
        cli = running_service
        if cli.service_type != 'flask':
            pytest.skip('Only valid for flask services')
        name = 'fakeplant_python'
        test_yml = ex_yamls['fakeplant']['python']
        try:
            cli.registry.add(name, test_yml)
            out = cli.send_request({'light_intensity': 1.0,
                                    'temperature': 35.0,
                                    'co2': 50.0}, model=name)
            with pytest.raises(ServerError):
                out = cli.send_request({'light_intensity': 1.0,
                                        'temperature': 35.0,
                                        'co2': 50.0}, model='invalid')
            assert out == {'photosynthesis_rate': 1.4285714285714286}
        finally:
            cli.registry.remove(name)


def test_validate_model_submission():
    r"""Test validate_model_submission"""
    import git
    yamldir = os.path.join(os.path.dirname(__file__), 'yamls')
    repodir = os.path.join(yamldir, 'cropsinsilico')
    fname_license = os.path.join(repodir, 'example-fakemodel', 'LICENSE')
    assert not os.path.isdir(repodir)
    try:
        fname = os.path.join(yamldir, 'FakePlant.yaml')
        validate_model_submission([fname])
        os.remove(fname_license)
        with pytest.raises(RuntimeError):
            validate_model_submission(fname)
    finally:
        if os.path.isdir(repodir):
            git.rmtree(repodir)


def test_validate_model_repo(yggdrasil_model_repository_url,
                             yggdrasil_model_repository_dir):
    r"""Test validation of YAMLs in the model repository."""
    import git
    import tempfile
    dest0 = yggdrasil_model_repository_dir
    url0 = yggdrasil_model_repository_url
    for suffix in ["", "_test"]:
        dest = dest0 + suffix
        dest_exists = os.path.isdir(dest)
        if not dest_exists:
            dest = os.path.join(tempfile.gettempdir(),
                                "model_repo" + suffix)
            dest_exists = os.path.isdir(dest)
        try:
            repo = None
            if not dest_exists:
                repo = git.Repo.clone_from(url0 + suffix, dest)
            model_dir = os.path.join(dest, "models")
            validate_model_submission(model_dir)
            if not dest_exists:
                repo.close()
        finally:
            if not dest_exists:
                if os.path.isdir(dest):
                    git.rmtree(dest)


class TestRegisteredIntegrationFunction(object):
    r"""Class to test calling a registered integration function."""

    name = None
    request = None
    nrep = 2
    _write_keys = False

    @pytest.fixture(
        scope="class", params=['function', 'local', 'remote']
    )
    def service_type(self, request):
        r"""str: Type of service to test."""
        if self.name is None:
            pytest.skip("name not set")
        return request.param

    @pytest.fixture(scope="class")
    def service_client(self, service_type, running_service,
                       remote_model_service,
                       yggdrasil_model_repository_dir):
        r"""Service manager client."""
        if service_type == 'local':
            with running_service('flask', include_yggdrasil_models=True) as cli:
                yield cli
        elif service_type == 'remote':
            yield remote_model_service
        elif service_type == 'function':
            yaml = os.path.join(yggdrasil_model_repository_dir, 'models',
                                f'{self.name}.yaml')
            function = runner.YggFunction(yaml)
            yield function
            function.stop()

    @pytest.fixture(scope="class")
    def service_address(self, service_type, service_client):
        r"""Address for the current service."""
        if service_type == 'function':
            return None
        address = service_client.address
        if not address.endswith('/'):
            address += '/'
        address += self.name
        return address

    @pytest.fixture(scope="class")
    def action_address(self, service_address):
        r"""Get a REST API service address.

        Args:
            action (str, optional): Action that address should be
                returned for.

        Returns:
            str: Address for service action REST API call.

        """

        def _action_address(action=None):
            address = service_address
            if action:
                address += f'/{action}'
            return address

        return _action_address

    @pytest.fixture(scope="class")
    def function_request(self, service_client):
        r"""Perform a function request.
        
        Args:
            request (dict, optional): Request to send.
            action (str, optional): Action that address should be
                returned for.

        Returns:
            dict: Response to request.

        """
        function = service_client

        def _function_request(request={}, action=None):
            if action in ['call', None]:
                return function(**request)
            elif action == 'info':
                return function.function_info
            elif action == 'n8n_form_node':
                return function.n8n_form_node
            else:
                raise ValueError(f"Unsupported action: {action}")

        return _function_request

    @pytest.fixture(scope="class")
    def service_request(self, service_type, action_address,
                        function_request):
        r"""Send a request to the REST API for a service action via
        POST.

        Args:
            request (dict, optional): Request to send.
            action (str, optional): Action that address should be
                returned for.

        Returns:
            dict: Response to request.

        """

        if service_type == 'function':
            _service_request = function_request
        else:
            def _service_request(request={}, action=None):
                import requests
                address = action_address(action=action)
                r = requests.post(address, json=request)
                r.raise_for_status()
                response = r.json()
                if 'error' in response:
                    print(response['traceback'])
                    raise RuntimeError(response['error'])
                return response
        return _service_request

    @pytest.fixture
    def call_method(self, service_type, service_request):
        r"""Allow call method to be parametrized via string."""

        def call(request):
            if service_type in ['local', 'remote']:
                service_request(action='delete')
            return service_request(request)

        return call

    @pytest.fixture
    def base_request(self):
        r"""dict: Base request."""
        if self.request is None:
            pytest.skip("request not set")
        return self.request

    @pytest.fixture(scope="class")
    def write_keys(self, service_type):
        r"""Write the response keys to a file.

        Args:
            response (dict): Response.

        """

        def _write_keys(response):
            if not self._write_keys:
                return
            fname = os.path.join(os.getcwd(),
                                 f'{self.name}_{service_type}_keys.txt')
            with open(fname, 'w') as fd:
                fd.write('\n'.join(sorted(list(response.keys()))))
            print(f"WROTE RESPONSE KEYS TO {fname}")

        return _write_keys

    @pytest.fixture(scope="class")
    def check_response(self):
        r"""Check if the response matches expectations."""

        def _check_response(request, response):
            return True

        return _check_response

    def test_landing(self, service_type, service_client, base_request,
                     call_method):
        r"""Test that the landing page returns properly before and
        after function called."""
        if service_type == 'function':
            service_client.printStatus()
            assert isinstance(
                service_client.printStatus(return_str=True), str)
            return
        import requests
        r = requests.get(service_client.address)
        r.raise_for_status()
        call_method(base_request)
        r = requests.get(service_client.address)
        r.raise_for_status()

    def test_request(self, call_method, base_request,
                     check_response):
        r"""Test call to the registered integration."""
        for _ in range(self.nrep):
            response = call_method(base_request)
            check_response(base_request, response)

    def test_info(self, service_request):
        r"""Test function info."""
        import pprint
        pprint.pprint(service_request(action='info'))

    def test_n8n_form_node(self, service_request):
        r"""Test function n8n_form_node."""
        import pprint
        pprint.pprint(service_request(action='n8n_form_node'))


class TestRegisteredBioCro(TestRegisteredIntegrationFunction):
    r"""Test registered BioCro integration function."""

    name = 'BioCro'
    keys = ['hour', 'year', 'Grain']

    @pytest.fixture(
        params=[
            {'crop': 'soybean', 'year': 2002, 'doy': 152},
            {'crop': 'soybean', 'year': 2002, 'doy': 152,
             'output_timesteps': True},
        ]
    )
    def base_request(self, request):
        r"""dict: Base request."""
        return request.param

    @pytest.fixture(scope="class")
    def check_response(self, service_type, write_keys):
        r"""Check if the response matches expectations."""
        import numpy as np

        def _check_response(request, response):
            assert isinstance(response, dict)
            write_keys(response)
            try:
                for k in self.keys:
                    assert k in response
                assert len(response) == 479
            except AssertionError:
                self._write_keys = True
                write_keys(response)
                raise
            if request.get('output_timesteps', False):
                for v in response.values():
                    if service_type == 'function':
                        assert isinstance(v, np.ndarray)
                    else:
                        assert isinstance(v, list)
                    assert len(v) == 3288

        return _check_response
