import os
import copy
import pytest
import unittest
import subprocess
from contextlib import contextmanager
from yggdrasil.services import (
    IntegrationServiceManager, create_service_manager_class, ServerError)
from yggdrasil.examples import yamls as ex_yamls
from yggdrasil.tests import assert_raises, requires_language
from yggdrasil import runner, import_as_function
from yggdrasil.tools import is_comm_installed
# TODO: Move into classes so that servers only need to be started once


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
        p.terminate()


def call_integration_service(service_type, partial_commtype,
                             yamls, test_yml, name='test'):
    r"""Call an integration that includes a service."""
    remote_yml = '_remote'.join(os.path.splitext(test_yml))
    yamls = copy.copy(yamls)
    yamls.remove(test_yml)
    yamls.append(remote_yml)
    try:
        with running_service(service_type, partial_commtype) as cli:
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


@pytest.mark.parametrize("service_type", ['flask', 'rmq'])
@pytest.mark.parametrize("partial_commtype", ['zmq', 'rmq'])
def test_integration_service(service_type, partial_commtype):
    r"""Test starting/stopping an integration service via flask/rmq."""
    name = 'ygg_integrations_test'
    test_yml = ex_yamls['fakeplant']['python']
    with running_service(service_type, partial_commtype,
                         manager_name=name) as cli:
        assert_raises(ServerError, cli.send_request,
                      test_yml, action='invalid')
        print(cli.send_request(test_yml))
        cli.send_request(action='status')
        cli.send_request(test_yml, action='status')
        cli.send_request(test_yml, action='stop')
        cli.send_request(action='status')


@pytest.mark.parametrize("service_type", ['flask'])
def test_registered_service(service_type):
    r"""Test registering an integration service."""
    name = 'ygg_integrations_test'
    test_yml = ex_yamls['fakeplant']['python']
    with running_service(service_type, partial_commtype=None,
                         manager_name=name) as cli:
        assert_raises(KeyError, cli.registry.remove, 'test')
        assert_raises(ServerError, cli.send_request, 'test')
        cli.registry.add('test', test_yml)
        print(cli.send_request('test'))
        assert_raises(ValueError, cli.registry.add, 'test', [])
        cli.send_request('test', action='stop')
        cli.stop_server()
        cli.registry.remove('test')
        assert_raises(KeyError, cli.registry.remove, 'test')


@requires_language('c')
@requires_language('c++')
@pytest.mark.parametrize("service_type", ['flask', 'rmq'])
@pytest.mark.parametrize("partial_commtype", ['zmq', 'rmq'])
def test_calling_integration_service(service_type, partial_commtype):
    r"""Test calling an integrations as a service in an integration."""
    call_integration_service(service_type, partial_commtype,
                             ex_yamls['fakeplant']['all_nomatlab'],
                             ex_yamls['fakeplant']['python'])


@requires_language('c')
@requires_language('c++')
@pytest.mark.parametrize("service_type", ['flask'])
@pytest.mark.parametrize("partial_commtype", ['zmq'])
def test_calling_server_as_service(service_type, partial_commtype):
    r"""Test calling an integration service that is a server in an
    integration."""
    os.environ.update(FIB_ITERATIONS='3',
                      FIB_SERVER_SLEEP_SECONDS='0.01')
    yamls = ex_yamls['rpcFib']['all_nomatlab']
    service = None
    for x in yamls:
        if 'Srv' in x:
            service = x
            break
    call_integration_service(service_type, partial_commtype, yamls, service,
                             name='rpcFibSrv')


@pytest.mark.parametrize("service_type", ['flask', 'rmq'])
@pytest.mark.parametrize("partial_commtype", ['zmq'])
def test_calling_service_as_function(service_type, partial_commtype):
    r"""Test calling an integrations as a service in an integration."""
    name = 'test'
    test_yml = ex_yamls['fakeplant']['python']
    with running_service(service_type, partial_commtype) as cli:
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
