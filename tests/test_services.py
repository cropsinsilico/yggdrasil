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
    if not remote_model_service.is_running:  # pragma: debug
        pytest.skip("Web service app is not running.")
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


def test_validate_model_repo():
    r"""Test validation of YAMLs in the model repository."""
    import git
    import tempfile
    dest0 = '/Users/langmm/yggdrasil_models'
    url0 = "https://github.com/cropsinsilico/yggdrasil_models"
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
