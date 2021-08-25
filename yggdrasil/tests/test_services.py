import os
import copy
import pytest
import unittest
import subprocess
import itertools
from contextlib import contextmanager
from yggdrasil.services import (
    IntegrationServiceManager, create_service_manager_class, ServerError)
from yggdrasil.examples import yamls as ex_yamls
from yggdrasil.tests import assert_raises, requires_language
from yggdrasil import runner, import_as_function
from yggdrasil.tools import is_comm_installed


def get_skips(service_type, partial_commtype=None, check_running=False):
    r"""Create a list of conditions and skip messages."""
    out = []
    if partial_commtype is not None:
        out.append(
            (not is_comm_installed(partial_commtype, language='python'),
             f"Communicator type '{partial_commtype}' not installed."))
    cls = create_service_manager_class(service_type=service_type)
    out.append(
        (not cls.is_installed(),
         f"Service type '{service_type}' not installed."))
    if check_running and cls.is_installed():
        cli = IntegrationServiceManager(service_type=service_type,
                                        commtype=partial_commtype,
                                        for_request=True)
        out.append(
            (not cli.is_running,
             f"Service of type {service_type} not running."))
    return out


def requires_service(service_type='flask', partial_commtype=None):
    r"""Decorator factory for marking tests that require that an yggdrasil
    service is running.

    Args:
        service_type (str, optional): Service type that is required.
            Defaults to 'flask'.

    Returns:
        function: Decorator for test.

    """

    def wrapper(function):
        for s in get_skips(service_type, partial_commtype=partial_commtype,
                           check_running=True):
            function = unittest.skipIf(*s)(function)
        return function
    
    return wrapper


def check_settings(service_type, partial_commtype=None):
    r"""Check that the requested settings are available, skipping if not."""
    skips = get_skips(service_type, partial_commtype=partial_commtype)
    for s in skips:
        if s[0]:
            pytest.skip(s[1])


@contextmanager
def running_service(service_type, partial_commtype=None,
                    manager_name=None):
    r"""Context manager to run and clean-up an integration service."""
    check_settings(service_type, partial_commtype)
    args = ["yggdrasil", "integration-service-manager",
            f"--service-type={service_type}"]
    if partial_commtype is not None:
        args.append(f"--commtype={partial_commtype}")
    if manager_name is not None:
        args.append(f"--manager-name={manager_name}")
    cli = IntegrationServiceManager(name=manager_name,
                                    service_type=service_type,
                                    commtype=partial_commtype,
                                    for_request=True)
    assert(not cli.is_running)
    p = subprocess.Popen(args)
    try:
        cli.wait_for_server()
        yield cli
        cli.stop_server()
        assert(not cli.is_running)
        p.wait(10)
    finally:
        if p.returncode is None:
            p.terminate()


def _make_ids(ids):
    return ','.join([str(x) for x in ids])

        
class TestServices(object):
    r"""Class to test integration services."""

    @pytest.fixture(params=itertools.product(['flask', 'rmq'], [None, 'rmq']),
                    ids=_make_ids, scope="class", autouse=True)
    def running_service(self, request):
        with running_service(request.param[0], request.param[1]) as cli:
            self.cli = cli
            yield cli
            self.cli = None

    def call_integration_service(self, cli, yamls, test_yml, name='test'):
        r"""Call an integration that includes a service."""
        remote_yml = '_remote'.join(os.path.splitext(test_yml))
        yamls = copy.copy(yamls)
        yamls.remove(test_yml)
        yamls.append(remote_yml)
        service_type = cli.service_type
        try:
            address = cli.address
            with open(remote_yml, 'w') as fd:
                fd.write('\n'.join(['service:',
                                    f'    name: {name}',
                                    f'    yamls: [{test_yml}]',
                                    f'    type: {service_type}',
                                    f'    address: {address}']))
            r = runner.get_runner(yamls)
            r.run()
            assert(not r.error_flag)
        finally:
            if os.path.isfile(remote_yml):
                os.remove(remote_yml)

    def test_integration_service(self, running_service):
        r"""Test starting/stopping an integration service via flask/rmq."""
        cli = running_service
        test_yml = ex_yamls['fakeplant']['python']
        assert_raises(ServerError, cli.send_request,
                      test_yml, action='invalid')
        print(cli.send_request(test_yml))
        cli.send_request(action='status')
        if cli.service_type == 'flask':
            import requests
            r = requests.get(cli.address)
            r.raise_for_status()
        cli.send_request(test_yml, action='status')
        cli.send_request(test_yml, action='stop')
        cli.send_request(action='status')

    def test_registered_service(self, running_service):
        r"""Test registering an integration service."""
        if (((running_service.commtype != 'rest')
             or (running_service.service_type != 'flask'))):
            pytest.skip("redundent test")
        cli = running_service
        test_yml = ex_yamls['fakeplant']['python']
        assert_raises(KeyError, cli.registry.remove, 'test')
        assert_raises(ServerError, cli.send_request, 'test')
        cli.registry.add('test', test_yml)
        print(cli.send_request('test'))
        assert_raises(ValueError, cli.registry.add, 'test', [test_yml])
        cli.send_request('test', action='stop')
        # cli.stop_server()
        cli.registry.remove('test')
        assert_raises(KeyError, cli.registry.remove, 'test')
        # Register from file
        reg_coll = 'registry_collection.yml'
        with open(reg_coll, 'w') as fd:
            fd.write(f'photosynthesis:\n  - {test_yml}')
        try:
            cli.registry.add(reg_coll)
            print(cli.send_request('photosynthesis'))
            assert_raises(ValueError, cli.registry.add,
                          'photosynthesis', [test_yml])
            cli.send_request('photosynthesis', action='stop')
            cli.registry.remove(reg_coll)
            assert_raises(KeyError, cli.registry.remove, 'photosynthesis')
        finally:
            os.remove(reg_coll)

    @requires_language('c')
    @requires_language('c++')
    def test_calling_integration_service(self, running_service):
        r"""Test calling an integrations as a service in an integration."""
        self.call_integration_service(
            running_service,
            ex_yamls['fakeplant']['all_nomatlab'],
            ex_yamls['fakeplant']['python'])

    @requires_language('c')
    @requires_language('c++')
    def test_calling_server_as_service(self, running_service):
        r"""Test calling an integration service that is a server in an
        integration."""
        if (((running_service.commtype != 'rest')
             or (running_service.service_type != 'flask'))):
            pytest.skip("redundent test")
        os.environ.update(FIB_ITERATIONS='3',
                          FIB_SERVER_SLEEP_SECONDS='0.01')
        yamls = ex_yamls['rpcFib']['all_nomatlab']
        service = None
        for x in yamls:
            if 'Srv' in x:
                service = x
                break
        self.call_integration_service(running_service, yamls, service,
                                      name='rpcFibSrv')

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
                assert(x in result)
            result = fmodel(*list(input_args.values()))
            for x in fmodel.returns:
                assert(x in result)
            fmodel.stop()
            fmodel.stop()
        finally:
            cli.registry.remove(name)
