import os
import uuid
import requests
from yggdrasil.communication import CommBase, NoMessages


def add_comm_server_to_app(app):
    r"""Add methods for handling send/receive calls server-side.

    Args:
        app (flask.Flask): Flask app to add methods to.

    """
    from flask import request
    app.queue = {}

    @app.route('/<client_id>/<model>/<channel>',
               methods=['GET', 'PUT', 'POST'])
    def queue(client_id, model, channel):
        r"""Respond to GET with queued message and add message from PUT
        or POST to the queue."""
        if request.method in ['PUT', 'POST']:
            # Queue a message when it is received from a client.
            app.queue.setdefault((client_id, model, channel), [])
            msg = request.get_data()
            app.queue[(client_id, model, channel)].append(msg)
            return b''
        else:
            # Return a message from the queue when requested by a client.
            if app.queue.get((client_id, model, channel), []):
                msg = app.queue[(client_id, model, channel)].pop(0)
                return msg
            else:
                return b''

    @app.route('/<client_id>/<model>/<channel>/size', methods=['GET'])
    def queue_size(client_id, model, channel):
        r"""Return the size of the message queue."""
        return str(len(app.queue.get((client_id, model, channel), [])))

    @app.route('/<client_id>/<model>/<channel>/purge', methods=['GET'])
    def queue_purge(client_id, model, channel):
        r"""Return the size of the message queue."""
        app.queue[(client_id, model, channel)] = []
        return b''

    @app.route('/<client_id>/<model>/<channel>/remove', methods=['GET'])
    def queue_remove(client_id, model, channel):
        r"""Remove a queue."""
        app.queue.pop((client_id, model, channel), None)
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
        'client_id': {'type': 'string'},
        'params': {'type': 'object'},
        'cookies': {'type': 'object'},
        'host': {'type': 'string', 'default': 'http://localhost:{port}'},
        'port': {'type': 'int'}}
    _maxMsgSize = 2048  # Based on limit for GET requests on most servers

    def __init__(self, *args, **kwargs):
        self._is_open = False
        super(RESTComm, self).__init__(*args, **kwargs)

    def atexit(self):  # pragma: debug
        r"""Close operations."""
        if self.direction == 'send':
            self.linger()
        super(RESTComm, self).atexit()
        
    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return self._is_open
    
    def open(self, *args, **kwargs):
        r"""Open the connection."""
        super(RESTComm, self).open(*args, **kwargs)
        self._is_open = True

    def bind(self, *args, **kwargs):
        r"""Bind to address based on information provided."""
        if self.address == 'address':
            client_id = self.client_id
            if client_id is None:
                client_id = str(uuid.uuid4()).split('-')[0]
            model = self.partner_model
            if model is None:
                model = str(uuid.uuid4()).split('-')[0]
            if self.port is None:
                self.port = int(os.environ.get("PORT", 5000))
            if not self.host.endswith('/'):
                self.host += '/'
            if '{port}' in self.host:
                self.host = self.host.format(port=self.port)
            host = self.host
            name = self.name_base
            assert(client_id is not None)
            self.address = f'{host}{client_id}/{model}/{name}'
        return super(RESTComm, self).bind(*args, **kwargs)

    def opp_comm_kwargs(self, for_yaml=False):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Args:
            for_yaml (bool, optional): If True, the returned dict will only
                contain values that can be specified in a YAML file. Defaults
                to False.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        from yggdrasil.services import _service_host_env
        out = super(RESTComm, self).opp_comm_kwargs(for_yaml=for_yaml)
        if _service_host_env in os.environ:
            out['host'] = os.environ[_service_host_env]
            out['address'] = out['address'].replace(self.host.rstrip('/'),
                                                    out['host'].rstrip('/'))
        else:
            out['host'] = self.host
        return out

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
        try:
            r = requests.get(
                self.address + '/size',
                params=self.params,
                cookies=self.cookies)
            r.raise_for_status()
            return int(r.content)
        except requests.exceptions.RequestException:  # pragma: debug
            return 0

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
