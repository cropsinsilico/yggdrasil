import os
import signal
import uuid
import json
import traceback
import threading
import yaml
import pprint
from yggdrasil import runner
from yggdrasil import platform
from yggdrasil.tools import sleep, TimeOut, YggClass
from yggdrasil.config import ygg_cfg


_default_service_type = ygg_cfg.get('services', 'default_type', 'flask')
_default_commtype = ygg_cfg.get('services', 'default_comm', None)
_default_address = ygg_cfg.get('services', 'address', None)


class ClientError(BaseException):
    r"""Error raised by errors when calling the server from the client."""
    pass


class ServerError(BaseException):
    r"""Error raised when there was an error on the server."""
    pass


class ServiceBase(YggClass):
    r"""Base class for sending/responding to service requests.

    Args:
        name (str): Name that should be used to initialize an address for the
            service.
        for_request (bool, optional): If True, a client-side connection is
            initialized. If False a server-side connection is initialized.
            Defaults to False.
        address (str, optional): The address that the service can be accessed
            from. Defaults to ('services', 'address') configuration option, if
            set, and None if not.
        *args: Additional arguments are used to initialize the client/server
            connection.
        **kwargs: Additional keyword arguments are used to initialize the
            client/server connection.

    """

    def __init__(self, name, *args, **kwargs):
        self.for_request = kwargs.pop('for_request', False)
        self.address = kwargs.pop('address', None)
        if self.address is None:
            self.address = _default_address
        self._args = args
        self._kwargs = kwargs
        super(ServiceBase, self).__init__(name, *args, **kwargs)
        if self.for_request:
            self.setup_client(*args, **kwargs)
        else:
            self.setup_server(*args, **kwargs)

    @classmethod
    def is_installed(cls):
        r"""bool: True if the class is fully installed, False otherwise."""
        return False

    @property
    def is_running(self):
        r"""bool: True if the server is running."""
        return True
    
    def wait_for_server(self, timeout=10.0):
        r"""Wait for a service to start running.

        Args:
            timeout (float, optional): Time (in seconds) that should be waited
                for the server to start. Defaults to 10.

        Raises:
            RuntimeError: If the time limit is reached and the server still
                hasn't started.

        """
        T = TimeOut(timeout)
        while (not self.is_running) and (not T.is_out):
            self.debug("Waiting for server to start")
            sleep(1)
        if not self.is_running:  # pragma: debug
            raise RuntimeError("Server never started")

    def setup_server(self, *args, **kwargs):
        r"""Set up the machinery for receiving requests."""
        raise NotImplementedError

    def setup_client(self, *args, **kwargs):
        r"""Set up the machinery for sending requests."""
        raise NotImplementedError

    def run_server(self):
        r"""Begin listening for requests."""
        raise NotImplementedError

    def respond(self, request, **kwargs):
        r"""Create a response to the request."""
        raise NotImplementedError

    def shutdown(self, *args, **kwargs):
        r"""Shutdown the process from the server."""
        raise NotImplementedError

    def process_request(self, request, **kwargs):
        r"""Process a request and return a response.

        Args:
            request (str): Serialized request that should be processed.
            **kwargs: Additional keyword arguments are passed to the respond
                method.

        Returns:
            str: Serialized response.

        """
        request = self.deserialize_request(request)
        response = self.respond(request, **kwargs)
        return self.serialize_response(response)

    def process_response(self, response):
        r"""Process a response.

        Args:
            response (str): Serialized response that should be processed.
        
        Returns:
            object: The deserialized, processed response.

        """
        return self.deserialize(response)

    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str): Message to deserialize.

        Returns:
            object: Deserialized message.

        """
        return json.loads(msg)

    def serialize(self, msg):
        r"""Serialize a message.

        Args:
            msg (object): Message to serialize.

        Returns:
            str: Serialized message.

        """
        return json.dumps(msg)

    def deserialize_request(self, request):
        r"""Deserialize a request message.

        Args:
            request (str): Serialized request.

        Returns:
            object: Deserialized request.

        """
        return self.deserialize(request)

    def serialize_response(self, response):
        r"""Serialize a response message.

        Args:
            request (object): Request to serialize.

        Returns:
            str: Serialized request.

        """
        return self.serialize(response)

    def call(self, *args, **kwargs):
        r"""Send a request."""
        raise NotImplementedError

    def send_request(self, request, **kwargs):
        r"""Send a request.

        Args:
            request (object): Request to send.
            **kwargs: Additional keyword arguments are passed to the call
                method.

        Returns:
            object: Response.

        """
        request_str = self.serialize(request)
        if not self.for_request:
            x = self.__class__(self.name, *self._args,
                               **self._kwargs, for_request=True)
        else:
            x = self
        return self.process_response(x.call(request_str, **kwargs))


class FlaskService(ServiceBase):
    r"""Flask based service."""

    @classmethod
    def is_installed(cls):
        r"""bool: True if the class is fully installed, False otherwise."""
        try:
            import flask  # noqa: F401
            return True
        except ImportError:
            return False

    def __init__(self, *args, **kwargs):
        super(FlaskService, self).__init__(*args, **kwargs)
        if self.address is None:
            self.address = 'http://localhost:5000'
        if not self.address.endswith('/'):
            self.address += '/'

    def setup_server(self, *args, **kwargs):
        r"""Set up the machinery for receiving requests.

        Args:
            *args: Arguments are ignored.
            **kwargs: Keyword arguments are ignored.

        """
        from flask import Flask
        from flask import request
        from flask import jsonify
        self.request = request
        self.jsonify = jsonify
        self.app = Flask(__name__)
        
        @self.app.route('/' + self.name, methods=['POST'])
        def _target(*req_args):
            return self.process_request(self.request.json, args=req_args)
        
    def setup_client(self, *args, **kwargs):
        r"""Set up the machinery for sending requests."""
        pass

    def run_server(self):
        r"""Begin listening for requests."""
        self.app.run()

    def shutdown(self):
        r"""Shutdown the process from the server."""
        func = self.request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        
    def deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str): Message to deserialize.

        Returns:
            object: Deserialized message.

        """
        return msg  # should already be deserialized

    def serialize(self, msg):
        r"""Serialize a message.

        Args:
            msg (object): Message to serialize.

        Returns:
            str: Serialized message.

        """
        return msg  # should already be serialized
    
    def serialize_response(self, response):
        r"""Serialize a response message.

        Args:
            request (object): Request to serialize.

        Returns:
            str: Serialized request.

        """
        return self.jsonify(response)

    def call(self, request, **kwargs):
        r"""Send a request.

        Args:
            request (object): JSON serializable request.
            **kwargs: Keyword arguments are ignored.

        Returns:
            object: Response.

        """
        import requests
        try:
            r = requests.post(self.address + self.name, json=request)
        except BaseException as e:
            raise ClientError(e)
        return r.json()
        

class RMQService(ServiceBase):
    r"""RabbitMQ based service."""

    @classmethod
    def is_installed(cls):
        r"""bool: True if the class is fully installed, False otherwise."""
        from yggdrasil.communication.RMQComm import check_rmq_server
        return check_rmq_server()

    def _init_rmq(self, *args, **kwargs):
        from yggdrasil.communication.RMQComm import pika, get_rmq_parameters
        self.pika = pika
        if not self.address:
            self.address, _, _ = get_rmq_parameters(*args, **kwargs)
        self.queue = self.name
        # Unclear why using a non-default exchange prevents the server
        # from starting
        self.exchange = ''
        parameters = pika.URLParameters(self.address)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def setup_server(self, *args, **kwargs):
        r"""Set up the machinery for receiving requests.

        Args:
            *args: Arguments are used to initialize the RabbitMQ connections
                via _init_rmq.
            **kwargs: Keyword arguments are used to initialize the RabbitMQ
                connections via _init_rmq.

        """
        self._init_rmq(*args, **kwargs)
        if self.exchange:
            self.channel.exchange_declare(exchange=self.exchange,
                                          auto_delete=True)
        self.channel.queue_declare(queue=self.queue)
        self.channel.basic_qos(prefetch_count=1)
        self.consumer_tag = self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=self._on_request)
    
    def setup_client(self, *args, **kwargs):
        r"""Set up the machinery for sending requests.

        Args:
            *args: Arguments are used to initialize the RabbitMQ connections
                via _init_rmq.
            **kwargs: Keyword arguments are used to initialize the RabbitMQ
                connections via _init_rmq.

        """
        self._init_rmq(*args, **kwargs)
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        self.consumer_tag = self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._on_response,
            auto_ack=True)

    def run_server(self):
        r"""Listen for requests."""
        try:
            self.channel.start_consuming()
        except self.pika.exceptions.ChannelWrongStateError:
            pass

    def shutdown(self):
        r"""Shutdown the process from the server."""
        if not self.channel:
            return
        if self.for_request:
            queue = self.callback_queue
        else:
            queue = self.queue
        self.channel.basic_cancel(consumer_tag=self.consumer_tag)
        self.channel.queue_delete(queue=queue)
        self.channel.close()
        self.channel = None
        self.connection.close()
        self.connection = None

    def _on_request(self, ch, method, props, body):
        response = self.process_request(body)
        ch.basic_publish(exchange=self.exchange,
                         routing_key=props.reply_to,
                         properties=self.pika.BasicProperties(
                             correlation_id=props.correlation_id),
                         body=response)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    @property
    def is_running(self):
        r"""bool: True if the server is running."""
        try:
            self.channel.queue_declare(queue=self.queue, passive=True)
            return True
        except self.pika.exceptions.ChannelClosedByBroker:
            self.connection.close()
            assert(self.for_request)
            self.setup_client(*self._args, **self._kwargs)
            return False

    def call(self, request, timeout=10.0, **kwargs):
        r"""Send a request.

        Args:
            request (str): Serialized request.
            timeout (float, optional): Time (in seconds) that should be waited
                for a response to be returned. Defaults to 10.
            **kwargs: Keyword arguments are ignored.

        Returns:
            str: Serialized response.

        """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        try:
            self.channel.basic_publish(exchange=self.exchange,
                                       routing_key=self.queue,
                                       properties=self.pika.BasicProperties(
                                           reply_to=self.callback_queue,
                                           correlation_id=self.corr_id),
                                       body=request)
        except self.pika.exceptions.UnroutableError as e:
            raise ClientError(e)
        T = TimeOut(timeout)
        while (self.response is None) and (not T.is_out):
            self.connection.process_data_events()
            sleep(0.5)
        if self.response is None:
            raise ClientError("No response received")
        return self.response


def create_service_manager_class(service_type=_default_service_type):
    r"""Create an integration manager service with the specified base.

    Args:
        service_type (ServiceBase, str, optional): Base class that should be
            used. Defaults to ('services', 'default_type') configuration
            options, if set, and 'flask' if not.

    Returns:
        type: Subclass of ServiceBase to handle starting/stopping integrations
            running as services.

    """
    if isinstance(service_type, str):
        cls_map = {'flask': FlaskService, 'rmq': RMQService}
        service_type = cls_map[service_type]

    class IntegrationServiceManager(service_type):
        r"""Manager to track running integrations.

        Args:
            name (str): Name that should be used to initialize an address for
                the service. Defaults to 'ygg_integrations'.
            commtype (str, optional): Communicator type that should be used
                for the connections to services. Defaults to ('services',
                'default_comm') configuration option, if set, and None if not.
            **kwargs: Additional keyword arguments are passed to the __init__
                method for the service_type class.

        """

        def __init__(self, name=None, commtype=_default_commtype, **kwargs):
            if name is None:
                name = 'ygg_integrations'
            self.integrations = {}
            self.registry = IntegrationServiceRegistry()
            self.commtype = commtype
            super(IntegrationServiceManager, self).__init__(name, **kwargs)

        def send_request(self, name=None, yamls=None, action='start', **kwargs):
            r"""Send a request.

            Args:
                name (str, tuple, optional): A hashable object that will be
                    used to reference the integration. If not provided,
                    the yamls keyword will be used.
                yamls (list, str, optional): One or more YAML files defining
                    a network of models to run as a service. Defaults to None.
                action (str, optional): Action that is being requested.
                    Defaults to 'start'.
                **kwargs: Additional keyword arguments are passed to the call
                    method.

            """
            if isinstance(yamls, str):
                yamls = [yamls]
            if name is None:
                name = yamls
            request = dict(name=name, yamls=yamls, action=action)
            return super(IntegrationServiceManager, self).send_request(
                request, **kwargs)

        def stop_server(self):
            r"""Stop the server from the client-side."""
            try:
                response = self.send_request(action='shutdown')
            except ClientError:
                return
            if platform._is_win:  # pragma: windows
                sig = signal.CTRL_C_EVENT
            else:
                sig = signal.SIGKILL
            os.kill(response['pid'], sig)

        def start_integration(self, x, yamls, **kwargs):
            r"""Start an integration if it is not already running.

            Args:
                x (str, tuple): Hashable object that should be used to
                    identify the integration being started in the registry of
                    running integrations.
                yamls (list): Set of YAML specification files defining the
                    integration that should be run as as service.
                **kwargs: Additional keyword arguments are passed to get_runner.

            """
            if (x in self.integrations) and (not self.integrations[x].is_alive):
                self.stop_integration(x)
            if x not in self.integrations:
                self.integrations[x] = runner.get_runner(
                    yamls, complete_partial=True,
                    partial_commtype=self.commtype, **kwargs)
                self.integrations[x].run(signal_handler=False)

        def stop_integration(self, x):
            r"""Stop a running integration.

            Args:
                x (str, tuple): Hashable object associated with the
                    integration service that should be stopped. If None,
                    all of the running integrations are stopped.

            Raises:
                KeyError: If there is not a running integration associated
                    with the specified hashable object.

            """
            if x is None:
                for k in list(self.integrations.keys()):
                    self.stop_integration(k)
                return
            if x not in self.integrations:
                raise KeyError(f"Integration defined by {x} not running")
            m = self.integrations.pop(x)
            m.terminate()
            m.atexit()

        def integration_info(self, x):
            r"""Get information about an integration and how to connect to it.

            Args:
                x (str, tuple): Hashable object associated with the
                    integration to get information on.

            Returns:
                dict: Information about the integration.

            Raises:
                KeyError: If there is not a running integration associated
                    with the specified hashable object.

            """
            if x not in self.integrations:
                raise KeyError(f"Integration defined by {x} not running")
            m = self.integrations[x].modeldrivers['dummy_model']
            out = m['instance'].connections
            name = 'dummy'
            if isinstance(x, str) and (not os.path.isfile(x)):
                name = x
            out.update(name=name,
                       args=name,
                       language='dummy')
            return out

        @property
        def is_running(self):
            r"""bool: True if the server is running."""
            if not super(IntegrationServiceManager, self).is_running:
                return False
            try:
                response = self.send_request(action='ping')
                return response['status'] == 'running'
            except ClientError:
                return False

        def respond(self, request, **kwargs):
            r"""Create a response to the request.

            Args:
                request (dict): Request to respond to.
                **kwargs: Additional keyword arguments are ignored.

            Returns:
                dict: Response to the request.

            """
            try:
                name = request.pop('name')
                action = request.pop('action')
                yamls = request.pop('yamls')
                if isinstance(name, list):
                    name = tuple(name)
                if action == 'start':
                    if yamls is None:
                        reg = self.registry.registry.get(name, None)
                        if isinstance(name, tuple):
                            yamls = list(name)
                        elif isinstance(name, str) and os.path.isfile(name):
                            yamls = [name]
                        elif reg is not None:
                            yamls = reg['yamls']
                            for k, v in reg.items():
                                if k not in ['name', 'yamls']:
                                    request.setdefault(k, v)
                        else:
                            raise RuntimeError("No YAML files specified.")
                    self.start_integration(name, yamls, **request)
                    response = {'status': 'started'}
                    response.update(self.integration_info(name))
                elif action == 'stop':
                    self.stop_integration(name)
                    response = {'status': 'stopped'}
                elif action == 'shutdown':
                    self.stop_integration(None)
                    tobj = threading.Timer(1, self.shutdown)
                    tobj.start()
                    response = {'status': 'shutting down',
                                'pid': os.getpid()}
                elif action == 'status':
                    response = {'status': 'done'}
                    if name is None:
                        response['integrations'] = list(self.integrations.keys())
                        for k, v in self.integrations.items():
                            response[k] = v.printStatus(return_str=True)
                    else:
                        response['status'] = self.integrations[name].printStatus(
                            return_str=True)
                elif action == 'ping':
                    response = {'status': 'running'}
                else:
                    raise RuntimeError(f"Unsupported action: '{action}'")
            except BaseException as e:
                tb = traceback.format_exc()
                response = {'error': str(e), 'traceback': tb}
            return response

        def process_response(self, response):
            r"""Process a response.

            Args:
                response (str): Serialized response that should be processed.

            Returns:
                object: The deserialized, processed response.

            Raises:
                ServerError: If the response indicates there was an error on
                    the server during the creation of the response.

            """
            response = super(
                IntegrationServiceManager, self).process_response(response)
            if 'error' in response:
                raise ServerError('%s\n%s' % (response['traceback'],
                                              response['error']))
            return response

        def printStatus(self, level='info', return_str=False):
            r"""Print the status of the service manager including available
            and running services."""
            status = self.send_request(action='status')
            fmt = ('Address: %s\n'
                   'Available Services:\n%s\n'
                   'Running Services:\n%s')
            registry_str = '\t' + '\n\t'.join(
                pprint.pformat(self.registry.registry).splitlines())
            running_str = ''
            for k in status['integrations']:
                running_str += '\t%s:\n\t\t%s' % (
                    k, '\n\t\t'.join(status[k].splitlines()))
            args = (self.address, registry_str, running_str)
            if return_str:
                msg, _ = self.logger.process(fmt, {})
                return msg % args
            getattr(self.logger, level)(fmt, *args)
            
    return IntegrationServiceManager


def IntegrationServiceManager(service_type=None, **kwargs):
    r"""Start a management service to track running integrations.

    Args:
        service_type (ServiceBase, str, optional): Base class that should be
            used. Defaults to ('services', 'default_type') configuration
            options, if set, and 'flask' if not. If there is an address
            provided, the service type will be determined by parsing the
            address.
        **kwargs: Additional keyword arguments are used to intialized the
            manager class instance.

    """
    if service_type is None:
        if kwargs.get('address', None):
            if kwargs['address'].startswith('amqp://'):
                service_type = 'rmq'
            else:
                service_type = 'flask'
        else:
            service_type = _default_service_type
    cls = create_service_manager_class(service_type=service_type)
    return cls(**kwargs)


class IntegrationServiceRegistry(object):
    r"""Class for managing integration services.

    Args:
        filename (str, optional): File where the registry will be/is stored.
            Defaults to '~/.yggdrasil_services.yml'.

    """

    def __init__(self, filename=os.path.join('~', '.yggdrasil_services.yml')):
        self.filename = os.path.expanduser(filename)

    @property
    def registry(self):
        r"""dict: Existing registry of integrations."""
        return self.load()

    def load(self):
        r"""Load the dictionary of existing integrations that have been
        registered.

        Returns:
            dict: Existing registry of integrations.

        """
        if os.path.isfile(self.filename):
            with open(self.filename, 'r') as fd:
                return yaml.safe_load(fd)
        return {}

    def save(self, registry):
        r"""Save the registry to self.filename.

        Args:
            registry (dict): Dictionary of integrations to save.

        """
        with open(self.filename, 'w') as fd:
            yaml.dump(registry, fd)

    def remove(self, name):
        r"""Remove an integration service from the registry.

        Args:
            name (str): Name associated with the integration service that
                should be removed from the registry.

        Raises:
            KeyError: If there is not an integration service associated with
                the specified name.

        """
        registry = self.load()
        if name not in registry:
            keys = list(self.registry.keys())
            raise KeyError(f"There is not an integration service registered "
                           f"under the name '{name}'. Existing services are "
                           f"{keys}")
        registry.pop(name)
        self.save(registry)

    def add(self, name, yamls, **kwargs):
        r"""Add an integration service to the registry.

        Args:
            name (str): Name that will be used to access the integration
                service when starting or stopping it.
            yamls (str, list): Set of one or more YAML specification files
                defining the integration.
            **kwargs: Additional keyword arguments are added to the new entry.

        Raises:
            ValueError: If there is already an integration with the specified
                name.

        """
        entry = dict(kwargs, name=name, yamls=yamls)
        registry = self.load()
        if name in registry:
            old = pprint.pformat(registry[name])
            new = pprint.pformat(entry)
            raise ValueError(f"There is an registry integration associated "
                             f"with the name '{name}'. Remove the registry "
                             f"entry before adding a new one.\n"
                             f"    Registry:\n{old}\n    New:\n{new}")
        registry[name] = entry
        self.save(registry)
