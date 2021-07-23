import pytest
import subprocess
from yggdrasil.tools import sleep, TimeOut
from yggdrasil.services import (
    ModelManager, create_model_manager_class, ServerError)
from yggdrasil.examples import yamls as ex_yamls
from yggdrasil.tests import assert_raises


@pytest.mark.parametrize("service_type", ['flask', 'rmq'])
def test_model_service(service_type):
    r"""Test starting/stopping a model as a service via flask."""
    cls = create_model_manager_class(service_type=service_type)
    if not cls.is_installed():
        pytest.skip("Service type not installed.")
    name = 'ygg_models_test'
    test_yml = ex_yamls['fakeplant']['python']
    args = ["yggdrasil", "model-service-manager",
            f"--name={name}", f"--service-type={service_type}"]
    cli = ModelManager(name=name, service_type=service_type,
                       for_request=True)
    assert(not cli.is_running)
    p = subprocess.Popen(args)
    try:
        T = TimeOut(10.0)
        while (not cli.is_running) and (not T.is_out):
            print('waiting for server to start')
            sleep(1)
        assert(cli.is_running)
        assert_raises(ServerError, cli.send_request,
                      test_yml, action='invalid')
        print(cli.send_request(test_yml))
        cli.send_request(action='info')
        cli.send_request(test_yml, action='info')
        cli.send_request(test_yml, action='stop')
        cli.send_request(action='info')
        cli.stop_server()
        assert(not cli.is_running)
        p.wait(10)
    finally:
        p.terminate()
