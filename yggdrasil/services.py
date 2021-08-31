import os
import signal
import uuid
import json
import traceback
import yaml
import pprint
import functools
import threading
from yggdrasil import runner
from yggdrasil import platform
from yggdrasil.multitasking import WaitableFunction
from yggdrasil.tools import sleep, TimeOut, YggClass, timer_context
from yggdrasil.config import ygg_cfg


_default_service_type = ygg_cfg.get('services', 'default_type', 'flask')
_default_commtype = ygg_cfg.get('services', 'default_comm', None)
_default_address = ygg_cfg.get('services', 'address', None)
if platform._is_win:  # pragma: windows
    _shutdown_signal = signal.SIGINT
else:
    _shutdown_signal = signal.SIGTERM


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

    default_address = None
    default_port = None

    def __init__(self, name, *args, **kwargs):
        self.for_request = kwargs.pop('for_request', False)
        self.address = kwargs.pop('address', None)
        self.port = kwargs.pop('port', None)
        if self.address is None:
            self.address = _default_address
        if self.address is None:
            self.address = self.default_address
        if self.port is None:
            self.port = self.default_port
        if isinstance(self.address, str) and ('{port}' in self.address):
            self.address = self.address.format(port=self.port)
        self._args = args
        self._kwargs = kwargs
        super(ServiceBase, self).__init__(name, *args, **kwargs)
        if self.for_request:
            self.setup_client(*args, **kwargs)
        else:
            self.setup_server(*args, **kwargs)

    @property
    def opp_address(self):
        r"""str: Opposite address."""
        return self.address

    @classmethod
    def is_installed(cls):
        r"""bool: True if the class is fully installed, False otherwise."""
        return False  # pragma: no cover

    @property
    def is_running(self):
        r"""bool: True if the server is running."""
        return True
    
    def wait_for_server(self, timeout=15.0):
        r"""Wait for a service to start running.

        Args:
            timeout (float, optional): Time (in seconds) that should be waited
                for the server to start. Defaults to 15.

        Raises:
            RuntimeError: If the time limit is reached and the server still
                hasn't started.

        """
        T = TimeOut(timeout)
        while (not self.is_running) and (not T.is_out):
            self.debug("Waiting for server to start")
            sleep(0.1)
        if not self.is_running:  # pragma: debug
            raise RuntimeError("Server never started")

    def setup_server(self, *args, **kwargs):
        r"""Set up the machinery for receiving requests."""
        raise NotImplementedError  # pragma: no cover

    def setup_client(self, *args, **kwargs):
        r"""Set up the machinery for sending requests."""
        raise NotImplementedError  # pragma: no cover

    def start_server(self, remote_url=None, with_coverage=False):
        r"""Start the server."""
        if remote_url is None:
            remote_url = os.environ.get('YGGDRASIL_SERVICE_HOST_URL', None)
        if remote_url is None:
            remote_url = self.address
        os.environ.setdefault('YGGDRASIL_SERVICE_HOST_URL', remote_url)
        if with_coverage:
            try:
                from pytest_cov.embed import cleanup_on_signal
                cleanup_on_signal(_shutdown_signal)
            except ImportError:  # pragma: debug
                pass
        self.run_server()

    def run_server(self):
        r"""Begin listening for requests."""
        raise NotImplementedError  # pragma: no cover

    def respond(self, request, **kwargs):
        r"""Create a response to the request."""
        raise NotImplementedError  # pragma: no cover

    def shutdown(self, *args, **kwargs):
        r"""Shutdown the process from the server."""
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def send_request(self, request, **kwargs):
        r"""Send a request.

        Args:
            request (object): Request to send.
            **kwargs: Additional keyword arguments are passed to the call
                method.

        Returns:
            object: Response.

        """
        with timer_context(
                "REQUEST TIME: {elapsed}s ({request}, kwargs={kwargs})",
                request=request, kwargs=kwargs):
            request_str = self.serialize(request)
            if not self.for_request:
                x = self.__class__(self.name, *self._args,
                                   **self._kwargs, for_request=True,
                                   address=self.opp_address)
            else:
                x = self
            out = self.process_response(x.call(request_str, **kwargs))
        return out


class FlaskService(ServiceBase):
    r"""Flask based service."""

    service_type = 'flask'
    default_commtype = 'rest'
    default_address = 'http://localhost:{port}'
    default_port = int(os.environ.get("PORT", 5000))

    @classmethod
    def is_installed(cls):
        r"""bool: True if the class is fully installed, False otherwise."""
        try:
            import flask  # noqa: F401
            return True
        except ImportError:  # pragma: debug
            return False

    def __init__(self, *args, **kwargs):
        super(FlaskService, self).__init__(*args, **kwargs)
        # if str(self.port) not in self.address:
        #     parts = self.address.split(':')
        #     if parts[-1].strip('/').isdigit():
        #         self.port = int(parts[-1].strip('/'))
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
        self.queue = {}
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
        self.app.run(host='0.0.0.0', port=self.port)

    def shutdown(self):
        r"""Shutdown the process from the server."""
        # if not self.for_request:
        #     func = self.request.environ.get('werkzeug.server.shutdown')
        #     # Explicitly cleaning up the pytest coverage plugin is required
        #     # to ensure that the server methods are properly covered during
        #     # cleanup.
        #     try:
        #         from pytest_cov.embed import cleanup
        #         cleanup()
        #     except ImportError:  # pragma: debug
        #         pass
        #     if func is None:  # pragma: debug
        #         raise RuntimeError('Not running with the Werkzeug Server')
        #     func()  # pragma: no cover
        pass
        
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
            r.raise_for_status()
        except BaseException as e:
            raise ClientError(e)
        return r.json()
        

class RMQService(ServiceBase):
    r"""RabbitMQ based service."""

    service_type = 'rmq'
    default_commtype = 'rmq'
    default_port = 5672

    @classmethod
    def is_installed(cls):
        r"""bool: True if the class is fully installed, False otherwise."""
        from yggdrasil.communication.RMQComm import check_rmq_server
        return check_rmq_server()

    def _init_rmq(self, *args, **kwargs):
        from yggdrasil.communication.RMQComm import pika, get_rmq_parameters
        self.pika = pika
        if not self.address:
            kwargs['port'] = self.port
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
        if self.exchange:  # pragma: debug
            # self.channel.exchange_declare(exchange=self.exchange,
            #                               auto_delete=True)
            raise NotImplementedError("There is a bug when using the "
                                      "non-default exchange.")
        self.channel.queue_declare(queue=self.queue)
        self.channel.basic_qos(prefetch_count=1)
        self.consumer_tag = self.channel.basic_consume(
            queue=self.queue,
            on_message_callback=self._on_request)
        cb = functools.partial(self.shutdown, in_callback=True)
        self.channel.add_on_cancel_callback(cb)
    
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
        except self.pika.exceptions.ChannelWrongStateError:  # pragma: debug
            pass

    def shutdown(self, in_callback=False):
        r"""Shutdown the process from the server."""
        if not self.channel:  # pragma: debug
            return
        if self.for_request:
            queue = self.callback_queue
            in_callback = False
        else:
            queue = self.queue
        if not in_callback:
            self.channel.basic_cancel(consumer_tag=self.consumer_tag)
            if not self.for_request:
                return
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
            if self.channel is None:  # pragma: debug
                return False
            self.channel.queue_declare(queue=self.queue, passive=True)
            return True
        except (self.pika.exceptions.ChannelClosedByBroker,
                self.pika.exceptions.ChannelWrongStateError):  # pragma: intermittent
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
        except (self.pika.exceptions.UnroutableError,
                self.pika.exceptions.StreamLostError) as e:  # pragma: debug
            raise ClientError(e)
        T = TimeOut(timeout)
        while (self.response is None) and (not T.is_out):
            self.connection.process_data_events()
            sleep(0.5)
        if self.response is None:
            raise ClientError("No response received")
        return self.response


def create_service_manager_class(service_type=None):
    r"""Create an integration manager service with the specified base.

    Args:
        service_type (ServiceBase, str, optional): Base class that should be
            used. Defaults to ('services', 'default_type') configuration
            options, if set, and 'flask' if not.

    Returns:
        type: Subclass of ServiceBase to handle starting/stopping integrations
            running as services.

    """
    if service_type is None:
        service_type = _default_service_type
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

        def __init__(self, name=None, commtype=None, **kwargs):
            if name is None:
                name = 'ygg_integrations'
            self.integrations = {}
            self.stopped_integrations = {}
            self.registry = IntegrationServiceRegistry()
            if commtype is None:
                commtype = _default_commtype
            self.commtype = commtype
            super(IntegrationServiceManager, self).__init__(name, **kwargs)
            if self.commtype is None:
                self.commtype = self.default_commtype

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
                **kwargs: Additional keyword arguments are included in the
                    request.

            """
            if isinstance(yamls, str):
                yamls = [yamls]
            if name is None:
                name = yamls
            request = dict(kwargs, name=name, yamls=yamls, action=action)
            wait_for_complete = (action in ['start', 'stop', 'shutdown'])
            out = super(IntegrationServiceManager, self).send_request(request)
            if wait_for_complete and (out['status'] != 'complete'):
                def is_complete():
                    out.update(
                        super(IntegrationServiceManager, self).send_request(
                            request))
                    return (out['status'] == 'complete')
                x = WaitableFunction(is_complete, polling_interval=0.5)
                x.wait(30, on_timeout=f"Request did not complete: {request}")
            return out

        def setup_server(self, *args, **kwargs):
            r"""Set up the machinery for receiving requests."""
            super(IntegrationServiceManager, self).setup_server(*args, **kwargs)
            if service_type == FlaskService:
                @self.app.route('/')
                def landing_page():
                    return self.respond({'action': 'status',
                                         'name': None,
                                         'yamls': None})['status']
                
                from yggdrasil.communication import RESTComm
                RESTComm.add_comm_server_to_app(self.app)
            
        def stop_server(self):
            r"""Stop the server from the client-side."""
            assert(self.for_request)
            try:
                response = self.send_request(action='shutdown')
            except ClientError:  # pragma: debug
                return
            os.kill(response['pid'], _shutdown_signal)
            self.shutdown()

        def start_integration(self, x, yamls, **kwargs):
            r"""Start an integration if it is not already running.

            Args:
                x (str, tuple): Hashable object that should be used to
                    identify the integration being started in the registry of
                    running integrations.
                yamls (list): Set of YAML specification files defining the
                    integration that should be run as as service.
                **kwargs: Additional keyword arguments are passed to get_runner.

            Returns:
                bool: True if the integration started, False otherwise.

            """
            if (x in self.integrations) and (not self.integrations[x].is_alive):
                if not self.stop_integration(x):
                    return False
            if x in self.stopped_integrations:
                if not self.stop_integration(x):
                    return False
                self.stopped_integrations.pop(x)
            if x not in self.integrations:
                self.integrations[x] = runner.get_runner(
                    yamls, complete_partial=True, as_service=True,
                    partial_commtype=self.commtype, **kwargs)
                self.integrations[x].run(signal_handler=False)
            return True

        def _stop_integration(self, x):
            r"""Finish stopping an integration in a thread."""
            m = self.integrations.pop(x)
            if m.is_alive:
                m.terminate()
            m.atexit()

        def stop_integration(self, x):
            r"""Stop a running integration.

            Args:
                x (str, tuple): Hashable object associated with the
                    integration service that should be stopped. If None,
                    all of the running integrations are stopped.

            Returns:
                bool: True if the integration has stopped.

            Raises:
                KeyError: If there is not a running integration associated
                    with the specified hashable object.

            """
            if x is None:
                return all(self.stop_integration(k)
                           for k in (list(self.integrations.keys())
                                     + list(self.stopped_integrations)))
            if x in self.stopped_integrations:
                pass
            elif x not in self.integrations:
                raise KeyError(f"Integration defined by {x} not running")
            elif service_type == RMQService:
                self._stop_integration(x)
                return True
            else:
                mthread = threading.Thread(target=self._stop_integration,
                                           args=(x,), daemon=True)
                mthread.start()
                self.stopped_integrations[x] = mthread
            return not self.stopped_integrations[x].is_alive()

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
            if x not in self.integrations:  # pragma: debug
                raise KeyError(f"Integration defined by {x} not running")
            m = self.integrations[x].modeldrivers['dummy_model']
            out = m['instance'].service_partner
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
            if not super(IntegrationServiceManager, self).is_running:  # pragma: debug
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
            name = None
            action = None
            yamls = None
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
                        else:  # pragma: debug
                            raise RuntimeError("No YAML files specified.")
                    if self.start_integration(name, yamls, **request):
                        response = {'status': 'complete'}
                        response.update(self.integration_info(name))
                    else:
                        response = {'status': 'starting'}
                elif action == 'stop':
                    if self.stop_integration(name):
                        response = {'status': 'complete'}
                    else:
                        response = {'status': 'stopping'}
                elif action == 'shutdown':
                    if self.stop_integration(None):
                        self.shutdown()
                        response = {'status': 'complete',
                                    'pid': os.getpid()}
                    else:
                        response = {'status': 'shutting down'}
                elif action == 'status':
                    response = {'status': 'done'}
                    if name is None:
                        fmt = ('Address: %s\n'
                               'Available Services:\n%s\n'
                               'Running Services:\n%s')
                        registry_str = '\t' + '\n\t'.join(
                            pprint.pformat(self.registry.registry).splitlines())
                        running_str = ''
                        for k, v in self.integrations.items():
                            running_str += '\t%s:\n\t\t%s' % (
                                k, '\n\t\t'.join(v.printStatus(
                                    return_str=True).splitlines()))
                        args = (self.address, registry_str, running_str)
                        response['status'] = fmt % args
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
                if action == 'start':  # pragma: intermittent
                    self.respond({'name': name, 'action': 'stop', 'yamls': None})
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
            if return_str:
                msg, _ = self.logger.process(status['status'], {})
                return msg
            getattr(self.logger, level)(status['status'])
            
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
        out = {}
        if os.path.isfile(self.filename):
            with open(self.filename, 'r') as fd:
                out = yaml.safe_load(fd)
        return out

    def save(self, registry):
        r"""Save the registry to self.filename.

        Args:
            registry (dict): Dictionary of integrations to save.

        """
        with open(self.filename, 'w') as fd:
            yaml.dump(registry, fd)

    def load_collection(self, name):
        r"""Read a collection of integration registry entries from an YAML.

        Args:
            name (str): Full path to a YAML file containing one or more
                registry entries mapping between integration name and YAML
                specification files.

        Returns:
            dict: Loaded registry entries.

        """
        with open(name, 'r') as fd:
            out = yaml.safe_load(fd.read())
        assert(isinstance(out, dict))
        base_dir = os.path.dirname(name)
        for k in out.keys():
            v = out.get(k, [])
            out[k] = []
            for x in v:
                if not os.path.isabs(x):
                    x = os.path.join(base_dir, x)
                out[k].append(x)
        return out

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
        if os.path.isfile(name):
            names = list(self.load_collection(name).keys())
        else:
            names = [name]
        for k in names:
            if k not in registry:
                keys = list(self.registry.keys())
                raise KeyError(f"There is not an integration service "
                               f"registered under the name '{k}'. Existing "
                               f"services are {keys}")
            registry.pop(k)
        self.save(registry)

    def add(self, name, yamls=None, **kwargs):
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
        registry = self.load()
        if os.path.isfile(name):
            assert(not yamls)
            collection = {k: dict(kwargs, name=k, yamls=v)
                          for k, v in self.load_collection(name).items()}
        else:
            assert(yamls)
            collection = {name: dict(kwargs, name=name, yamls=yamls)}
        for k, v in collection.items():
            if k in registry:
                old = pprint.pformat(registry[k])
                new = pprint.pformat(v)
                raise ValueError(f"There is an registry integration "
                                 f"associated with the name '{k}'. Remove "
                                 f"the registry entry before adding a new "
                                 f"one.\n"
                                 f"    Registry:\n{old}\n    New:\n{new}")
            registry[k] = v
        self.save(registry)
