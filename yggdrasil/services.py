import os
import signal
import uuid
import json
import traceback
import threading
from yggdrasil import runner
from yggdrasil import platform
from yggdrasil.tools import sleep, TimeOut


class ClientError(BaseException):
    r"""Error raised by errors when calling the server from the client."""
    pass


class ServerError(BaseException):
    r"""Error raised when there was an error on the server."""
    pass


class ServiceBase(object):
    r"""Base class for sending/responding to service requests."""

    def __init__(self, name, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self.name = name
        self.for_request = kwargs.pop('for_request', False)
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
        r"""Process a request and return a response."""
        request = self.deserialize_request(request)
        response = self.respond(request, **kwargs)
        return self.serialize_response(response)

    def process_response(self, response):
        r"""Process a response."""
        return self.deserialize(response)

    def deserialize(self, msg):
        r"""Deserialize a message."""
        return json.loads(msg)

    def serialize(self, msg):
        r"""Serialize a message."""
        return json.dumps(msg)

    def deserialize_request(self, request):
        r"""Deserialize a request message."""
        return self.deserialize(request)

    def serialize_response(self, response):
        r"""Serialize a response message."""
        return self.serialize(response)

    def call(self, request, **kwargs):
        r"""Send a request."""
        raise NotImplementedError

    def send_request(self, request, **kwargs):
        r"""Send a request."""
        request_str = self.serialize(request)
        if not self.for_request:
            x = self.__class__(*self._args, **self._kwargs, for_request=True)
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

    def setup_server(self, *args, **kwargs):
        r"""Set up the machinery for receiving requests."""
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
        self.address = 'http://localhost:5000/' + self.name
        
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
        r"""Deserialize a message."""
        return msg  # should already be deserialized

    def serialize(self, msg):
        r"""Serialize a message."""
        return msg  # should already be serialized
    
    def serialize_response(self, response):
        r"""Serialize a response message."""
        return self.jsonify(response)

    def call(self, request, **kwargs):
        r"""Send a request."""
        import requests
        try:
            r = requests.post(self.address, json=request)
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
        self.url, self.exchange, self.queue = get_rmq_parameters(
            *args, **kwargs)
        self.queue = self.name
        # Unclear why using a non-default exchange prevents the server
        # from starting
        self.exchange = ''
        parameters = pika.URLParameters(self.url)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def setup_server(self, *args, **kwargs):
        r"""Set up the machinery for receiving requests."""
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
        r"""Set up the machinery for sending requests."""
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
        r"""Send a request."""
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


def create_model_manager_class(service_type=FlaskService):
    r"""Create a model manager service with the specified base.

    Args:
        service_type (ServiceBase, str, optional): Base class that should be
            used. Defaults to FlaskService.

    Returns:
        type: Subclass of ServiceBase to handle starting/stopping models
            running as services.

    """
    if isinstance(service_type, str):
        cls_map = {'flask': FlaskService, 'rmq': RMQService}
        service_type = cls_map[service_type]

    class ModelManager(service_type):
        r"""Manager to track running models."""

        def __init__(self, name=None, **kwargs):
            if name is None:
                name = 'ygg_models'
            self.models = {}
            super(ModelManager, self).__init__(name, **kwargs)

        def send_request(self, models=None, action='start', **kwargs):
            r"""Send a request.

            Args:
                models (list, str): One or more YAML files defining a set of
                    models to run as a service.
                action (str, optional): Action that is being requested.
                    Defaults to 'start'.
                **kwargs: Additional keyword arguments are passed to the call
                    method.

            """
            if not isinstance(models, (list, tuple, type(None))):
                models = [models]
            request = {'models': models,
                       'action': action}
            return super(ModelManager, self).send_request(request, **kwargs)

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

        def start_model(self, x):
            r"""Start a model integration."""
            if (x in self.models) and (not self.models[x].is_alive):
                self.stop_model(x)
            if x not in self.models:
                self.models[x] = runner.get_runner(list(x),
                                                   complete_partial=True)
                self.models[x].run(signal_handler=False)

        def stop_model(self, x):
            r"""Stop a model from running."""
            if x is None:
                for k in list(self.models.keys()):
                    self.stop_model(k)
                return
            if x not in self.models:
                raise KeyError(f"Integration defined by {x} not running")
            m = self.models.pop(x)
            m.terminate()
            m.atexit()

        def model_info(self, x):
            if x not in self.models:
                raise KeyError(f"Integration defined by {x} not running")
            m = self.models[x].modeldrivers['dummy_model']
            return m['instance'].connections

        @property
        def is_running(self):
            r"""bool: True if the server is running."""
            if not super(ModelManager, self).is_running:
                return False
            try:
                response = self.send_request(action='ping')
                return response['status'] == 'running'
            except ClientError:
                return False

        def respond(self, request, **kwargs):
            r"""Create a response to the request."""
            try:
                action = request['action']
                models = request['models']
                if isinstance(models, list):
                    models = tuple(models)
                if action == 'start':
                    if models is None:
                        raise RuntimeError("No model specified.")
                    self.start_model(models)
                    response = {'status': 'started'}
                    response.update(self.model_info(models))
                elif action == 'stop':
                    self.stop_model(models)
                    response = {'status': 'stopped'}
                elif action == 'shutdown':
                    self.stop_model(None)
                    tobj = threading.Timer(1, self.shutdown)
                    tobj.start()
                    response = {'status': 'shutting down',
                                'pid': os.getpid()}
                elif action == 'info':
                    response = {'status': 'done'}
                    if models is None:
                        response['models'] = list(self.models.keys())
                    else:
                        self.models[models].printStatus(return_str=True)
                elif action == 'ping':
                    response = {'status': 'running'}
                else:
                    raise RuntimeError(f"Unsupported action: '{action}'")
            except BaseException as e:
                tb = traceback.format_exc()
                response = {'error': str(e), 'traceback': tb}
            return response

        def process_response(self, response):
            r"""Process a response."""
            response = super(ModelManager, self).process_response(response)
            if 'error' in response:
                raise ServerError('%s\n%s' % (response['traceback'],
                                              response['error']))
            return response
            
    return ModelManager


def ModelManager(service_type=FlaskService, **kwargs):
    r"""Start a model management service to track running models.

    Args:
        service_type (ServiceBase, str, optional): Base class that should be
            used. Defaults to FlaskService.
        **kwargs: Additional keyword arguments are used to intialized the
            manager class instance.

    """
    cls = create_model_manager_class(service_type=service_type)
    return cls(**kwargs)


def start_model_manager(service_type=FlaskService, **kwargs):
    r"""Start a model management service to track running models.

    Args:
        service_type (ServiceBase, str, optional): Base class that should be
            used. Defaults to FlaskService.
        **kwargs: Additional keyword arguments are used to intialized the
            manager class instance.

    """
    x = ModelManager(service_type=FlaskService, **kwargs)
    x.run_server()
