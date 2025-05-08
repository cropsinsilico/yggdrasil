# TODO: Handle MPI
# TODO: Handle driver management
import os
import copy
import pprint
import atexit
import traceback
import itertools
from yggdrasil import multitasking
from yggdrasil.communication import CommBase, new_comm, get_comm
from yggdrasil.drivers import create_driver, DirectConnectionDriver
from yggdrasil.components import create_component


class BrokerError(RuntimeError):
    r"""Errors during interaction with the broker."""
    pass


class DelayedRequestError(BrokerError):
    r"""Error when request should be delayed."""
    pass


class YggBroker(multitasking.YggTaskLoop):
    r"""Broker for tracking models and connections in an integration.

    Args:
       yaml (dict): Parsed yaml specification for an integration.

    """

    _clients = {}
    _global_scope_comms = {}
    _server_address_env = 'YGG_BROKER_SERVER_ADDRESS'

    def __init__(self, yaml=None):
        if yaml is None:
            yaml = {}
        self.yaml = yaml
        self.server_comm = new_comm(
            'YggBroker', commtype='server', use_async=False,
            direct_connection=True, datatype={'type': 'object'},
            allow_multiple_comms=True, no_suffix=True,
            create_proxy=True, no_request_reply=True,
        )
        self._delayed_requests = []
        self._current_request = None
        self._comms = None
        self._connections = {}
        self._models = {}
        # TODO: Once broker handles model driver creation & managment
        #   in place of the runner, this won't be necessary
        # assert self._server_address_env not in os.environ
        os.environ[self._server_address_env] = self.address
        super(YggBroker, self).__init__('YggBroker')

    def __del__(self):
        os.environ.pop(self._server_address_env, None)

    @property
    def address(self):
        r"""str: Broker address."""
        return self.server_comm.opp_address

    @property
    def models(self):
        r"""iterator: Model drivers."""
        with self.lock:
            for v in self._models.values():
                if not v.disabled:
                    yield v

    @property
    def connections(self):
        r"""iterator: Connection drivers."""
        with self.lock:
            for v in self._connections.values():
                if (not v.disabled) or v._connection_type == 'direct':
                    yield v

    @property
    def drivers(self):
        r"""iterator: All drivers."""
        return itertools.chain(self.models, self.connections)

    @classmethod
    def _param_model_comm(cls, comm):
        commlist = None
        if isinstance(comm, dict):
            name = comm['name']
            direction = comm['direction']
            model = comm['model']
            if name.startswith(f'{model}:'):
                name = name.split(f'{model}:', 1)[-1]
            if isinstance(comm['commtype'], list):
                commlist = comm['commtype']
        else:
            name = comm.name_base
            direction = comm.opp_direction
            model = comm.partner_model
            if comm._commtype == 'fork':
                commlist = comm.comm_list
            elif comm._commtype == 'server' and direction == 'send':
                commlist = [comm.icomm]
            elif comm._commtype == 'client' and direction == 'recv':
                commlist = [comm.ocomm]
        return (model, direction, name, commlist)

    @classmethod
    def _check_model_comm(cls, comm, model, direction, name):
        param = cls._param_model_comm(comm)
        if (model, direction, name) == param[:-1]:
            return comm
        commlist = param[-1]
        if commlist:
            for x in commlist:
                try:
                    return cls._check_model_comm(x, model, direction, name)
                except CommBase.CommError:
                    pass
        raise CommBase.CommError("no match")

    def find_model_comm(self, model, direction, name):
        r"""Locate a matching communicator from the registered
        connections.

        Args:
            model (str): Name of the model to find the partner comm for.
            direction (str): Direction that the model communicator
                operates in.
            name (str): Channel name for the communicator.

        Returns:
            dict, CommBase: Partner communicator or parameters for the
                model communicator (in the case of a direct connection).

        Raises:
            BrokerError: If a matching communicator cannot be located.

        """
        if name.startswith(f"{model}:"):
            name = name.split(f"{model}:", 1)[-1]
        for x in self.connections:
            for io in ['input', 'output']:
                if model not in x.models[io]:
                    continue
                comm = getattr(x, f"{io[0]}comm")
                try:
                    return self._check_model_comm(
                        comm, model, direction, name)
                except CommBase.CommError:
                    pass
        raise BrokerError(f"Could not locate a {direction} communicator "
                          f"with name \"{name}\" for model \"{model}\": "
                          f"{pprint.pformat(self.comms)}")

    @classmethod
    def _add_model_comms(cls, comm, out=None, return_comms=False):
        model, direction, name, commlist = cls._param_model_comm(comm)
        if model:
            if return_comms:
                out.setdefault(model, {'send': {}, 'recv': {}})
            else:
                out.setdefault(model, {'send': [], 'recv': []})
            assert name not in out[model][direction]
            if return_comms:
                out[model][direction][name] = comm
            else:
                out[model][direction].append(name)
        elif commlist:
            for x in commlist:
                out = cls._add_model_comms(x, out=out,
                                           return_comms=return_comms)
        return out

    @property
    def comms(self):
        r"""dict: Model touching communicators in the integration."""
        out = {}
        for x in self.connections:
            out = self._add_model_comms(x.icomm, out=out)
            out = self._add_model_comms(x.ocomm, out=out)
        return out

    @property
    def models_alive(self):
        r"""bool: True if any models are alive."""
        for x in self.models:
            if not x.was_started:
                return True
            if x.is_alive():
                return True
        return False

    def start(self):
        r"""Start the loop thread."""
        if self.was_started:
            return
        with self.lock:
            for k, v in self.yaml.get('model', {}).items():
                if 'instance' in v:
                    self._models[k] = v['instance']
            for k, v in self.yaml.get('connection', {}).items():
                if 'instance' in v:
                    self._connections[k] = v['instance']
            atexit.register(self.terminate)
        super(YggBroker, self).start()

    def before_loop(self):
        r"""Actions performed before the loop."""
        super(YggBroker, self).before_loop()

    def run_loop(self):
        r"""Process requests."""
        for x in self.models:
            if x.errors or x.io_errors:
                raise BrokerError("Error on one or more models")
        # if not self.models_alive:
        #     raise multitasking.BreakLoopException(
        #         "Models no longer running")
        msg = self.server_comm.recv(
            timeout=0.1, return_message_object=True,
            quiet_timeout=True)
        if msg.flag in [CommBase.FLAG_EOF, CommBase.FLAG_EMPTY]:
            return
        elif msg.flag != CommBase.FLAG_SUCCESS:
            raise BrokerError(f"Error receiving inside loop: "
                              f"{CommBase.FLAG_TO_STRING[msg.flag]}")
        if self._delayed_requests:
            self.complete_request(self._delayed_requests.pop(0))
        self.complete_request(msg.args)

    def run_finally(self):
        r"""Cleanup."""
        self.server_comm.close()
        self.server_comm = None
        super(YggBroker, self).run_finally()
        with self.lock:
            for x in itertools.chain(self._models.values(),
                                     self._connections.values()):
                if x.disabled:
                    x.terminate()
        for x in self.models:
            if x.language == 'dummy' and x.is_alive():
                x.terminate()
        # Terminate drivers?
        os.environ.pop(self._server_address_env, None)

    def complete_request(self, request):
        r"""Complete a request by processing it and either delaying it
        or returning a response.

        Args:
            request (dict): Client request.

        """
        error = None
        try:
            response = self.process_request(request)
        except DelayedRequestError:
            self._delayed_requests.append(request)
            return
        except BaseException as e:
            error = e
            tb = traceback.format_exc()
            response = {'error': str(e), 'traceback': tb}
        flag = self.server_comm.send(response)
        if error:
            raise error
        if not flag:
            raise BrokerError(f"Error sending response to request "
                              f"{request}")

    def process_request(self, request):
        r"""Process a request.

        Args:
            request (dict): Client request.

        Returns:
            dict: Response.

        """
        try:
            self._current_request = request
            action = request['action']
            if not hasattr(self, f"{action}"):
                raise BrokerError(
                    f"Unsupported action \"{action}\" in "
                    f"request {request}")
            return {'return': getattr(self, f"{action}")(
                *request['args'], **request['kwargs'], self=self)}
        finally:
            self._current_request = None

    # Server API
    def _create_driver(self, component, yml):
        kwargs = dict(
            yml, yml=yml,
            # namespace=self.namespace,
            # rank=self.rank,
        )
        if 'driver' in kwargs:
            drv = create_driver(**kwargs)
        else:
            drv = create_component(component, **kwargs)
        if self.was_started:
            drv.start()
        return drv
    
    def add_model(self, yml):
        r"""Add a model driver to the integration.

        Args:
            yml (dict): Specification describing the model.

        Returns:
            ModelDriver: Model instance.

        """
        yml.setdefault('env', {})
        yml['env'][self._server_address_env] = self.address
        drv = self._create_driver('model', yml)
        with self.lock:
            assert drv.name not in self._models
            self._models[drv.name] = drv
        return drv
        
    def add_connection(self, yml):
        r"""Add a connection driver to the integration.

        Args:
            yml (dict): Specification describing the connection.

        Returns:
            ConnectionDriver: Connection instance.

        """
        try:
            yml_direct = copy.deepcopy(yml)
            yml_direct.update(
                driver='DirectConnectionDriver',
                connection_type='direct',
            )
            drv = self._create_driver('connection', yml_direct)
        except DirectConnectionDriver.DirectConnectionError:
            drv = self._create_driver('connection', yml)
        with self.lock:
            assert drv.name not in self._connections
            self._connections[drv.name] = drv
            if drv.was_started:
                drv.wait_for_loop()
        return drv

    def remove_model(self, name):
        r"""Stop a model driver and remove it from the registry.

        Args:
            name (str): Name of the model driver to remove.

        """
        with self.lock:
            drv = self._models.pop(name)
            drv.terminate()
            drv.cleanup()
            drv.disconnect()
            remove_response = []
            if self.server_comm:
                for k, ocomm in self.server_comm.ocomm.items():
                    if name == ocomm.client_model:
                        remove_response.append(k)
                for k in remove_response:
                    ocomm = self.server_comm.ocomm.pop(k)
                    ocomm.close()

    def remove_connection(self, name):
        r"""Stop a connection driver and remove it from the registry.

        Args:
            name (str): Name of the connection driver to remove.

        """
        with self.lock:
            drv = self._connections.pop(name)
            drv.terminate()
            drv.cleanup()
            drv.disconnect()

    # Client API
    @classmethod
    def get_env(cls, keys):
        r"""Get a set of environment variables.

        Args:
            keys (str, list): Set of required environment variables.

        Returns:
            dict: Environment variables.

        Raises:
            BrokerError: If any of the variables are missing.

        """
        try:
            if isinstance(keys, str):
                return os.environ[keys]
            return {k: os.environ[k] for k in keys}
        except KeyError:
            missing = []
            if isinstance(keys, str):
                missing.append(keys)
            else:
                for k in keys:
                    if k not in os.environ:
                        missing.append(k)
            raise BrokerError(f"Missing broker environment "
                              f"variables {missing}")
        
    @classmethod
    def get_client(cls, model=None):
        r"""Get the broker client for a model, creating it if it does
        not exist.

        Args:
            model (str, optional): Model to get the client for. If not
                provided, the model identified by the YGG_MODEL_NAME
                environment variable will be used.

        Returns:
            ClientComm: Broker client communicator.

        """
        if model is None:
            model = cls.get_env('YGG_MODEL_NAME')
        if model not in cls._clients:
            server_address = cls.get_env(cls._server_address_env)
            cls._clients[model] = get_comm(
                f"YggBroker-{model}", commtype='client',
                address=server_address,
                use_async=False, direct_connection=True,
                create_proxy=False, no_request_reply=True)
        return cls._clients[model]

    @classmethod
    def remove_client(cls, model=None):
        r"""Remove a broker client for a model, closing the communicator.

        Args:
            model (str, optional): Model to remove the client for. If not
                provided, the model identified by the YGG_MODEL_NAME
                environment variable will be used.

        """
        if model is None:
            model = cls.get_env('YGG_MODEL_NAME')
        if model is None:
            for model in cls._clients.keys():
                cls.remove_client(model)
            return
        if model in cls._clients:
            client = cls._clients.pop(model)
            client.close()
        
    @classmethod
    def _send_request(cls, action, *args, **kwargs):
        model = cls.get_env('YGG_MODEL_NAME')
        request = {
            'model': model,
            'action': action,
            'args': args,
            'kwargs': kwargs,
        }
        client = cls.get_client()
        flag, response = client.call(request)
        if not flag:
            raise BrokerError(f"{model}: Failed to send request to "
                              f"the broker {request}")
        if 'error' in response:
            raise BrokerError(f"{model}: Error on broker process during "
                              f"response to request {request}.\n"
                              f"{response['error']}\n"
                              f"{response['traceback']}")
        return response['return']

    @classmethod
    def update_model_comm_kwargs(cls, name, kwargs, self=None):
        r"""Update the communicator parameters for the partner model
        communicator in the case of a direct connection.

        Args:
            name (str): Name of the partner communicator.
            kwargs (dict): Parameters to update.

        """
        if self is None:
            return cls._send_request('update_model_comm_kwargs',
                                     name, kwargs)
        model = kwargs.pop('model')
        direction = kwargs.pop('direction')
        comm = self.find_model_comm(model, direction, name)
        assert isinstance(comm, dict)
        comm.update(kwargs)
        assert comm['direction'] == direction

    @classmethod
    def model_comm_kwargs(cls, name, direction, self=None):
        r"""Get communicator parameters for connecting to another model.

        Args:
            name (str): Local channel name.
            direction (str): Direction that the channel will operate in.

        Returns:
            dict: Parameters for the communicator.

        """
        if self is None:
            return cls._send_request('model_comm_kwargs',
                                     name, direction)
        model = self._current_request['model']
        prefix = f'{model}:'
        if not name.startswith(prefix):
            name = prefix + name
        out = {}
        is_split_server = False
        language = None
        with self.lock:
            model_driver = self._models[model]
            language = model_driver.language
            if isinstance(model_driver.is_server, dict):
                if ((name == model_driver.is_server['input']
                     or name == model_driver.is_server['output'])):
                    # TODO: Verify that this works
                    is_split_server = True
        comm = self.find_model_comm(model, direction, name)
        if isinstance(comm, dict):
            out = copy.deepcopy(comm)
            if (('address' not in comm
                 and isinstance(comm['commtype'], list)
                 and not all('address' in x for x in comm['commtype']))):
                raise DelayedRequestError(
                    f"Delaying creation of a forked communicator until "
                    f"all of the partner models create their comms "
                    f"({sum(('address' in x) for x in comm['commtype'])}"
                    f" missing).")
        else:
            out = comm.model_comm_kwargs
        out.update(
            name=name,
            is_interface=True,
            language=language,
        )
        if is_split_server or out['commtype'] == 'model_function':
            out['global_scope'] = model
        return out

    @classmethod
    def model_comm(cls, name, direction, **kwargs):
        r"""Create an interface communicator for a Python based model.

        Args:
            name (str): Communicator name.
            direction (str): Direction that the channel will operate in.
            **kwargs: Additional keyword arguments are passed to
                get_comm.

        Returns:
            CommBase: Interface communicator.

        """
        kwargs = dict(cls.model_comm_kwargs(name, direction), **kwargs)
        assert direction == kwargs['direction']
        name = kwargs.pop('name')
        global_scope = kwargs.pop('global_scope', False)
        global_name = name
        if isinstance(global_scope, str):
            global_name = global_scope
        if global_scope and global_name in cls._global_scope_comms:
            # TODO: Update with user provided keywords like format_str
            # for case where server or function comm is split between
            # two aliases
            return cls._global_scope_comms[global_name]
        if 'address' in kwargs:
            out = get_comm(name, **kwargs)
        else:
            partner_name = kwargs.pop('partner_name')
            out = new_comm(name, **kwargs)
            cls.update_model_comm_kwargs(
                partner_name, out.model_comm_kwargs)
        if global_scope:
            cls._global_scope_comms[global_name] = out
        return out

    @classmethod
    def model_error(cls, message, self=None):
        r"""Notify the broker of a model error.

        Args:
            message (str): Error message.

        """
        if self is None:
            return cls._send_request('model_error', message)
        model = self._current_request['model']
        raise BrokerError(f"Model {model} issued an error: \n{message}")
