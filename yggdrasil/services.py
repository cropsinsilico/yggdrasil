import os
import sys
import signal
import uuid
import json
import traceback
import yaml
import glob
import pprint
import functools
import threading
import logging
from yggdrasil import runner
from yggdrasil import platform
from yggdrasil.multitasking import wait_on_function, ValueEvent
from yggdrasil.tools import YggClass, kill
from yggdrasil.config import ygg_cfg


_service_host_env = 'YGGDRASIL_SERVICE_HOST_URL'
_service_repo_dir = 'YGGDRASIL_SERVICE_REPO_DIR'
_default_service_type = ygg_cfg.get('services', 'default_type', 'flask')
_default_commtype = ygg_cfg.get('services', 'default_comm', None)
_default_address = ygg_cfg.get('services', 'address', None)
_client_id = ygg_cfg.get('services', 'client_id', None)
if platform._is_win:  # pragma: windows
    _shutdown_signal = signal.SIGBREAK
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
        self._is_running = False
        super(ServiceBase, self).__init__(name, *args, **kwargs)
        if self.for_request:
            self.setup_client(*args, **kwargs)
        else:
            self.setup_server(*args, **kwargs)

    @classmethod
    def is_installed(cls):
        r"""bool: True if the class is fully installed, False otherwise."""
        return False  # pragma: no cover

    @property
    def is_running(self):
        r"""bool: True if the server is running."""
        if self.for_request:
            return True
        else:
            return self._is_running
    
    def wait_for_server(self, timeout=15.0):
        r"""Wait for a service to start running.

        Args:
            timeout (float, optional): Time (in seconds) that should be waited
                for the server to start. Defaults to 15.

        Raises:
            RuntimeError: If the time limit is reached and the server still
                hasn't started.

        """
        wait_on_function(lambda: self.is_running, timeout=timeout,
                         on_timeout="Server never started")

    def setup_server(self, *args, **kwargs):
        r"""Set up the machinery for receiving requests."""
        raise NotImplementedError  # pragma: no cover

    def setup_client(self, *args, **kwargs):
        r"""Set up the machinery for sending requests."""
        raise NotImplementedError  # pragma: no cover

    def set_log_level(self, log_level):
        r"""Set the logging level.

        Args:
            log_level (int): Logging level.

        """
        import logging
        logging.basicConfig(level=log_level)

    def start_server(self, remote_url=None, with_coverage=False,
                     log_level=None, model_repository=None):
        r"""Start the server.

        Args:
            remote_url (str optional): Address for the URL that remote
                integrations will use to connect to this server. Defaults to
                None and is set based on the YGGDRASIL_SERVICE_HOST_URL
                environment variable if it is set and is the local address
                otherwise.
            with_coverage (bool, optional): If True, the server is started
                with coverage. Defaults to False.
            log_level (int, optional): Level of log messages that should be
                printed. Defaults to None and is ignored.
            model_repository (str, optional): URL of directory in a Git
                repository containing YAMLs that should be added to the model
                registry. Defaults to None and is ignored.

        """
        if remote_url is None:
            remote_url = os.environ.get(_service_host_env, None)
        if remote_url is None:
            remote_url = self.address
        if model_repository is not None:
            repo_dir = self.registry.add_from_repository(model_repository)
            os.environ.setdefault(_service_repo_dir, repo_dir)
        os.environ.setdefault(_service_host_env, remote_url)
        if log_level is not None:
            self.set_log_level(log_level)
        if with_coverage:  # pragma: testing
            def handle_shutdown(sig, frame):
                sys.exit()
            signal.signal(_shutdown_signal, handle_shutdown)
            # try:
            #     from pytest_cov.embed import cleanup_on_signal
            #     cleanup_on_signal(_shutdown_signal)
            # except ImportError:  # pragma: debug
            #     pass
        self._is_running = True
        try:
            self.run_server()
        finally:
            self._is_running = False

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
        request_str = self.serialize(request)
        assert(self.for_request)
        # if not self.for_request:
        #     x = self.__class__(self.name, *self._args,
        #                        **self._kwargs, for_request=True,
        #                        address=self.opp_address)
        # else:
        #     x = self
        return self.process_response(self.call(request_str, **kwargs))


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

    def set_log_level(self, log_level):
        r"""Set the logging level.

        Args:
            log_level (int): Logging level.

        """
        super(FlaskService, self).set_log_level(log_level)
        from flask.logging import default_handler
        werkzeug_logger = logging.getLogger('werkzeug')
        default_handler.setLevel(level=log_level)
        self.app.logger.setLevel(level=log_level)
        werkzeug_logger.setLevel(level=log_level)
        
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
            self.response.set(body)

    @property
    def is_running(self):
        r"""bool: True if the server is running."""
        return (super(RMQService, self).is_running and bool(self.channel))

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
        self.response = ValueEvent()
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
        
        def process_events():
            self.connection.process_data_events()
            return self.response.is_set()
        
        def client_error():
            raise ClientError("No response received")

        if not self.response.is_set():
            wait_on_function(
                process_events, timeout=timeout, polling_interval=0.5,
                on_timeout=client_error)
        return self.response.get()


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
            is_app (bool, optional): If True, the service manager will be run
                as an app and will not be expected to be shut down by clients.
                Defaults to False.
            **kwargs: Additional keyword arguments are passed to the __init__
                method for the service_type class.

        """

        def __init__(self, name=None, commtype=None, is_app=False, **kwargs):
            if name is None:
                name = 'ygg_integrations'
            self.integrations = {}
            self.stopped_integrations = {}
            self.registry = IntegrationServiceRegistry()
            if commtype is None:
                commtype = _default_commtype
            self.commtype = commtype
            self.is_app = is_app
            super(IntegrationServiceManager, self).__init__(name, **kwargs)
            if self.commtype is None:
                self.commtype = self.default_commtype

        @property
        def client_id(self):
            r"""str: The ID that should be associated with a client on the
            current machine. Defaults to the configuration entry
            ('services', 'client_id') if it is set and is generated otherwise.
            """
            global _client_id
            if _client_id is None:
                _client_id = str(uuid.uuid4())
            return _client_id

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
            request.setdefault('client_id', self.client_id)
            wait_for_complete = ((action in ['start', 'stop', 'shutdown'])
                                 and (service_type != RMQService))
            out = super(IntegrationServiceManager, self).send_request(request)
            if wait_for_complete and (out['status'] != 'complete'):
                def is_complete():
                    out.update(
                        super(IntegrationServiceManager, self).send_request(
                            request))
                    return (out['status'] == 'complete')
                wait_on_function(
                    is_complete, timeout=30, polling_interval=0.5,
                    on_timeout=f"Request did not complete: {request}")
            return out

        def setup_server(self, *args, **kwargs):
            r"""Set up the machinery for receiving requests."""
            super(IntegrationServiceManager, self).setup_server(*args, **kwargs)
            if service_type == FlaskService:
                @self.app.route('/')
                def landing_page():
                    from flask import render_template
                    import yaml
                    kwargs = {
                        'address': self.address,
                        'available': {
                            k: yaml.dump(v).splitlines()
                            for k, v in self.registry.registry.items()},
                        'running': {
                            k: {k2: v2.printStatus(return_str=True).splitlines()
                                for k2, v2 in v.items()}
                            for k, v in self.integrations.items()}}
                    out = render_template(
                        'service_manager_index.html', **kwargs)
                    return out
                
                from yggdrasil.communication import RESTComm
                RESTComm.add_comm_server_to_app(self.app)
            
        def stop_server(self):
            r"""Stop the server from the client-side."""
            assert(self.for_request)
            try:
                response = self.send_request(action='shutdown')
            except ClientError:  # pragma: debug
                return
            if response.get('pid', None):
                kill(response['pid'], _shutdown_signal)
            self.shutdown()

        def start_integration(self, client_id, x, yamls, **kwargs):
            r"""Start an integration if it is not already running.

            Args:
                client_id (str): ID associated with the client requesting the
                    integration be started.
                x (str, tuple): Hashable object that should be used to
                    identify the integration being started in the registry of
                    running integrations.
                yamls (list): Set of YAML specification files defining the
                    integration that should be run as as service.
                **kwargs: Additional keyword arguments are passed to get_runner.

            Returns:
                bool: True if the integration started, False otherwise.

            """
            integrations = self.integrations[client_id]
            stopped_integrations = self.stopped_integrations[client_id]
            if (x in integrations) and (not integrations[x].is_alive):
                if not self.stop_integration(client_id, x):
                    return False
            if x in stopped_integrations:
                if not self.stop_integration(client_id, x):
                    return False
                stopped_integrations.pop(x)
            if x not in integrations:
                partial_commtype = {'commtype': self.commtype}
                if self.commtype == 'rest':
                    partial_commtype['client_id'] = client_id
                integrations[x] = runner.get_runner(
                    yamls, complete_partial=True, as_service=True,
                    partial_commtype=partial_commtype, **kwargs)
                integrations[x].run(signal_handler=False)
            return True

        def _stop_integration(self, client_id, x):
            r"""Finish stopping an integration in a thread."""
            m = self.integrations[client_id].pop(x)
            if m.is_alive:
                m.terminate()
            m.atexit()

        def stop_integration(self, client_id, x):
            r"""Stop a running integration.

            Args:
                client_id (str): ID associated with the client requesting the
                    integration be stopped.
                x (str, tuple): Hashable object associated with the
                    integration service that should be stopped. If None,
                    all of the running integrations are stopped.

            Returns:
                bool: True if the integration has stopped.

            Raises:
                KeyError: If there is not a running integration associated
                    with the specified hashable object.

            """
            integrations = self.integrations[client_id]
            stopped_integrations = self.stopped_integrations[client_id]
            if x is None:
                return all(self.stop_integration(client_id, k)
                           for k in (list(integrations.keys())
                                     + list(stopped_integrations.keys())))
            if x in stopped_integrations:
                pass
            elif x not in integrations:
                raise KeyError(f"Integration defined by {x} not running")
            elif service_type == RMQService:
                self._stop_integration(client_id, x)
                return True
            else:
                mthread = threading.Thread(target=self._stop_integration,
                                           args=(client_id, x,), daemon=True)
                mthread.start()
                stopped_integrations[x] = mthread
            return not stopped_integrations[x].is_alive()

        def integration_info(self, client_id, x):
            r"""Get information about an integration and how to connect to it.

            Args:
                client_id (str): ID associated with the client requesting the
                    integration info.
                x (str, tuple): Hashable object associated with the
                    integration to get information on.

            Returns:
                dict: Information about the integration.

            Raises:
                KeyError: If there is not a running integration associated
                    with the specified hashable object.

            """
            integrations = self.integrations[client_id]
            if x not in integrations:  # pragma: debug
                raise KeyError(f"Integration defined by {x} not running")
            m = integrations[x].modeldrivers['dummy_model']
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
            if not super(IntegrationServiceManager, self).is_running:
                return False
            if self.for_request:
                try:
                    response = self.send_request(action='ping')
                    return response['status'] == 'running'
                except ClientError:
                    return False
            else:  # pragma: debug
                # This would only occur if a server calls is_running while it
                # is running (perhaps in a future callback?)
                return True

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
            client_id = None
            try:
                name = request.pop('name')
                action = request.pop('action')
                yamls = request.pop('yamls')
                client_id = request.pop('client_id')
                if client_id is not None:
                    self.integrations.setdefault(client_id, {})
                    self.stopped_integrations.setdefault(client_id, {})
                if isinstance(name, list):
                    name = tuple(name)
                if action == 'start':
                    if not yamls:
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
                    if self.start_integration(client_id, name, yamls,
                                              **request):
                        response = dict(
                            self.integration_info(client_id, name),
                            status='complete')
                    else:
                        response = {'status': 'starting'}
                elif action == 'stop':
                    if self.stop_integration(client_id, name):
                        response = {'status': 'complete'}
                    else:
                        response = {'status': 'stopping'}
                elif action == 'shutdown':
                    if self.stop_integration(client_id, None):
                        if self.is_app:  # pragma: no cover
                            response = {'status': 'complete'}
                        else:
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
                        if client_id is None:
                            clients = list(self.integrations.keys())
                        else:
                            clients = [client_id]
                        running_str = ''
                        for cli in clients:
                            running_str += '\tClient %s\n' % cli
                            for k, v in self.integrations[cli].items():
                                running_str += '\t\t%s:\n\t\t\t%s' % (
                                    k, '\n\t\t\t'.join(v.printStatus(
                                        return_str=True).splitlines()))
                        args = (self.address, registry_str, running_str)
                        response['status'] = fmt % args
                    else:
                        assert(client_id is not None)
                        response['status'] = (
                            self.integrations[client_id][name].printStatus(
                                return_str=True))
                elif action == 'ping':
                    response = {'status': 'running'}
                else:
                    raise RuntimeError(f"Unsupported action: '{action}'")
            except BaseException as e:
                tb = traceback.format_exc()
                response = {'error': str(e), 'traceback': tb}
                if action == 'start':  # pragma: intermittent
                    self.respond({'name': name, 'action': 'stop', 'yamls': None,
                                  'client_id': client_id})
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

    def add_from_repository(self, model_repository, directory=None):
        r"""Add integration services to the registry from a repository of
        model YAMLs.

        Args:
            model_repository (str): URL of directory in a Git repository
                containing YAMLs that should be added to the model registry.
            directory (str, optional): Directory where services from the
                model_repository should be cloned. Defaults to
                '~/.yggdrasil_service'.

        Returns:
            str: The directory where the repositories were cloned.

        """
        from yggdrasil.yamlfile import clone_github_repo, prep_yaml
        if directory is None:
            directory = os.path.expanduser(
                os.path.join('~', '.yggdrasil_services'))
        yaml_dir = clone_github_repo(model_repository,
                                     local_directory=directory)
        yaml_files = (glob.glob(os.path.join(yaml_dir, '*.yaml'))
                      + glob.glob(os.path.join(yaml_dir, '*.yml')))
        for x in yaml_files:
            # Calling prep_yaml allows the model repositories to be cloned
            # in advance to circumvent th hold place on git cloning on the
            # service manager (these models are assumed to be vetted so
            # they do not pose a security risk).
            prep_yaml(x, directory_for_clones=directory)
            self.add(os.path.splitext(os.path.basename(x))[0], x)
        return directory

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
            if (k in registry) and (registry[k] != v):
                old = pprint.pformat(registry[k])
                new = pprint.pformat(v)
                raise ValueError(f"There is an registry integration "
                                 f"associated with the name '{k}'. Remove "
                                 f"the registry entry before adding a new "
                                 f"one.\n"
                                 f"    Registry:\n{old}\n    New:\n{new}")
            registry[k] = v
        self.save(registry)


def validate_model_submission(fname):
    r"""Validate a YAML file according to the standards for submission to
    the yggdrasil model repository.

    Args:
        fname (str): YAML file to validate or directory in which to check
            each of the YAML files.

    """
    from yggdrasil import yamlfile, runner
    if isinstance(fname, list):
        for x in fname:
            validate_model_submission(x)
        return
    elif os.path.isdir(fname):
        files = sorted(glob.glob(os.path.join(fname, '*.yml'))
                       + glob.glob(os.path.join(fname, '*.yaml')))
        for x in files:
            validate_model_submission(x)
        return
    # 1-2. YAML syntax and schema
    yml = yamlfile.parse_yaml(fname, model_submission=True)
    # 3a. LICENSE
    repo_dir = yml['models'][0]['working_dir']
    patterns = ['LICENSE', 'LICENSE.*']
    for x in patterns:
        if ((glob.glob(os.path.join(repo_dir, x.upper()))
             or glob.glob(os.path.join(repo_dir, x.lower())))):
            break
    else:
        raise RuntimeError("Model repository does not contain a LICENSE file.")
    # 4. Run & validate
    runner.run(fname, validate=True)
