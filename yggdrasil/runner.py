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
from yggdrasil import platform, yamlfile
from yggdrasil.drivers import create_driver
from yggdrasil.components import import_component
from yggdrasil.multitasking import MPI
from yggdrasil.drivers.DuplicatedModelDriver import DuplicatedModelDriver
from yggdrasil.drivers.ModelDriver import ModelDriver


COLOR_TRACE = '\033[30;43;22m'
COLOR_NORMAL = '\033[0m'


class IntegrationError(BaseException):
    r"""Error raised when there is an error in an integration."""
    pass


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
        **kwargs: Additional keyword arguments are passed to the YggRunner
            constructor.

    Attributes:
        outputs (dict): Input channels providing access to model output.
        inputs (dict): Output channels providing access to model input.
        runner (YggRunner): Runner for model.

    """
    
    def __init__(self, model_yaml, service_address=None, **kwargs):
        import uuid
        from yggdrasil.languages.Python.YggInterface import (
            YggInput, YggOutput, YggRpcClient)
        super(YggFunction, self).__init__()
        # Create and start runner in another process
        self.dummy_name = 'func' + str(uuid.uuid4()).split('-')[0]
        kwargs['complete_partial'] = self.dummy_name
        if service_address:
            # Temporary YAML describing the service
            contents = (f'service:\n'
                        f'    name: {model_yaml}\n'
                        f'    address: {service_address}\n')
            model_yaml = os.path.join(os.getcwd(), self.dummy_name + '.yml')
            with open(model_yaml, 'w') as fd:
                fd.write(contents)
        self.runner = YggRunner(model_yaml, **kwargs)
        # Start the drivers
        self.runner.run()
        self.model_driver = self.runner.modeldrivers[self.dummy_name]
        for k in self.runner.modeldrivers.keys():
            if k != self.dummy_name:
                self.__name__ = k
                break
        self.debug("run started")
        # Create input/output channels
        self.inputs = {}
        self.outputs = {}
        # import zmq; ctx = zmq.Context()
        self.old_environ = os.environ.copy()
        for drv in self.model_driver['input_drivers']:
            for env in drv['instance'].model_env.values():
                os.environ.update(env)
            channel_name = drv['instance'].ocomm.name
            var_name = drv['name'].split('function_')[-1]
            self.outputs[var_name] = drv.copy()
            self.outputs[var_name]['comm'] = YggInput(
                channel_name, no_suffix=True)  # context=ctx)
            if 'vars' in drv['inputs'][0]:
                self.outputs[var_name]['vars'] = drv['inputs'][0]['vars']
            else:
                self.outputs[var_name]['vars'] = [var_name]
        for drv in self.model_driver['output_drivers']:
            for env in drv['instance'].model_env.values():
                os.environ.update(env)
            channel_name = drv['instance'].icomm.name
            var_name = drv['name'].split('function_')[-1]
            self.inputs[var_name] = drv.copy()
            if drv['instance']._connection_type == 'rpc_request':
                self.inputs[var_name]['comm'] = YggRpcClient(
                    channel_name, no_suffix=True)
                self.outputs[var_name] = drv.copy()
                self.outputs[var_name]['comm'] = self.inputs[var_name]['comm']
                if drv['outputs'][0].get('server_replaces', False):
                    srv = drv['outputs'][0]['server_replaces']
                    self.inputs[var_name]['vars'] = srv['input']['vars']
                    self.outputs[var_name]['vars'] = srv['output']['vars']
            else:
                self.inputs[var_name]['comm'] = YggOutput(
                    channel_name, no_suffix=True)  # context=ctx)
                if 'vars' in drv['outputs'][0]:
                    self.inputs[var_name]['vars'] = drv['outputs'][0]['vars']
                else:
                    self.inputs[var_name]['vars'] = [var_name]
        self.debug('inputs: %s, outputs: %s',
                   list(self.inputs.keys()),
                   list(self.outputs.keys()))
        self._stop_called = False
        atexit.register(self.stop)
        # Ensure that vars are strings
        for k, v in chain(self.inputs.items(), self.outputs.items()):
            v_vars = []
            for iv in v['vars']:
                if isinstance(iv, dict):
                    if not iv.get('is_length_var', False):
                        v_vars.append(iv['name'])
                else:
                    v_vars.append(iv)
            v['vars'] = v_vars
        # Get arguments
        self.arguments = []
        for k, v in self.inputs.items():
            self.arguments += v['vars']
        self.returns = []
        for k, v in self.outputs.items():
            self.returns += v['vars']
        self.debug("arguments: %s, returns: %s", self.arguments, self.returns)
        self.runner.pause()
        if service_address:
            os.remove(model_yaml)

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
        
    def __call__(self, *args, **kwargs):
        r"""Call the model as a function by sending variables.

        Args:
           *args: Any positional arguments are expected to be input variables
               in the correct order.
           **kwargs: Any keyword arguments are expected to be named input
               variables for the model.

        Raises:
            RuntimeError: If an input argument is missing.
            RuntimeError: If sending an input argument to a model fails.
            RuntimeError: If receiving an output value from a model fails.

        Returns:
            dict: Returned values for each return variable.

        """
        self.runner.resume()
        # Check for arguments
        for a, arg in zip(self.arguments, args):
            assert(a not in kwargs)
            kwargs[a] = arg
        for a in self.arguments:
            if a not in kwargs:  # pragma: debug
                raise RuntimeError("Required argument %s not provided." % a)
        # Send
        for k, v in self.inputs.items():
            flag = v['comm'].send([kwargs[a] for a in v['vars']])
            if not flag:  # pragma: debug
                raise RuntimeError("Failed to send %s" % k)
        # Receive
        out = {}
        for k, v in self.outputs.items():
            flag, data = v['comm'].recv(timeout=60.0)
            if not flag:  # pragma: debug
                raise RuntimeError("Failed to receive variable %s" % v)
            ivars = v['vars']
            if isinstance(data, (list, tuple)):
                assert(len(data) == len(ivars))
                for a, d in zip(ivars, data):
                    out[a] = d
            else:
                assert(len(ivars) == 1)
                out[ivars[0]] = data
        self.runner.pause()
        return out

    def stop(self):
        r"""Stop the model(s) from running."""
        self.runner.resume()
        if self._stop_called:
            return
        self._stop_called = True
        for x in self.inputs.values():
            x['comm'].send_eof()
        self.model_driver['instance'].set_break_flag()
        self.runner.waitModels(timeout=10)
        for x in self.inputs.values():
            x['comm'].close()
        for x in self.outputs.values():
            x['comm'].close()
        self.runner.terminate()
        self.runner.atexit()
        os.environ.clear()
        os.environ.update(self.old_environ)

    def model_info(self):
        r"""Display information about the wrapped model(s)."""
        print("Models: %s\nInputs:\n%s\nOutputs:\n%s\n"
              % (', '.join([x['name'] for x in
                            self.runner.modeldrivers.values()
                            if x['name'] != self.dummy_name]),
                 '\n'.join(['\t%s (vars=%s)' % (k, v['vars'])
                            for k, v in self.inputs.items()]),
                 '\n'.join(['\t%s (vars=%s)' % (k, v['vars'])
                            for k, v in self.outputs.items()])))


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
        yaml_param (dict, optional): Parameters that should be used in
            mustache formatting of YAML files. Defaults to None and is
            ignored.
        validate (bool, optional): If True, the validation scripts for each
            modle (if present), will be run after the integration finishes
            running. Defaults to False.

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
                 mpi_tag_start=None, yaml_param=None, validate=False):
        self.mpi_comm = None
        name = 'runner'
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
        if as_service:
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
                partial_commtype=partial_commtype, yaml_param=yaml_param)
            self.connectiondrivers = self.drivers['connection']
            self.modeldrivers = self.drivers['model']
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
            assert(models[0].get('copies', 0) > 1)
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
                if 'models' not in yml:
                    yml['models'] = models
                comms = []
                for rank in rank_map.keys():
                    x_copy = dict(copy.deepcopy(x),
                                  partner_copies=len(rank_map[rank]))
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
                                'name': (
                                    '%s_mpi%s_%s' % (yml['name'], rank, io)),
                                'models': {
                                    io_opp[:-1]: models[io_opp[:-1]],
                                    io[:-1]: [m['name'] for m in
                                              rank_map[rank]]}})
                        if yml['driver'].startswith('RPC'):
                            icomm['mpi_stride'] += MPIComm._max_response
                        self._mpi_comms.append(icomm)
                        for m in rank_map[rank]:
                            drv_key = 'mpi_%s_drivers' % io_opp[:-1]
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
        yml['task_method'] = self.connection_task_method
        drv = self.create_driver(yml)
        # Transfer connection addresses to model via env
        # TODO: Change to server that tracks connections
        for model, env in drv.model_env.items():
            env_key = 'env'
            if (model not in self.modelcopies) and (model not in self.modeldrivers):
                env_key = 'env_%s' % model
            for x in self.get_models(model):
                x.setdefault(env_key, {})
                x[env_key].update(env)
        return drv

    def distribute_mpi(self):
        r"""Distribute models between MPI processes."""
        size = self.mpi_comm.Get_size()
        if self.rank == 0:
            from yggdrasil.communication.MPIComm import MPIComm
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
                    x_cp[k2] = x_cp.get('mpi_%s' % k2, [])
                # Skew models away from root process so that
                # connection threading might not share process
                models[v['mpi_rank']].append((k, x_cp))
            max_len = len(max(models, key=len))
            for x in models:
                while len(x) < max_len:
                    x.append(None)
        else:
            models = None
            connections = None
        self.modeldrivers = dict(
            [x for x in self.mpi_comm.scatter(models, root=0)
             if (x is not None)])
        self.connectiondrivers = dict(
            [x for x in self.mpi_comm.scatter(connections, root=0)
             if (x is not None)])
        self.modelcopies = self.mpi_comm.bcast(self.modelcopies, root=0)
        self.info("Models on MPI process %d: %s", self.rank,
                  list(self.modeldrivers.keys()))
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
                driver['task_method'] = self.connection_task_method
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
        #     assert(name not in self.modeldrivers)
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
        #     assert(name not in self.modeldrivers)
        #     for cpy in self.modelcopies[name]:
        #         self.stop_server(cpy)
        #     return
        x = self.modeldrivers[name]['instance']
        x.stop()

    def startDrivers(self):
        r"""Start drivers, starting with the IO drivers."""
        if not self.mpi_comm or (self.rank == 0):
            assert(not self.modelcopies)
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
                assert(d.was_loop)
                assert(not d.errors)
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
        else:
            self.error('One or more models generated errors.')
            self.printStatus()
            self.terminate()
        if self.mpi_comm:
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
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].pause()

    def resume(self):
        r"""Resume all paused drivers."""
        self.debug('')
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
                assert(not driver['instance'].is_alive())
        self.debug('Returning')

    def cleanup(self):
        r"""Perform cleanup operations for all drivers."""
        self.debug('')
        for driver in self.all_drivers:
            if 'instance' in driver:
                driver['instance'].cleanup()
        # self.inputdrivers = {}
        # self.outputdrivers = {}
        # self.modeldrivers = {}

    def printStatus(self, return_str=False):
        r"""Print the status of all drivers, starting with the IO drivers."""
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
                assert(not driver.is_alive())
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
    yggRunner = get_runner(*args, **kwargs)
    yggRunner.run()
    yggRunner.debug("runner returns, exiting")
