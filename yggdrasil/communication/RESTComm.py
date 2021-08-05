import uuid
import requests
from yggdrasil.communication import CommBase, NoMessages


def add_comm_server_to_app(app, send_callback=None,
                           recv_callback=None):
    r"""Add methods for handling send/receive calls server-side.

    Args:
        app (flask.Flask): Flask app to add methods to.
        send_callback (callable, optional): A function that should be
            called when the server receives a message sent by a comm.
            Defaults to None and is ignored.
        recv_callback (callable, optional): A function that should be
            called when the server responds to a receive request by a comm.
            Defaults to None and is ignored.

    """
    from flask import request
    app.queue = {}
    app.send_callback = send_callback
    app.recv_callback = recv_callback

    @app.route('/<model>/<channel>', methods=['GET', 'PUT', 'POST'])
    def queue(model, channel):
        r"""Respond to GET with queued message and add message from PUT
        or POST to the queue."""
        if request.method in ['PUT', 'POST']:
            # Queue a message when it is received from a client.
            app.queue.setdefault((model, channel), [])
            msg = request.get_data()
            app.queue[(model, channel)].append(msg)
            if app.send_callback is not None:
                app.send_callback(msg)
            return b''
        else:
            # Return a message from the queue when requested by a client.
            if app.queue.get((model, channel), []):
                msg = app.queue[(model, channel)].pop(0)
                if app.recv_callback is not None:
                    app.recv_callback(msg)
                return msg
            else:
                return b''

    @app.route('/<model>/<channel>/size', methods=['GET'])
    def queue_size(model, channel):
        r"""Return the size of the message queue."""
        return str(len(app.queue.get((model, channel), [])))

    @app.route('/<model>/<channel>/purge', methods=['GET'])
    def queue_purge(model, channel):
        r"""Return the size of the message queue."""
        app.queue[(model, channel)] = []
        return b''

    @app.route('/<model>/<channel>/remove', methods=['GET'])
    def queue_remove(model, channel):
        r"""Remove a queue."""
        app.queue.pop((model, channel), None)
        return b''


class RESTComm(CommBase.CommBase):
    r"""Class for handling I/O via a RESTful API. The provided address should
    be an HTTP address to a server running a flask app that has been equipped
    to respond to send/receive calls via the add_comm_server_to_app method.

    Args:
        params (dict, optional): Parameters that should be passed via URL.
            Defaults to None and is ignored.
        cookies (dict, optional): Cookies to send to the server. Defaults to
            None and is ignored.
        **kwargs: Additional keyword arguments will be passed to the base
            class.

    """

    _commtype = 'rest'
    _schema_subtype_description = 'RESTful API.'
    _schema_properties = {
        'params': {'type': 'object'},
        'cookies': {'type': 'object'}}
    _maxMsgSize = 2048  # Based on limit for GET requests on most servers

    def __init__(self, *args, **kwargs):
        self._is_open = False
        super(RESTComm, self).__init__(*args, **kwargs)

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self._is_open
    
    def open(self, *args, **kwargs):
        r"""Open the connection."""
        super(RESTComm, self).open(*args, **kwargs)
        self._is_open = True

    @classmethod
    def new_comm_kwargs(cls, name, host=None, **kwargs):
        r"""Initialize keywords for a new comm."""
        model = kwargs.get('partner_model', None)
        if model is None:
            model = str(uuid.uuid4()).split('-')[0]
        args = [name]
        if host is None:
            host = 'http://localhost:5000'
        if not host.endswith('/'):
            host += '/'
        if not kwargs.get('address', None):
            kwargs['address'] = f'{host}{model}/{name}'
        return args, kwargs

    def _close(self, *args, **kwargs):
        r"""Close the connection."""
        self._is_open = False
        r = requests.get(
            self.address + '/remove',
            params=self.params,
            cookies=self.cookies)
        r.raise_for_status()
        
    def _send(self, payload):
        r = requests.post(
            self.address,
            data=payload,
            params=self.params,
            cookies=self.cookies)
        r.raise_for_status()
        return True

    def _recv(self, **kwargs):
        r = requests.get(
            self.address,
            params=self.params,
            cookies=self.cookies)
        r.raise_for_status()
        msg = r.content
        if msg == b'':
            raise NoMessages("No messages queued on the server.")
        return (True, msg)

    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        r = requests.get(
            self.address + '/size',
            params=self.params,
            cookies=self.cookies)
        r.raise_for_status()
        return int(r.content)

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        return self.n_msg_recv

    def purge(self):
        r"""Purge all messages from the comm."""
        r = requests.get(
            self.address + '/purge',
            params=self.params,
            cookies=self.cookies)
        r.raise_for_status()
        self._n_sent = 0
        self._n_recv = 0
        self._last_send = None
        self._last_recv = None
