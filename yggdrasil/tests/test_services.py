import os
import copy
import pytest
import subprocess
from yggdrasil.services import (
    IntegrationServiceManager, create_service_manager_class, ServerError)
from yggdrasil.examples import yamls as ex_yamls
from yggdrasil.tests import assert_raises
from yggdrasil import runner
from yggdrasil.tools import is_comm_installed


@pytest.mark.parametrize("service_type", ['flask', 'rmq'])
@pytest.mark.parametrize("partial_commtype", ['zmq', 'rmq'])
def test_integration_service(service_type, partial_commtype):
    r"""Test starting/stopping an integration service via flask/rmq."""
    if not is_comm_installed(partial_commtype, language='python'):
        pytest.skip(f"Communicator type '{partial_commtype}' not installed.")
    cls = create_service_manager_class(service_type=service_type)
    if not cls.is_installed():
        pytest.skip("Service type not installed.")
    name = 'ygg_integrations_test'
    test_yml = ex_yamls['fakeplant']['python']
    args = ["yggdrasil", "integration-service-manager",
            f"--manager-name={name}", f"--service-type={service_type}",
            f"--commtype={partial_commtype}"]
    cli = IntegrationServiceManager(name=name, service_type=service_type,
                                    for_request=True)
    assert(not cli.is_running)
    p = subprocess.Popen(args)
    try:
        cli.wait_for_server()
        assert_raises(ServerError, cli.send_request,
                      test_yml, action='invalid')
        print(cli.send_request(test_yml))
        cli.send_request(action='status')
        cli.send_request(test_yml, action='status')
        cli.send_request(test_yml, action='stop')
        cli.send_request(action='status')
        cli.stop_server()
        assert(not cli.is_running)
        p.wait(10)
    finally:
        p.terminate()


@pytest.mark.parametrize("service_type", ['flask'])
def test_registered_service(service_type):
    r"""Test registering an integration service."""
    cls = create_service_manager_class(service_type=service_type)
    if not cls.is_installed():
        pytest.skip("Service type not installed.")
    name = 'ygg_integrations_test'
    test_yml = ex_yamls['fakeplant']['python']
    args = ["yggdrasil", "integration-service-manager",
            f"--manager-name={name}", f"--service-type={service_type}"]
    cli = IntegrationServiceManager(name=name, service_type=service_type,
                                    for_request=True)
    assert(not cli.is_running)
    p = subprocess.Popen(args)
    try:
        cli.wait_for_server()
        assert_raises(KeyError, cli.registry.remove, 'test')
        assert_raises(ServerError, cli.send_request, 'test')
        cli.registry.add('test', test_yml)
        print(cli.send_request('test'))
        assert_raises(ValueError, cli.registry.add, 'test', [])
        cli.send_request('test', action='stop')
        cli.stop_server()
        cli.registry.remove('test')
        assert_raises(KeyError, cli.registry.remove, 'test')
        assert(not cli.is_running)
        p.wait(10)
    finally:
        p.terminate()


@pytest.mark.parametrize("service_type", ['flask', 'rmq'])
@pytest.mark.parametrize("partial_commtype", ['zmq', 'rmq'])
def test_calling_integration_service(service_type, partial_commtype):
    r"""Test calling an integrations as a service in an integration."""
    if not is_comm_installed(partial_commtype, language='python'):
        pytest.skip(f"Communicator type '{partial_commtype}' not installed.")
    cls = create_service_manager_class(service_type=service_type)
    if not cls.is_installed():
        pytest.skip(f"Service type '{service_type}' not installed.")
    test_yml = ex_yamls['fakeplant']['python']
    remote_yml = '_remote'.join(os.path.splitext(test_yml))
    yamls = copy.copy(ex_yamls['fakeplant']['all_nomatlab'])
    yamls.remove(test_yml)
    yamls.append(remote_yml)
    args = ["yggdrasil", "integration-service-manager",
            f"--service-type={service_type}",
            f"--commtype={partial_commtype}"]
    cli = IntegrationServiceManager(service_type=service_type,
                                    for_request=True)
    assert(not cli.is_running)
    p = subprocess.Popen(args)
    try:
        cli.wait_for_server()
        address = cli.address
        with open(remote_yml, 'w') as fd:
            fd.write('\n'.join(['service:',
                                '    name: test',
                                f'    yamls: [{test_yml}]',
                                f'    type: {service_type}',
                                f'    address: {address}']))
        r = runner.get_runner(yamls)
        r.run()
        cli.stop_server()
        assert(not cli.is_running)
        p.wait(10)
    finally:
        if os.path.isfile(remote_yml):
            os.remove(remote_yml)
        p.terminate()
