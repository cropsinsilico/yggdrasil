"""This module provides tools for running models using yggdrasil."""
import sys
import os
import time
import copy
import signal
import atexit
from pprint import pformat
from itertools import chain
import socket
from collections import OrderedDict
from yggdrasil.tools import YggClass
from yggdrasil.config import ygg_cfg, cfg_environment, temp_config
from yggdrasil import platform, yamlfile, rapidjson
from yggdrasil.drivers import create_driver, DirectConnectionDriver
from yggdrasil.components import import_component
from yggdrasil.multitasking import init_mpi, YggTaskLoop, AsyncResult
from yggdrasil.drivers.DuplicatedModelDriver import DuplicatedModelDriver
from yggdrasil.broker import YggBroker


COLOR_TRACE = '\033[30;43;22m'
COLOR_NORMAL = '\033[0m'


class IntegrationError(BaseException):
    r"""Error raised when there is an error in an integration."""
    pass


class IntegrationFunctionError(IntegrationError):
    r"""Error raised when an error occurs during a call to an
    integration function."""

    def __init__(self, msg, partial_output=None):
        self.partial_output = partial_output
        super(IntegrationFunctionError, self).__init__(msg)


class YggFunction(YggClass):
    r"""This class wraps function-like behavior around a model.

    Args:
        model_yaml (str, list): Full path to one or more YAML specification
            files containing information defining a partial integration. If
            service_address is set, this should be the name of a service
            registered with the service manager running at the provided
            address.
        service_address (str, optional): Address for service manager that is
            capable of running the specified integration. Defaults to None
            and is ignored.
        signal_handler (function, optional): Function that should handle
            received SIGINT and SIGTERM signals. Defaults to
            runner.signal_handler.
        **kwargs: Additional keyword arguments are passed to the YggRunner
            constructor.

    Attributes:
        outputs (dict): Input channels providing access to model output.
        inputs (dict): Output channels providing access to model input.
        runner (YggRunner): Runner for model.

    """
    
    def __init__(self, model_yaml, service_address=None,
                 signal_handler=None, name=None, **kwargs):
        super(YggFunction, self).__init__()
        # Create and start runner in another process
        if name is None:
            name = os.path.splitext(os.path.basename(model_yaml))[0]
        self.dummy_name = f'{name}-FUNCTION'
        self.model_yaml = model_yaml
        self.service_address = service_address
        self.runner_kwargs = dict(
            kwargs, name=name,
            complete_partial=self.dummy_name,
        )
        self.runner_kwargs['complete_partial'] = self.dummy_name
        self._stop_called = False
        self._comms = {'input': {}, 'output': {}}
        self._opp_comms = {'input': {}, 'output': {}}
        self._vars = {'input': {}, 'output': {}}
        self.runner = None
        self.run(signal_handler=signal_handler)

    # def widget_function(self, *args, **kwargs):
    #     # import matplotlib.pyplot as plt
    #     # ncols = min(3, len(arguments))
    #     # nrows = int(ceil(float(len(arguments))/float(ncols)))
    #     # plt.show()
    #     out = self(*args, **kwargs)
    #     return out

    # def widget(self, *args, **kwargs):
    #     from ipywidgets import interact_manual
    #     return interact_manual(self.widget_function, *args, **kwargs)

    def __del__(self):
        self.stop()
        
    def is_alive(self):
        r"""bool: True if the function is still alive."""
        return (self.runner is not None and self.runner.is_alive
                and not self._stop_called)

    def argument_models(self, io, name):
        r"""Get the name of the model that the argument is passed to.

        Args:
            io (str): Direction of argument ('input' or 'output').
            name (str): Argument name.

        Returns:
            list: Names of models that the argument is passed to.

        """
        comm = self._vars[io][name]
        if io == 'input':
            out = [x['partner_model'] for x in comm['outputs']]
        else:
            out = [x['partner_model'] for x in comm['inputs']]
        return out

    def argument_datatype(self, io, name):
        r"""Get the datatype for an argument.

        Args:
            io (str): Direction of argument ('input' or 'output').
            name (str): Argument name.

        Returns:
            dict: JSON schema describing the data type.

        """
        if name in self._vars[io][name]['vars_datatypes']:
            return self._vars[io][name]['vars_datatypes'][name]
        comm = self._vars[io][name]['comm']
        if comm.commtype == 'client':
            if io == 'input':
                out = comm.ocomm.serializer.datatype
            else:
                out = comm.icomm.serializer.datatype
        else:
            out = comm.serializer.datatype
        return out

    # def comm_datatype(self, io, name):
    #     r"""Get the datatype for a communicator.

    #     Args:
    #         io (str): Direction of communicator ('input' or 'output').
    #         name (str): Communicator name.

    #     Returns:
    #         dict: JSON schema describing the data type.

    #     """
    #     comm = self._opp_comms[io][name]
    #     out = {}
    #     import pprint
    #     print(io, name)
    #     pprint.pprint(comm)
    #     import pdb; pdb.set_trace()
    #     return out

    def comm_info(self, io, name):
        r"""Get information about a communicator.

        Args:
            io (str): Direction of communicator ('input' or 'output').
            name (str): Communicator name.

        Returns:
            dict: Info about the communicator.

        """
        comm = self._comms[io][name]
        out = {'arguments': comm['var_names']}
        if io == 'input':
            out['models'] = [x['partner_model'] for x in comm['outputs']]
        else:
            out['models'] = [x['partner_model'] for x in comm['inputs']]
        return out

    def argument_info(self, io, name):
        r"""Get information about an argument.

        Args:
            io (str): Direction of argument ('input' or 'output').
            name (str): Argument name.

        Returns:
            dict: Info about the argument.

        """
        out = {
            'models': self.argument_models(io, name),
            'datatype': self.argument_datatype(io, name),
        }
        # TODO: Add description
        return out

    @property
    def inputs(self):
        r"""dict: Input communicators."""
        return self._comms['input']

    @property
    def outputs(self):
        r"""dict: Output communicators."""
        return self._comms['output']

    @property
    def function_info(self):
        r"""dict: Information about the function."""
        out = {
            'models': [
                x['name'] for x in self.runner.modeldrivers.values()
                if x['name'] != self.dummy_name
            ],
        }
        for io in ['input', 'output']:
            out[io] = {}
            for v in self._vars[io].keys():
                out[io][v] = self.argument_info(io, v)
        return out

    @property
    def n8n_form_node(self):
        r"""dict: Parameters describing an n8n tool for this function."""

        def n8n_dtype(x):
            out = x['type']
            if out in ['1darray', 'ndarray']:
                out = 'array'
            elif out in ['scalar']:
                if x['subtype'] in ['string', 'bytes', 'unicode']:
                    out = 'string'
                else:
                    out = 'number'
            if out not in ['array', 'object', 'string', 'number',
                           'integer', 'boolean', 'null']:
                raise TypeError(f"Cannot create an n8n form argument "
                                f"with type \"{out}\"")
            return out

        name = self.runner.name
        values = []
        datatypes = []
        for k, v in self._vars['input'].items():
            datatype = self.argument_datatype('input', k)
            ivalue = {
                "fieldLabel": k,
                "fieldType": n8n_dtype(datatype),
                "requiredField": True,
            }
            if 'default' in datatype:
                ivalue["placeholder"] = datatype['default']
            values.append(ivalue)
            datatypes.append(datatype)
        if ((len(values) == 1 and values[0]["fieldType"] == "object"
             and datatypes[0].get('properties', None))):
            values = []
            for k, v in datatypes[0]['properties'].items():
                ivalue = {
                    "fieldLabel": k,
                    "fieldType": n8n_dtype(v),
                }
                if 'default' in v:
                    ivalue["placeholder"] = v['default']
                if k in datatypes[0].get('required', []):
                    ivalue["requiredField"] = True
                values.append(ivalue)
        out = {
            "name": "n8n Form Trigger",
            "type": "n8n-nodes-base.formTrigger",
            "typeVersion": 2.1,
            "parameters": {
                "path": f"{name}-form".lower(),
                "formTitle": f"Run {name} model/integration",
                "formFields": {
                    "values": values,
                    "options": {},
                },
            },
            "position": [600, 380],
        }
        return out

    @property
    def argument_datatypes(self):
        r"""dict: Datatypes for each function argument."""
        out = {}
        for v in self._vars['input'].keys():
            out[v] = self.argument_datatype('input', v)
        return out

    @property
    def return_datatypes(self):
        r"""dict: Datatypes for each function return variable."""
        out = {}
        for v in self._vars['output'].keys():
            out[v] = self.argument_datatype('output', v)
        if len(out) == 1:
            out = out[list(out.keys())[0]]
        return out

    @property
    def arguments(self):
        r"""list: Names of function arguments."""
        return list(self._vars['input'].keys())

    @property
    def returns(self):
        r"""list: Name of function output variables."""
        return list(self._vars['output'].keys())

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def call(self, *args, **kwargs):
        r"""Call the model as a function by sending variables.

        Args:
           *args: Input variables in the correct order.
           **kwargs: Name input variables.

        Raises:
            IntegrationFunctionError: If there is an error during the
                call.

        Returns:
            dict: Returned values for each return variable.

        """
        self.send(*args, **kwargs)
        return self.recv()

    def send(self, *args, **kwargs):
        r"""Send input to the integration model(s).

        Args:
           *args: Input variables in the correct order.
           **kwargs: Name input variables.

        Raises:
            IntegrationFunctionError: If an input argument is missing.
            IntegrationFunctionError: If sending an input argument to a
                model fails.

        """
        try:
            self.runner.resume()
            data = self._transform_input(args, kwargs)
            # Send
            for k, v in self.inputs.items():
                flag = v['comm'].send(*data[k])
                if not flag:  # pragma: debug
                    raise IntegrationFunctionError(
                        f"Failed to send {k}")
            self.runner.pause()
        except BaseException as e:
            self.info(f"STOPPING DUE TO ERROR DURING SEND: {e}")
            self.stop(error=True)
            raise

    def recv(self, timeout=None, existing_output=None, in_async=False):
        r"""Receive output from the integration model(s).

        Args:
            timeout (float, optional): Time (in seconds) that should be
                waited for the call to finish. A value of None will wait
                indefinitely.
            existing_output (dict, optional): Existing output for each
                integration communicator that new outputs should be
                added to.
            in_async (bool, optional): If True, this method is being
                called from an AsyncFunctionOutput instance.

        Raises:
            IntegrationFunctionError: If receiving an output value from
                a model fails.

        Returns:
            dict: Returned values for each return variable.

        """
        from yggdrasil.communication.CommBase import (
            FLAG_EMPTY, FLAG_SUCCESS)
        out = {}
        if existing_output is not None:
            out = existing_output
        try:
            self.runner.resume()
            Tout = self.start_timeout(t=timeout,
                                      key_suffix='.function_recv')

            def is_complete():
                return (all((k in out) for k in self.outputs)
                        or Tout.is_out)

            while not is_complete():
                for k, v in self.outputs.items():
                    if k in out:
                        continue
                    msg = v['comm'].recv(return_message_object=True,
                                         timeout=0.0,
                                         quiet_timeout=True)
                    if msg.flag == FLAG_EMPTY:
                        continue
                    if msg.flag != FLAG_SUCCESS:  # pragma: debug
                        raise IntegrationFunctionError(
                            f"Failed to receive {k}",
                            partial_output=out)
                    out[k] = msg.args
                if in_async:
                    break
                if not is_complete():
                    self.sleep()
            self.stop_timeout(key_suffix='.function_recv',
                              quiet=True)
            self.runner.pause()
        except BaseException as e:
            self.info(f"STOPPING DUE TO ERROR DURING RECV: {e}")
            self.stop(error=True)
            raise
        if in_async:
            return out
        if not all((k in out) for k in self.outputs):
            raise IntegrationFunctionError(
                "Function receive timed out", partial_output=out)
        return self._transform_output(out)

    def _transform_input(self, args, kwargs):
        out = {}
        for a, arg in zip(self.arguments, args):
            assert a not in kwargs
            kwargs[a] = arg
        for a in self.arguments:
            if a in kwargs:
                continue
            a_dtype = self.argument_datatype('input', a)
            if ((len(args) == 0 and len(self.arguments) == 1
                 and a_dtype.get('type', '') == 'object')):
                a_kws = list(kwargs.keys())
                if not a_dtype.get('additionalProperties', True):
                    a_kws = list(a_dtype.get('properties', {}).keys())
                kwargs[a] = {k: kwargs[k] for k in a_kws}
            else:  # pragma: debug
                # TODO: Get default data from file if available
                raise RuntimeError(f"Required argument \"{a}\" "
                                   f"not provided.")
        for k, v in self.inputs.items():
            out[k] = [kwargs[a] for a in v['var_names']]
        return out

    def _transform_output(self, data):
        out = {}
        vars_out = []
        for k, idata in data.items():
            v = self.outputs[k]
            ivars = v['var_names']
            if ((isinstance(idata, (list, tuple))
                 and (len(ivars) > 1 or len(idata) == len(ivars)))):
                assert len(idata) == len(ivars)
                for a, d in zip(ivars, idata):
                    out[a] = d
            else:
                assert len(ivars) == 1
                out[ivars[0]] = idata
            vars_out += ivars
        if len(vars_out) == 1 and isinstance(out[vars_out[0]], dict):
            out = out[vars_out[0]]
        return out

    def create_runner(self, **kwargs):
        r"""Create a runner."""
        assert self.runner is None
        model_yaml = self.model_yaml
        if self.service_address:
            # Temporary YAML describing the service
            contents = (f'service:\n'
                        f'    name: {model_yaml}\n'
                        f'    address: {self.service_address}\n')
            model_yaml = os.path.join(os.getcwd(),
                                      self.dummy_name + '.yml')
            with open(model_yaml, 'w') as fd:
                fd.write(contents)
        try:
            self.runner = YggRunner(model_yaml, **self.runner_kwargs)
            self.runner.run(**kwargs)
            self.model_driver = self.runner.modeldrivers[self.dummy_name]
            for k in self.runner.modeldrivers.keys():
                if k != self.dummy_name:
                    self.__name__ = k
                    break
            self.debug("run started")
        finally:
            if self.service_address and os.path.isfile(model_yaml):
                os.remove(model_yaml)

    def run(self, **kwargs):
        r"""Run the model"""
        if self.runner is not None:
            self.info("Function runner already exists")
            return
        from yggdrasil.languages.Python.YggInterface import InterfaceComm
        from yggdrasil import tools
        self.create_runner(**kwargs)
        # Create input/output channels
        with tools.updated_environment(self.model_driver['instance'].set_env()):
            for io in ['output', 'input']:
                io_opp = 'output' if io == 'input' else 'input'
                direction = 'send' if io == 'input' else 'recv'
                for drv in self.model_driver[f'{io_opp}_drivers']:
                    channels = drv['instance'].model_comm_kwargs(
                        io, self.dummy_name)
                    assert len(channels) == 1
                    self._opp_comms[io].update(channels)
                    channel_name = list(channels.keys())[0]
                    var_name = channel_name
                    self._comms[io][var_name] = drv.copy()
                    kws = {
                        'direction': direction,
                        'no_suffix': True,
                        # 'context': ctx,
                    }
                    if drv['instance']._connection_type == 'rpc_request':
                        kws['commtype'] = 'client'
                    self._comms[io][var_name]['comm'] = InterfaceComm(
                        channel_name, **kws)
                    if drv['instance']._connection_type == 'rpc_request':
                        self._comms[io_opp][var_name] = drv.copy()
                        self._comms[io_opp][var_name]['comm'] = (
                            self._comms[io][var_name]['comm'])
                        if drv['outputs'][0].get('server_replaces', False):
                            srv = drv['outputs'][0]['server_replaces']
                            self._comms[io][var_name]['vars'] = (
                                srv[io]['vars'])
                            self._comms[io_opp][var_name]['vars'] = (
                                srv[io_opp]['vars'])
                        else:
                            self._comms[io_opp][var_name]['vars'] = (
                                drv[f'{io_opp}'][0].get(
                                    'response_kwargs', {}).get(
                                        'vars', [var_name]))
                    if 'vars' not in self._comms[io][var_name]:
                        self._comms[io][var_name]['vars'] = (
                            drv[f'{io_opp}s'][0].get('vars', [var_name]))
        self.debug(f'inputs: {list(self.inputs.keys())}, '
                   f'outputs: {list(self.outputs.keys())}')
        atexit.register(self.stop)
        # Ensure that vars are strings
        for io in ['input', 'output']:
            for k, v in getattr(self, f'{io}s').items():
                v['var_names'] = []
                v['vars_datatypes'] = {}
                for iv in v['vars']:
                    if isinstance(iv, dict):
                        if iv.get('is_length_var', False):
                            continue
                        if 'datatype' in iv:
                            v['vars_datatypes'][iv['name']] = iv['datatype']
                        iv = iv['name']
                    v['var_names'].append(iv)
                    self._vars[io][iv] = v
        # Get arguments
        self.debug(f"arguments: {self.arguments}, "
                   f"returns: {self.returns}")
        self.runner.pause()

    def reload(self):
        r"""Reload the model"""
        self.stop()
        self.run()

    def stop(self, error=False):
        r"""Stop the model(s) from running.

        Args:
            error (bool, optional): If True, the function is being
                stopped due to an error and the drivers should be
                terminated directly instead of allowing them to exit
                gravefully.

        """
        if self.runner is None:
            self.info("Runner already stopped")
            return
        self.runner.resume()
        if not self._stop_called:
            self._stop_called = True
            if not error:
                for x in self.inputs.values():
                    if 'comm' in x:
                        x['comm'].send_eof()
            if not error:
                self.runner.waitModels()
            for x in self.inputs.values():
                if 'comm' in x:
                    x['comm'].close()
            for x in self.outputs.values():
                if 'comm' in x:
                    x['comm'].close()
            self.runner.terminate()
            self.runner.atexit()
            self.runner = None
            self._stop_called = False

    def printStatus(self, level='info', return_str=False):
        r"""Print the status of the function as a log message.

        Args:
            level (str, optional): Debug level that log message should be
                emitted at.
            return_str (bool, optional): If True, return the message
                string instead of emitting it as a log message.

        """
        info = self.function_info
        t = '   '
        msg = f"Models: {', '.join(info['models'])}\n"
        for io in ['input', 'output']:
            msg += f'{io.title()}s:\n'
            for k, v in info[io].items():
                msg += f"{t}{k}:\n"
                datatype_str = pformat(v['datatype'])
                datatype_lines = datatype_str.splitlines()
                if len(datatype_lines) > 1:
                    datatype_str = (
                        f'\n{3 * t}' + f'\n{3 * t}'.join(datatype_lines)
                    )
                if 'description' in v:
                    msg += f"{2 * t}description: {v['description']}\n"
                msg += (
                    f"{2 * t}models: {', '.join(v['models'])}\n"
                    f"{2 * t}datatype: {datatype_str}\n"
                )
        if return_str:
            return msg
        getattr(self.logger, level)(msg)


class YggAsyncFunctionResult(AsyncResult):
    r"""Result from call to asynchronous integration function.

    Args:
        args (tuple): Arguments provided to call.
        kwargs (dict): Keyword arguments provided to call.
        lock (multitasking.RLock): Lock to use for result.

    """

    def __init__(self, args, kwargs, lock):
        self.args = args
        self.kwargs = kwargs
        self.sent = False
        self.output_keys = None
        self.partial = {}
        super(YggAsyncFunctionResult, self).__init__(lock=lock)


class YggAsyncFunction(YggTaskLoop):
    r"""Version of YggFunction that returns asynchronous results.

    Args:
        *args, **kwargs: All arguments are passed to the YggFunction
            constructor.

    """

    def __init__(self, *args, **kwargs):
        self._function = None
        self._function_args = args
        self._function_kwargs = kwargs
        self._output_keys = None
        self._arguments = None
        self._returns = None
        self._backlog_external = []
        self._backlog_internal = []
        super(YggAsyncFunction, self).__init__()
        self.start()
        self.wait_for_loop()

    def before_loop(self):
        r"""Actions performed before the loop."""
        super(YggAsyncFunction, self).before_loop()
        with self.lock:
            self._function = YggFunction(*self._function_args,
                                         **self._function_kwargs)
            self._output_keys = list(self._function.outputs.keys())
            self._arguments = self._function.arguments
            self._returns = self._function.returns

    def run_loop(self):
        r"""Actions performed on each loop iteration."""
        if not self._function.is_alive():
            raise IntegrationFunctionError("Function is not alive")
        # Move back log into loop
        with self.lock:
            self._backlog_internal += self.backlog_external
            self._backlog_external = []
        # Send unsent messages
        for x in self._backlog_internal:
            with x.lock:
                if not x.sent:
                    self._function.send(*x.args, **x.kwargs)
                    x.sent = True
        # Check for new received messages & update first request
        #   missing each of the recieved values
        out = self._function.recv(in_async=True)
        for k, v in out.items():
            assert k in self._output_keys
            for x in self._backlog_internal:
                if self._update(x, k, v):
                    break
            else:
                raise IntegrationFunctionError(
                    f"Extra input received from \"{k}\": {v}")
        # Remove finalized messages
        self._backlog_internal = [
            x for x in self._backlog_internal if not x.is_complete()
        ]

    def _update(self, x, k, v):
        with x.lock:
            if k in x.partial:
                return False
            x.partial[k] = v
            if all(kk in x.partial for kk in self._output_keys):
                x.set(self._function._transform_output(x.partial))
        return True

    def after_loop(self):
        r"""Actions performed after the loop."""
        super(YggAsyncFunction, self).after_loop()
        with self.lock:
            for x in self._backlog_internal:
                x.set_error("Loop exiting")
            self._function.stop()

    @property
    def function_info(self):
        r"""dict: Information about the function."""
        with self.lock:
            if self._function is None:
                raise IntegrationFunctionError(
                    "Function not yet initialized")
            return self._function.function_info

    @property
    def n8n_form_node(self):
        r"""dict: Parameters describing an n8n tool for this function."""
        with self.lock:
            if self._function is None:
                raise IntegrationFunctionError(
                    "Function not yet initialized")
            return self._function.n8n_form_node

    @property
    def arguments(self):
        r"""list: Names of function arguments."""
        return self._arguments

    @property
    def returns(self):
        r"""list: Name of function output variables."""
        return self._returns

    def __call__(self, *args, **kwargs):
        return self.call(args, kwargs)

    def call(self, *args, **kwargs):
        r"""Call the model as a function by sending variables.

        Args:
           *args: Input variables in the correct order.
           **kwargs: Name input variables.

        Raises:
            IntegrationFunctionError: If there is an error during the
                call.

        Returns:
            dict: Returned values for each return variable.

        """
        out = YggAsyncFunctionResult(args, kwargs,
                                     self.context.RLock())
        with self.lock:
            self._backlog_external.append(out)
        return out

    def printStatus(self, level='info', return_str=False):
        r"""Print the status of the function as a log message.

        Args:
            level (str, optional): Debug level that log message should be
                emitted at.
            return_str (bool, optional): If True, return the message
                string instead of emitting it as a log message.

        """
        with self.lock:
            if self._function is None:
                msg = 'Function not yet constructed'
            else:
                msg = self._function.printStatus(return_str=True)
        if return_str:
            return msg
        getattr(self.logger, level)(msg)

    def reload(self):
        r"""Reload the model"""
        raise IntegrationFunctionError("Cannot reload an asynchronous "
                                       "integration function")


class YggRunner(YggClass):
    r"""This class handles the orchestration of starting the model and
    IO drivers, monitoring their progress, and cleaning up on exit.

    Arguments:
        modelYmls (list): List of paths to yaml files specifying the models
            that should be run.
        namespace (str, optional): Name that should be used to uniquely
            identify any RMQ exchange. Defaults to the value in the config
            file.
        host (str, optional): Name of the host that the models will be
            launched from. Defaults to None.
        rank (int, optional): Rank of this set of models if run in parallel.
            Defaults to 0.
        ygg_debug_level (str, optional): Level for Ygg debug messages.
            Defaults to environment variable 'YGG_DEBUG'.
        rmq_debug_level (str, optional): Level for RabbitMQ debug messages.
            Defaults to environment variable 'RMQ_DEBUG'.
        ygg_debug_prefix (str, optional): Prefix for Ygg debug messages.
            Defaults to namespace.
        as_service (bool, optional): If True, the integration is running as a
            service. If True, complete_partial is set to True. Defaults to
            False.
        complete_partial (bool, optional): If True, unpaired input/output
            channels are allowed and reserved for use (e.g. for calling the
            model as a function). Defaults to False.
        partial_commtype (dict, optional): Communicator kwargs that should be
            be used for the connections to the unpaired channels when
            complete_partial is True. Defaults to None and will be ignored.
        validate (bool, optional): If True, the validation scripts for each
            modle (if present), will be run after the integration finishes
            running. Defaults to False.
        with_debugger (str, optional): Tool (and any flags for the tool)
            that should be used to run models.
        disable_python_c_api (bool, optional): If True, the Python C API will
            be disabled. Defaults to False.
        with_asan (bool, optional): Compile and run all models with the
            address sanitizer. Defaults to False.
        with_omp (bool, optional): Compile all models with OpenMP if
            OpenMP is installed and can be located. Defaults to False.
        overwrite (bool, optional): If True, any existing model products
            (compilation products, wrapper scripts, etc.) are removed prior to
            the run. If False, the products are not removed. Defaults to True.
            Setting this to False can improve the performance, particularly for
            models that take a long time to compile, but this should only be
            done once the model has been fully debugged to ensure that each run
            is tested on a clean copy of the model.
        remove_products (bool, optional): If True, integration products
            will be removed after running the model.
        **kwargs: Additional keyword arguments are passed to parse_yaml.

    Attributes:
        namespace (str): Name that should be used to uniquely identify any
            RMQ exchange.
        host (str): Name of the host that the models will be launched from.
        rank (int): Rank of this set of models if run in parallel.
        modeldrivers (dict): Model drivers associated with this run.
        connectiondrivers (dict): Connection drivers for this run.
        interrupt_time (float): Time of last interrupt signal.
        error_flag (bool): True if one or more models raises an error.

    ..todo:: namespace, host, and rank do not seem strictly necessary.

    """
    def __init__(self, modelYmls, namespace=None, host=None, rank=0,
                 ygg_debug_level=None, rmq_debug_level=None,
                 ygg_debug_prefix=None, connection_task_method='thread',
                 as_service=False, complete_partial=False,
                 partial_commtype=None, production_run=False,
                 mpi_tag_start=None, validate=False,
                 with_debugger=None, disable_python_c_api=False,
                 with_asan=False, with_omp=False, overwrite=False,
                 remove_products=False, name='runner', **kwargs):
        kwargs_models = {'with_debugger': with_debugger,
                         'disable_python_c_api': disable_python_c_api,
                         'with_asan': with_asan,
                         'with_omp': with_omp,
                         'overwrite': overwrite,
                         'remove_products': remove_products}
        self.mpi_comm = None
        MPI = init_mpi()
        if MPI is not None:
            comm = MPI.COMM_WORLD
            if comm.Get_size() > 1:
                self.mpi_comm = comm
                rank = comm.Get_rank()
                name += str(rank)
        super(YggRunner, self).__init__(name)
        if namespace is None:
            namespace = ygg_cfg.get('rmq', 'namespace', False)
        if not namespace:  # pragma: debug
            raise Exception('rmq:namespace not set in config file')
        if as_service and not complete_partial:
            complete_partial = True
        self.namespace = namespace
        self.host = host
        self.rank = rank
        self.connection_task_method = connection_task_method
        self.base_dup = {}
        self.modelcopies = {}
        self.modeldrivers = {}
        self.connectiondrivers = {}
        self.interrupt_time = 0
        self._old_handlers = {}
        self.production_run = production_run
        self.error_flag = False
        self.complete_partial = complete_partial
        self.partial_commtype = partial_commtype
        self.validate = validate
        self.debug("Running in %s with path %s namespace %s rank %d",
                   os.getcwd(), sys.path, namespace, rank)
        # Update environment based on config
        cfg_environment()
        # Parse yamls
        self.mpi_tag_start = mpi_tag_start
        if self.mpi_comm and (self.rank > 0):
            pass
        else:
            self.drivers = yamlfile.parse_yaml(
                modelYmls, complete_partial=complete_partial,
                partial_commtype=partial_commtype, **kwargs)
            self.connectiondrivers = self.drivers['connection']
            self.modeldrivers = self.drivers['model']
            for k, v in kwargs_models.items():
                if not v:
                    continue
                for x in self.modeldrivers.values():
                    x[k] = v
            for x in self.modeldrivers.values():
                if x['driver'] == 'DummyModelDriver':
                    x['runner'] = self
                    if as_service:
                        for io in x['output_drivers']:
                            for comm in io['inputs']:
                                comm['for_service'] = True
                        for io in x['input_drivers']:
                            for comm in io['outputs']:
                                comm['for_service'] = True
            self.broker = YggBroker(self.drivers)

    def pprint(self, *args):
        r"""Print with color."""
        s = ''.join(str(i) for i in args)
        print((COLOR_TRACE + '{}' + COLOR_NORMAL).format(s))

    def atexit(self, *args, **kwargs):
        r"""At exit ensure that the runner has stopped and cleaned up."""
        self.debug('')
        self.reset_signal_handler()
        self.closeChannels()
        self.cleanup()

    def signal_handler(self, sig, frame):
        r"""Terminate all drivers on interrrupt."""
        self.debug("Interrupt with signal %d", sig)
        now = time.perf_counter()
        elapsed = now - self.interrupt_time
        self.debug('Elapsed time since last interrupt: %d s', elapsed)
        self.interrupt_time = now
        self.pprint(' ')
        self.pprint(80 * '*')
        if elapsed < 5:
            self.pprint('* %76s *' % 'Interrupted twice within 5 seconds: shutting down')
            self.pprint(80 * '*')
            self.debug("Terminating models and closing all channels")
            self.terminate()
            self.pprint(80 * '*')
            return 1
        else:
            self.pprint('* %76s *' % 'Interrupted: Displaying channel summary')
            self.pprint('* %76s *' % 'interrupt again (within 5 seconds) to exit')
            self.pprint(80 * '*')
            self.printStatus()
            self.pprint(80 * '*')
        self.debug('%d returns', sig)

    def _swap_handler(self, signum, signal_handler):
        self._old_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, signal_handler)
        if not platform._is_win:
            signal.siginterrupt(signum, False)
        
    def set_signal_handler(self, signal_handler=None):
        r"""Set the signal handler.

        Args:
            signal_handler (function, optional): Function that should handle
                received SIGINT and SIGTERM signals. Defaults to
                self.signal_handler.

        """
        if signal_handler is None:
            signal_handler = self.signal_handler
        if signal_handler:
            self._swap_handler(signal.SIGINT, signal_handler)
            if not platform._is_win:
                self._swap_handler(signal.SIGTERM, signal_handler)
            else:  # pragma: windows
                self._swap_handler(signal.SIGBREAK, signal_handler)

    def reset_signal_handler(self):
        r"""Reset signal handlers to old ones."""
        for k, v in self._old_handlers.items():
            signal.signal(k, v)

    def run(self, signal_handler=None, timer=None, t0=None):
        r"""Run all of the models and wait for them to exit.

        Args:
            signal_handler (function, optional): Function that should be used as
                a signal handler. Defaults to None and is set by
                set_signal_handler.
            timer (function, optional): Function that should be called to get
                intermediate timing statistics. Defaults to time.time if not
                provided.
            t0 (float, optional): Zero point for timing statistics. Is set
                using the provided timer if not provided.

        Returns:
            dict: Intermediate times from the run.

        """
        with temp_config(production_run=self.production_run):
            if timer is None:
                timer = time.time
            if t0 is None:
                t0 = timer()
            times = OrderedDict()
            times['init'] = timer()
            self.loadDrivers()
            times['load drivers'] = timer()
            self.startDrivers()
            self.broker.start()
            times['start drivers'] = timer()
            self.set_signal_handler(signal_handler)
            if not self.complete_partial:
                self.waitModels()
                times['run models'] = timer()
                self.atexit()
                times['at exit'] = timer()
            tprev = t0
            for k, t in times.items():
                self.info('%20s\t%f', k, t - tprev)
                tprev = t
            self.info(40 * '=')
            self.info('%20s\t%f', "Total", tprev - t0)
        if self.error_flag:
            raise IntegrationError("Error running the integration.")
        if self.validate:
            for v in self.modeldrivers.values():
                v['instance'].run_validation()
        return times

    @property
    def all_drivers(self):
        r"""iterator: For all drivers."""
        return chain(self.connectiondrivers.values(),
                     self.modeldrivers.values())

    def io_drivers(self):
        r"""Return the input and output drivers for all models.

        Returns:
            iterator: Access to list of I/O drivers.

        """
        return self.connectiondrivers.values()

    def create_driver(self, yml, **kwargs):
        r"""Create a driver instance from the yaml information.

        Args:
            yml (yaml): Yaml object containing driver information.

        Returns:
            object: An instance of the specified driver.

        """
        self.debug('Creating %s, a %s', yml['name'], yml['driver'])
        curpath = os.getcwd()
        if 'working_dir' in yml:
            os.chdir(yml['working_dir'])
        try:
            if (yml.get('copies', 1) > 1) and ('copy_index' not in yml):
                instance = DuplicatedModelDriver(
                    yml, namespace=self.namespace, rank=self.rank,
                    duplicates=yml.pop('duplicates', None), **kwargs)
            else:
                kwargs = dict(yml, **kwargs)
                instance = create_driver(yml=yml, namespace=self.namespace,
                                         rank=self.rank, **kwargs)
            yml['instance'] = instance
        finally:
            os.chdir(curpath)
        return instance

    def get_models(self, name, rank=None):
        r"""Get the set of drivers referenced by a model name.

        Args:
            name (str, list): Name of model(s).
            rank (int, optional): If provided, only models that will run on
                MPI processes with this rank will be returned. Defaults to
                None and is ignored.

        Returns:
            list: Set of drivers for a model.

        """
        if isinstance(name, list):
            models = []
            for x in name:
                models += self.get_models(x, rank=rank)
        elif name in self.modelcopies:
            models = [self.modeldrivers[cpy] for cpy in self.modelcopies[name]]
        elif name in self.modeldrivers:
            models = [self.modeldrivers[name]]
        else:
            models = [self.modeldrivers[
                DuplicatedModelDriver.get_base_name(name)]]
            assert models[0].get('copies', 0) > 1
        if rank is not None:  # pragma: debug
            # models = [x for x in models if (x['mpi_rank'] == rank)]
            raise NotImplementedError
        return models

    def bridge_mpi_connections(self, yml):
        r"""Bridge connections over MPI processes."""
        from yggdrasil.communication.MPIComm import MPIComm
        io_map = {'inputs': 'outputs', 'outputs': 'inputs'}
        models = {}
        for io in io_map.keys():
            models[io[:-1]] = [x['name'] for x in self.get_models(
                [x.get('partner_model', None) for x in yml[io]
                 if x.get('partner_model', None)])]
        if 'models' not in yml:
            yml['models'] = models
        for io, io_opp in io_map.items():
            for x in yml[io]:
                model = x.get('partner_model', None)
                if not model:
                    continue
                rank_map = {}
                for m in self.get_models(model):
                    rank_map.setdefault(m['mpi_rank'], [])
                    rank_map[m['mpi_rank']].append(m)
                if not any(rank > 0 for rank in rank_map.keys()):
                    continue
                comms = []
                for rank in rank_map.keys():
                    x_copy = dict(copy.deepcopy(x),
                                  partner_copies=len(rank_map[rank]))
                    x_copy.pop('transform', None)
                    x_copy.pop('filter', None)
                    if rank == 0:
                        icomm = x_copy
                    else:
                        icomm = dict(
                            commtype='mpi',
                            daemon=True,
                            ranks=[rank],
                            mpi_index=len(self._mpi_comms),
                            mpi_direction=io_opp,
                            mpi_stride=1,
                            mpi_driver={
                                io_opp: [{'commtype': 'mpi', 'ranks': [0],
                                          'daemon': True}],
                                io: [x_copy],
                                'driver': yml['driver'],
                                'name': f"{x['name']}_mpi{rank}_{io}",
                                'models': {
                                    io_opp[:-1]: models[io_opp[:-1]],
                                    io[:-1]: [m['name'] for m in
                                              rank_map[rank]]}})
                        if yml['driver'].startswith('RPC'):
                            icomm['mpi_stride'] += MPIComm._max_response
                        self._mpi_comms.append(icomm)
                        for m in rank_map[rank]:
                            drv_key = f'mpi_{io_opp[:-1]}_drivers'
                            m.setdefault(drv_key, [])
                            m[drv_key].append(icomm['mpi_driver']['name'])
                    comms.append(icomm)
                if len(comms) == 1:
                    x.update(comms[0])
                    self._mpi_comms[comms[0]['mpi_index']] = x
                else:
                    # TODO: Move to connection level?
                    x.clear()
                    x['commtype'] = comms
                    if yml['driver'].startswith('RPC'):
                        x['pattern'] = 'cycle'

    def create_connection_driver(self, yml):
        r"""Create a connection driver instance from the yaml information.

        Args:
            yml (yaml): Yaml object containing driver information.

        Returns:
            object: An instance of the specified driver.

        """
        # TODO: Verify if this should be overridden
        yml.setdefault('task_method', self.connection_task_method)
        driver0 = yml['driver']
        try:
            yml['driver'] = 'DirectConnectionDriver'
            drv = self.create_driver(yml)
        except DirectConnectionDriver.DirectConnectionError:
            yml['driver'] = driver0
            drv = self.create_driver(yml)
            # Transfer connection addresses to model via env
            # TODO: Change to server that tracks connections
            for model, env in drv.model_env.items():
                env_key = 'env'
                if (((model not in self.modelcopies)
                     and (model not in self.modeldrivers))):
                    env_key = f'env_{model}'
                for x in self.get_models(model):
                    x.setdefault(env_key, {})
                    x[env_key].update(env)
        return drv

    def distribute_mpi(self):
        r"""Distribute models between MPI processes."""
        size = self.mpi_comm.Get_size()
        if self.rank == 0:
            from yggdrasil.communication.MPIComm import MPIComm
            from yggdrasil.drivers.ModelDriver import ModelDriver
            self.expand_duplicates()
            # Set the rank and index for each model
            for i, v in enumerate(self.modeldrivers.values()):
                v['mpi_rank'] = (i + 1) % size
                v['model_index'] = i
                v['mpi_tag_start'] = self.mpi_tag_start
            # Split the connections bridging MPI processes
            self.debug("Splitting connection drivers over MPI")
            self.all_connectiondrivers = self.connectiondrivers
            self._mpi_comms = []
            for driver in self.connectiondrivers.values():
                self.bridge_mpi_connections(driver)
            tag_start = len(ModelDriver._mpi_tags) * len(self.modeldrivers) * 5
            if self.mpi_tag_start is not None:
                tag_start += self.mpi_tag_start
            tag_stride = sum([x.pop('mpi_stride') for x in self._mpi_comms])
            connections = [[] for _ in range(size)]
            for x in self._mpi_comms:
                x['tag_start'] = tag_start + x.pop('mpi_index') * MPIComm._spacer_tags
                x['tag_stride'] = tag_stride
                io = x.pop('mpi_direction')
                drv = x.pop('mpi_driver')
                drv[io][0]['tag_start'] = x['tag_start']
                drv[io][0]['tag_stride'] = x['tag_stride']
                connections[x['ranks'][0]].append((drv['name'], drv))
            max_len = len(max(connections, key=len))
            for x in connections:
                while len(x) < max_len:
                    x.append(None)
            # Sort models
            self.all_modeldrivers = self.modeldrivers
            models = [[] for _ in range(size)]
            for i, (k, v) in enumerate(self.modeldrivers.items()):
                x_cp = copy.deepcopy(v)
                for k2 in ['input_drivers', 'output_drivers', 'mpi_rank']:
                    x_cp.pop(k2, None)
                for k2 in ['input_drivers', 'output_drivers']:
                    x_cp[k2] = x_cp.get(f'mpi_{k2}', [])
                # Skew models away from root process so that
                # connection threading might not share process
                models[v['mpi_rank']].append((k, x_cp))
            max_len = len(max(models, key=len))
            for x in models:
                while len(x) < max_len:
                    x.append(None)
            models = [rapidjson.dumps(x) for x in models]
            connections = [rapidjson.dumps(x) for x in connections]
        else:
            models = None
            connections = None
        self.modeldrivers = rapidjson.loads(
            self.mpi_comm.scatter(models, root=0))
        self.connectiondrivers = rapidjson.loads(
            self.mpi_comm.scatter(connections, root=0))
        self.modeldrivers = dict(
            [x for x in self.modeldrivers if (x is not None)])
        self.connectiondrivers = dict(
            [x for x in self.connectiondrivers if (x is not None)])
        self.modelcopies = self.mpi_comm.bcast(self.modelcopies, root=0)
        self.info(f"Models on MPI process {self.rank}: "
                  f"{list(self.modeldrivers.keys())}")
        # Add dummy drivers on root process to monitor remote ones
        # and re-group copies into duplicate model w/ duplicate models
        # before non-duplicate to allow them to start before starting
        # local models
        if self.rank == 0:
            for i, (k, v) in enumerate(self.all_modeldrivers.items()):
                if k not in self.modeldrivers:
                    v['partner_driver'] = v['driver']
                    v['language'] = 'mpi'
                    v['driver'] = 'MPIPartnerModel'
                self.modeldrivers[k] = v
            self.connectiondrivers = self.all_connectiondrivers
        else:
            for v in self.modeldrivers.values():
                for k in ['input_drivers', 'output_drivers']:
                    v[k] = [self.connectiondrivers[x] for x in v.get(k, [])]
        self.reduce_duplicates()

    def expand_duplicates(self):
        r"""Expand model copies so they can be split across MPI processes."""
        self.debug("Expanding duplicated models")
        remove_dup = []
        add_dup = {}
        for k, v in self.modeldrivers.items():
            if v.get('copies', 1) > 1:
                self.modelcopies[v['name']] = []
                for x in DuplicatedModelDriver.get_yaml_copies(v):
                    add_dup[x['name']] = x
                    self.modelcopies[v['name']].append(x['name'])
                remove_dup.append(k)
        for k in remove_dup:
            self.base_dup[k] = self.modeldrivers.pop(k)
        self.modeldrivers.update(add_dup)

    def reduce_duplicates(self):
        r"""Join model duplicates after they were split between processes."""
        self.debug("Reducing duplicated models")
        for k in list(self.modelcopies.keys()):
            duplicates = [self.modeldrivers.pop(cpy)
                          for cpy in self.modelcopies.pop(k)
                          if cpy in self.modeldrivers]
            if duplicates:
                if k in self.base_dup:
                    base = self.base_dup[k]
                else:
                    base = dict(copy.deepcopy(duplicates[0]), name=k,
                                input_drivers=duplicates[0].get(
                                    'input_drivers', []),
                                output_drivers=duplicates[0].get(
                                    'output_drivers', []))
                    base.pop('copy_index', None)
                for x in duplicates:
                    for k2 in ['input_drivers', 'output_drivers']:
                        x[k2] = base.get(k2, [])
                base['duplicates'] = duplicates
                self.modeldrivers[k] = base
        
    def loadDrivers(self):
        r"""Load all of the necessary drivers, doing the IO drivers first
        and adding IO driver environmental variables back tot he models."""
        self.debug('')
        driver = dict(name='name')
        try:
            # Preparse model drivers first so that the input/output
            # channels are updated for wrapped functions
            self.debug("Preparsing model functions")
            for driver in self.modeldrivers.values():
                driver_cls = import_component('model', driver['driver'],
                                              without_schema=True)
                driver_cls.preparse_function(driver)
            if self.mpi_comm:
                self.distribute_mpi()
            # Create I/O drivers
            self.debug("Loading connection drivers")
            for driver in self.connectiondrivers.values():
                self.create_connection_driver(driver)
            # Create model drivers
            self.debug("Loading model drivers")
            for driver in self.modeldrivers.values():
                self.create_driver(driver)
                self.debug("Model %s:, env: %s",
                           driver['name'], pformat(driver['instance'].env))
        except BaseException as e:  # pragma: debug
            self.error("%s could not be created: %s", driver['name'], e)
            self.terminate()
            raise

    def start_server(self, name):
        r"""Start a server driver."""
        if self.mpi_comm and (self.rank != 0):
            return
        # This is required if modelcopies are not joined before drivers
        # are started
        # if name in self.modelcopies:
        #     assert name not in self.modeldrivers
        #     for cpy in self.modelcopies[name]:
        #         self.start_server(cpy)
        #     return
        x = self.modeldrivers[name]['instance']
        if not x.was_started:
            self.debug("Starting server '%s' before client", x.name)
            x.start()

    def stop_server(self, name):
        r"""Stop a server driver."""
        # This is required if modelcopies are not joined before drivers
        # are started
        # if name in self.modelcopies:
        #     assert name not in self.modeldrivers
        #     for cpy in self.modelcopies[name]:
        #         self.stop_server(cpy)
        #     return
        x = self.modeldrivers[name]['instance']
        x.stop()

    def stop_dummy_models(self):
        r"""Stop all dummy models that are running."""
        for x in self.modeldrivers.values():
            if x['instance'].language == 'dummy':
                x['instance'].set_break_flag()

    def startDrivers(self):
        r"""Start drivers, starting with the IO drivers."""
        if not self.mpi_comm or (self.rank == 0):
            assert not self.modelcopies
        self.info('Starting I/O drivers and models on system '
                  + '{} in namespace {} with rank {}'.format(
                      self.host, self.namespace, self.rank))
        driver = dict(name='name')
        try:
            # Start connections
            for driver in self.io_drivers():
                self.debug("Starting driver %s", driver['name'])
                d = driver['instance']
                if not d.was_started:
                    d.start()
            # Ensure connections in loop
            for driver in self.io_drivers():
                self.debug("Checking driver %s", driver['name'])
                d = driver['instance']
                d.wait_for_loop()
                assert d.was_loop
                assert not d.errors
            # Start models
            for driver in self.modeldrivers.values():
                self.debug("Starting driver %s", driver['name'])
                d = driver['instance']
                for n2 in driver.get('client_of', []):
                    self.start_server(n2)
                if not d.was_started:
                    d.start()
        except BaseException as e:  # pragma: debug
            self.error("%s did not start: %s(%s)", driver['name'], type(e), e)
            self.terminate()
            raise
        if self.mpi_comm:
            self.mpi_comm.barrier()
        self.debug('ALL DRIVERS STARTED')

    @property
    def is_alive(self):
        r"""bool: True if all of the models are still running, False
        otherwise."""
        for drv in self.modeldrivers.values():
            if (not drv['instance'].is_alive()) or drv['instance'].errors:
                return False
        return True

    def waitModels(self, timeout=False):
        r"""Wait for all model drivers to finish. When a model finishes,
        join the thread and perform exits for associated IO drivers."""
        self.debug('')
        running = [d for d in self.modeldrivers.values()]
        dead = []
        Tout = self.start_timeout(t=timeout,
                                  key_suffix='.waitModels')
        while ((len(running) > 0) and (not self.error_flag)
               and (not Tout.is_out)):
            if not self.broker.is_alive():
                if self.broker.errors:
                    self.error('Error on broker')
                    self.error_flag = True
                break
            for drv in running:
                d = drv['instance']
                if d.errors:  # pragma: debug
                    self.error('Error in model %s', drv['name'])
                    self.error_flag = True
                    break
                elif d.io_errors:  # pragma: debug
                    self.error('Error in input/output driver for model %s'
                               % drv['name'])
                    self.error_flag = True
                    break
                elif d.disabled:
                    d.terminate()
                d.join(1)
                if not d.is_alive():
                    if not d.errors:
                        self.info("%s finished running.", drv['name'])
                        # self.do_model_exits(drv)
                        # self.debug("%s completed model exits.", drv['name'])
                        self.do_client_exits(drv)
                        self.debug("%s completed client exits.", drv['name'])
                        running.remove(drv)
                        self.info("%s finished exiting.", drv['name'])
                else:
                    self.debug('%s still running', drv['name'])
            dead = []
            for drv in self.all_drivers:
                d = drv['instance']
                d.join(0.1)
                if not d.is_alive():
                    dead.append(drv['name'])
        self.stop_timeout(key_suffix='.waitModels')
        for d in self.modeldrivers.values():
            if d['instance'].errors:
                self.error_flag = True
        if not self.error_flag:
            self.info('All models completed')
            self.broker.stop()
        else:
            self.error('One or more models generated errors.')
            self.printStatus()
            self.terminate()
        if self.mpi_comm:
            MPI = init_mpi()
            allcode = self.mpi_comm.allreduce(self.error_flag, op=MPI.SUM)
            if not self.error_flag:
                self.error_flag = allcode
        self.debug('Returning')

    # def do_model_exits(self, model):
    #     r"""Perform exits for IO drivers associated with a model.

    #     Args:
    #         model (dict): Dictionary of model parameters including any
    #             associated IO drivers.

    #     """
    #     for drv in model['input_drivers']:
    #         #  if model['name'] in drv['models']:
    #         #     drv['models'].remove(model['name'])
    #         if not drv['instance'].is_alive():
    #             continue
    #         # if (len(drv['models']) == 0):
    #         self.debug('on_model_exit %s', drv['name'])
    #         drv['instance'].on_model_exit('output', model['name'])
    #     for drv in model['output_drivers']:
    #         # if model['name'] in drv['models']:
    #         #     drv['models'].remove(model['name'])
    #         if not drv['instance'].is_alive():
    #             continue
    #         # if (len(drv['models']) == 0):
    #         self.debug('on_model_exit %s', drv['name'])
    #         drv['instance'].on_model_exit('input', model['name'])
    
    def do_client_exits(self, model):
        r"""Perform exits for IO drivers associated with a client model.

        Args:
            model (dict): Dictionary of model parameters including any
                associated IO drivers.

        """
        if self.mpi_comm and (self.rank != 0):
            return
        # TODO: Exit upstream models that no longer have any open
        # output, connections when a connection is closed.
        for srv_name in model.get('client_of', []):
            iod = self.connectiondrivers[srv_name]
            iod['instance'].remove_model('input', model['name'])
            if iod['instance'].nclients == 0:
                self.stop_server(srv_name)

    def pause(self):
        r"""Pause all drivers."""
        self.debug('')
        self.broker.pause()
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].pause()

    def resume(self):
        r"""Resume all paused drivers."""
        self.debug('')
        self.broker.resume()
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].resume()

    def terminate(self):
        r"""Immediately stop all drivers, beginning with IO drivers."""
        self.debug('')
        self.resume()
        for driver in self.all_drivers:
            if 'instance' in driver:
                self.debug('Stop %s', driver['name'])
                driver['instance'].terminate()
                # Terminate should ensure instance not alive
                assert not driver['instance'].is_alive()
        self.broker.terminate()
        self.debug('Returning')

    def cleanup(self):
        r"""Perform cleanup operations for all drivers."""
        self.debug('')
        self.broker.cleanup()
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].cleanup()
        # self.inputdrivers = {}
        # self.outputdrivers = {}
        # self.modeldrivers = {}

    def printStatus(self, return_str=False):
        r"""Print the status of all drivers, starting with the IO drivers.

        Args:
            return_str (bool, optional): If True, return the message
                string instead of emitting it as a log message.

        """
        self.debug('')
        out = []
        for driver in self.all_drivers:
            if 'instance' in driver:
                out.append(
                    driver['instance'].printStatus(return_str=return_str))
        if return_str:
            return '\n'.join(out)

    def closeChannels(self, force_stop=False):
        r"""Stop IO drivers and join the threads.

        Args:
            force_stop (bool, optional): If True, the terminate method is
                used to stop the drivers. Otherwise, the stop method is used.
                The stop method will try to exit gracefully while terminate
                will exit as quickly as possible. Defaults to False.

        """
        self.debug('')
        drivers = [i for i in self.io_drivers()]
        for drv in drivers:
            if 'instance' in drv:
                driver = drv['instance']
                if driver.is_alive():  # pragma: debug
                    self.debug("Stopping %s", drv['name'])
                    if force_stop or self.error_flag:
                        driver.terminate()
                    else:
                        driver.stop()
                    self.debug("Stop(%s) returns", drv['name'])
        self.debug('Channel Stops DONE')
        for drv in drivers:
            if 'instance' in drv:
                driver = drv['instance']
                assert not driver.is_alive()
        self.debug('Returning')

        
def get_runner(models, **kwargs):
    r"""Get runner for a set of models, getting run information from the
    environment.

    Args:
        models (list): List of yaml files containing information on the models
            that should be run.
        **kwargs: Additonal keyword arguments are passed to YggRunner.

    Returns:
        YggRunner: Runner for the provided models.

    Raises:
        Exception: If config option 'namespace' in 'rmq' section not set.

    """
    # Get environment variables
    rank = os.environ.get('PARALLEL_SEQ', '0')
    host = socket.gethostname()
    os.environ['YGG_RANK'] = rank
    os.environ['YGG_HOST'] = host
    rank = int(rank)
    kwargs.update(rank=rank, host=host)
    # Run
    yggRunner = YggRunner(models, **kwargs)
    return yggRunner


def run(*args, **kwargs):
    run_kwargs = kwargs.pop('run_kwargs', {})
    yggRunner = get_runner(*args, **kwargs)
    yggRunner.run(**run_kwargs)
    yggRunner.debug("runner returns, exiting")
