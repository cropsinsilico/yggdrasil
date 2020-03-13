import os
import copy
import uuid
import atexit
import threading
import logging
import types
import time
from yggdrasil.tests import assert_equal
from yggdrasil import tools
from yggdrasil.tools import YGG_MSG_EOF
from yggdrasil.communication import new_comm, get_comm, determine_suffix
from yggdrasil.components import import_component, create_component
from yggdrasil.metaschema.datatypes import MetaschemaTypeError
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.datatypes.JSONArrayMetaschemaType import (
    JSONArrayMetaschemaType)
from yggdrasil.metaschema.datatypes.JSONObjectMetaschemaType import (
    JSONObjectMetaschemaType)
from yggdrasil.communication.transforms.TransformBase import TransformBase


logger = logging.getLogger(__name__)
_registered_servers = dict()
_registered_comms = dict()
_server_lock = threading.RLock()
_registry_lock = threading.RLock()


def is_registered(comm_class, key):
    r"""Determine if a comm object has been registered under the specified key.
    
    Args:
        comm_class (str): Comm class to check for the key under.
        key (str): Key that should be checked.

    """
    with _registry_lock:
        global _registered_comms
        if comm_class not in _registered_comms:
            return False
        return (key in _registered_comms[comm_class])


def get_comm_registry(comm_class):
    r"""Get the comm registry for a comm class.

    Args:
        comm_class (str): Comm class to get registry for.

    Returns:
        dict: Dictionary of registered comm objects.

    """
    with _registry_lock:
        if comm_class is None:
            out = {}
        else:
            out = _registered_comms.get(comm_class, {})
    return out


def register_comm(comm_class, key, value):
    r"""Add a comm object to the global registry.

    Args:
        comm_class (str): Comm class to register the object under.
        key (str): Key that should be used to register the object.
        value (obj): Object being registered.

    """
    with _registry_lock:
        global _registered_comms
        if comm_class not in _registered_comms:
            _registered_comms[comm_class] = dict()
        if key not in _registered_comms[comm_class]:
            _registered_comms[comm_class][key] = value


def unregister_comm(comm_class, key, dont_close=False):
    r"""Remove a comm object from the global registry and close it.

    Args:
        comm_class (str): Comm class to check for key under.
        key (str): Key for object that should be removed from the registry.
        dont_close (bool, optional): If True, the comm will be removed from
            the registry, but it won't be closed. Defaults to False.

    Returns:
        bool: True if an object was closed.

    """
    with _registry_lock:
        global _registered_comms
        if comm_class not in _registered_comms:
            return False
        if key not in _registered_comms[comm_class]:
            return False
        value = _registered_comms[comm_class].pop(key)
        if dont_close:
            return False
        out = import_component('comm', comm_class).close_registry_entry(value)
        del value
    return out


def cleanup_comms(comm_class, close_func=None):
    r"""Clean up comms of a certain type.

    Args:
        comm_class (str): Comm class that should be cleaned up.

    Returns:
        int: Number of comms closed.

    """
    count = 0
    if comm_class is None:
        return count
    with _registry_lock:
        global _registered_comms
        if comm_class in _registered_comms:
            keys = [k for k in _registered_comms[comm_class].keys()]
            for k in keys:
                flag = unregister_comm(comm_class, k)
                if flag:  # pragma: debug
                    count += 1
    return count


class CommThreadLoop(tools.YggThreadLoop):
    r"""Thread loop for comms to ensure cleanup.

    Args:
        comm (:class:.CommBase): Comm class that thread is for.
        name (str, optional): Name for the thread. If not provided, one is
            created by combining the comm name and the provided suffix.
        suffix (str, optional): Suffix that should be added to comm name to name
            the thread. Defaults to 'CommThread'.
        **kwargs: Additional keyword arguments are passed to the parent class.

    Attributes:
        comm (:class:.CommBase): Comm class that thread is for.

    """
    def __init__(self, comm, name=None, suffix='CommThread', **kwargs):
        self.comm = comm
        if name is None:
            name = '%s.%s' % (comm.name, suffix)
        super(CommThreadLoop, self).__init__(name=name, **kwargs)

    def on_main_terminated(self):  # pragma: debug
        r"""Actions taken on the backlog thread when the main thread stops."""
        self.debug('is_interface = %s, direction = %s',
                   self.comm.is_interface, self.comm.direction)
        if self.comm.is_interface:
            self.debug('_1st_main_terminated = %s', str(self._1st_main_terminated))
            if self.comm.direction == 'send':
                self._1st_main_terminated = True
                self.comm.send_eof()
                self.comm.close_in_thread(no_wait=True)
                self.debug("Close in thread, closed = %s, nmsg = %d",
                           self.comm.is_closed, self.comm.n_msg)
                return
        super(CommThreadLoop, self).on_main_terminated()


class CommServer(tools.YggThreadLoop):
    r"""Basic server object to keep track of clients.

    Attributes:
        cli_count (int): Number of clients that have connected to this server.

    """
    def __init__(self, srv_address, cli_address=None, **kwargs):
        global _registered_servers
        self.cli_count = 0
        if cli_address is None:
            cli_address = srv_address
        self.srv_address = srv_address
        self.cli_address = cli_address
        super(CommServer, self).__init__('CommServer.%s' % srv_address, **kwargs)
        _registered_servers[self.srv_address] = self

    def add_client(self):
        r"""Increment the client count."""
        global _registered_servers
        _registered_servers[self.srv_address].cli_count += 1
        self.debug("Added client to server: nclients = %d", self.cli_count)

    def remove_client(self):
        r"""Decrement the client count, closing the server if all clients done."""
        global _registered_servers
        self.debug("Removing client from server")
        _registered_servers[self.srv_address].cli_count -= 1
        if _registered_servers[self.srv_address].cli_count <= 0:
            self.debug("Shutting down server")
            self.terminate()
            _registered_servers.pop(self.srv_address)


class CommBase(tools.YggClass):
    r"""Class for handling I/O.

    Args:
        name (str): The environment variable where communication address is
            stored.
        address (str, optional): Communication info. Default to None and
            address is taken from the environment variable.
        direction (str, optional): The direction that messages should flow
            through the connection. 'send' if the connection will send
            messages, 'recv' if the connecton will receive messages. Defaults
            to 'send'.
        is_interface (bool, optional): Set to True if this comm is a Python
            interface binding. Defaults to False.
        language (str, optional): Programming language of the calling model.
            Defaults to 'python'.
        partner_language (str, optional): Programming language of this comm's
            partner comm. Defaults to 'python'.
        datatype (schema, optional): JSON schema (with expanded core types
            defined by |yggdrasil|) that constrains the type of data that
            should be sent/received by this object. Defaults to {'type': 'bytes'}.
            Additional information on specifying datatypes can be found
            :ref:`here <datatypes_rst>`.
        field_names (list, optional): [DEPRECATED] Field names that should be
            used to label fields in sent/received tables. This keyword is only
            valid for table-like datatypes. If not provided, field names are
            created based on the field order.
        field_units (list, optional): [DEPRECATED] Field units that should be
            used to convert fields in sent/received tables. This keyword is only
            valid for table-like datatypes. If not provided, all fields are
            assumed to be unitless.
        as_array (bool, optional): [DEPRECATED] If True and the datatype is
            table-like, tables are sent/recieved with either columns rather
            than row by row. Defaults to False.
        serializer (:class:.DefaultSerialize, optional): Class with serialize and
            deserialize methods that should be used to process sent and received
            messages. Defaults to None and is constructed using provided
            'serializer_kwargs'.
        serializer_kwargs (dict, optional): Keyword arguments that should be
            passed to :class:.DefaultSerialize to create serializer. Defaults to {}.
        format_str (str, optional): String that should be used to format/parse
            messages. Default to None.
        dont_open (bool, optional): If True, the connection will not be opened.
            Defaults to False.
        is_interface (bool, optional): Set to True if this comm is a Python
            interface binding. Defaults to False.
        recv_timeout (float, optional): Time that should be waited for an
            incoming message before returning None. Defaults to 0 (no wait). A
            value of False indicates that recv should block.
        close_on_eof_recv (bool, optional): If True, the comm will be closed
            when it receives an end-of-file messages. Otherwise, it will remain
            open. Defaults to True.
        close_on_eof_send (bool, optional): If True, the comm will be closed
            after it sends an end-of-file messages. Otherwise, it will remain
            open. Defaults to False.
        single_use (bool, optional): If True, the comm will only be used to
            send/recv a single message. Defaults to False.
        reverse_names (bool, optional): If True, the suffix added to the comm
            with be reversed. Defaults to False.
        no_suffix (bool, optional): If True, no directional suffix will be added
            to the comm name. Defaults to False.
        is_client (bool, optional): If True, the comm is one of many potential
            clients that will be sending messages to one or more servers.
            Defaults to False.
        is_response_client (bool, optional): If True, the comm is a client-side
            response comm. Defaults to False.
        is_server (bool, optional): If True, the commis one of many potential
            servers that will be receiving messages from one or more clients.
            Defaults to False.
        is_response_server (bool, optional): If True, the comm is a server-side
            response comm. Defaults to False.
        recv_converter (func, optional): Converter that should be used on
            received objects. Defaults to None.
        send_converter (func, optional): Converter that should be used on
            sent objects. Defaults to None.
        vars (list, optional): Names of variables to be sent/received by
            this comm. Defaults to [].
        length_map (dict, optional): Map from pointer variable names to

            the names of variables where their length will be stored.
            Defaults to {}.
        comm (str, optional): The comm that should be created. This only serves
            as a check that the correct class is being created. Defaults to None.
        filter (:class:.FilterBase, optional): Callable class that will be used to
            determine when messages should be sent/received. Defaults to None
            and is ignored.
        transform (:class:.TransformBase, optional): Callable class that will be
            used to transform messages that are sent/received. Defaults to None
            and is ignored.
        is_default (bool, optional): If True, this comm was created to handle
            all input/output variables to/from a model. Defaults to False. This
            variable is used internally and should not be set explicitly in
            the YAML.
        outside_loop (bool, optional): If True, and the comm is an
            input/outputs to/from a model being wrapped. The receive/send
            calls for this comm will be outside the loop for the model.
            Defaults to False.
        **kwargs: Additional keywords arguments are passed to parent class.

    Class Attributes:
        is_file (bool): True if the comm accesses a file.
        _maxMsgSize (int): Maximum size of a single message that should be sent.
        address_description (str): Description of the information constituting
            an address for this communication mechanism.

    Attributes:
        name (str): The environment variable where communication address is
            stored.
        address (str): Communication info.
        direction (str): The direction that messages should flow through the
            connection.
        is_interface (bool): True if this comm is a Python interface binding.
        language (str): Language that this comm is being called from.
        partner_language (str): Programming language of this comm's partner comm.
        serializer (:class:.DefaultSerialize): Object that will be used to
            serialize/deserialize messages to/from python objects.
        recv_timeout (float): Time that should be waited for an incoming
            message before returning None.
        close_on_eof_recv (bool): If True, the comm will be closed when it
            receives an end-of-file messages. Otherwise, it will remain open.
        close_on_eof_send (bool): If True, the comm will be closed after it
            sends an end-of-file messages. Otherwise, it will remain open.
        single_use (bool): If True, the comm will only be used to send/recv a
            single message.
        is_client (bool): If True, the comm is one of many potential clients
            that will be sending messages to one or more servers.
        is_response_client (bool): If True, the comm is a client-side response
            comm.
        is_server (bool): If True, the comm is one of many potential servers
            that will be receiving messages from one or more clients.
        is_response_server (bool): If True, the comm is a server-side response
            comm.
        recv_converter (func): Converter that should be used on received objects.
        send_converter (func): Converter that should be used on sent objects.
        filter (:class:.FilterBase): Callable class that will be used to determine when
            messages should be sent/received.

    Raises:
        RuntimeError: If the comm class is not installed.
        RuntimeError: If there is not an environment variable with the specified
            name.
        ValueError: If directions is not 'send' or 'recv'.

    """

    _commtype = None
    _schema_type = 'comm'
    _schema_subtype_key = 'commtype'
    _schema_required = ['name', 'commtype', 'datatype']
    _schema_properties = {'name': {'type': 'string'},
                          'commtype': {'type': 'string', 'default': 'default',
                                       'description': ('Communication mechanism '
                                                       'that should be used.')},
                          'datatype': {'type': 'schema',
                                       'default': {'type': 'bytes'}},
                          'recv_converter': {'anyOf': [
                              {'$ref': '#/definitions/transform'},
                              {'type': ['function', 'string']},
                              {'type': 'array',
                               'items': {'anyOf': [
                                   {'$ref': '#/definitions/transform'},
                                   {'type': ['function', 'string']}]}}]},
                          'send_converter': {'anyOf': [
                              {'$ref': '#/definitions/transform'},
                              {'type': ['function', 'string']},
                              {'type': 'array',
                               'items': {'anyOf': [
                                   {'$ref': '#/definitions/transform'},
                                   {'type': ['function', 'string']}]}}]},
                          'vars': {'type': 'array',
                                   'items': {'type': 'string'}},
                          'length_map': {
                              'type': 'object',
                              'additionalProperties': {'type': 'string'}},
                          'format_str': {'type': 'string'},
                          'field_names': {'type': 'array',
                                          'items': {'type': 'string'}},
                          'field_units': {'type': 'array',
                                          'items': {'type': 'string'}},
                          'as_array': {'type': 'boolean', 'default': False},
                          'filter': {'$ref': '#/definitions/filter'},
                          'transform': {'anyOf': [
                              {'$ref': '#/definitions/transform'},
                              {'type': ['function', 'string']},
                              {'type': 'array',
                               'items': {'anyOf': [
                                   {'$ref': '#/definitions/transform'},
                                   {'type': ['function', 'string']}]}}]},
                          'is_default': {'type': 'boolean', 'default': False},
                          'outside_loop': {'type': 'boolean',
                                           'default': False},
                          'default_file': {'$ref': '#/definitions/file'}}
    _schema_excluded_from_class = ['name']
    _default_serializer = 'default'
    _default_serializer_class = None
    _schema_excluded_from_class_validation = ['datatype']
    is_file = False
    _maxMsgSize = 0
    address_description = None
    no_serialization = False
    _model_schema_prop = ['is_default', 'outside_loop', 'default_file']

    def __init__(self, name, address=None, direction='send', dont_open=False,
                 is_interface=None, language=None, partner_language='python',
                 recv_timeout=0.0, close_on_eof_recv=True, close_on_eof_send=False,
                 single_use=False, reverse_names=False, no_suffix=False,
                 is_client=False, is_response_client=False,
                 is_server=False, is_response_server=False,
                 comm=None, **kwargs):
        self._comm_class = None
        if comm is not None:
            assert(comm == self.comm_class)
        if isinstance(kwargs.get('datatype', None), MetaschemaType):
            self.datatype = kwargs.pop('datatype')
        super(CommBase, self).__init__(name, **kwargs)
        if not self.__class__.is_installed(language='python'):
            raise RuntimeError("Comm class %s not installed" % self.__class__)
        suffix = determine_suffix(no_suffix=no_suffix,
                                  reverse_names=reverse_names,
                                  direction=direction)
        self.name_base = name
        self.suffix = suffix
        self._name = name + suffix
        if address is None:
            if self.name not in os.environ:
                model_name = os.environ.get('YGG_MODEL_NAME', '')
                prefix = '%s:' % model_name
                if model_name and (not self.name.startswith(prefix)):
                    self._name = prefix + self.name
                if self.name not in os.environ:
                    raise RuntimeError('Cannot see %s in env.' % self.name)
            self.address = os.environ[self.name]
        else:
            self.address = address
        self.direction = direction
        if is_interface is None:
            is_interface = False  # tools.is_subprocess()
        self.is_interface = is_interface
        if self.is_interface:
            # All models connect to python connection drivers
            partner_language = 'python'
            recv_timeout = False
        if language is None:
            language = 'python'
        self.language = language
        self.partner_language = partner_language
        self.partner_language_driver = None
        if partner_language:
            self.partner_language_driver = import_component(
                'model', self.partner_language)
        self.language_driver = import_component('model', self.language)
        self.is_client = is_client
        self.is_server = is_server
        self.is_response_client = is_response_client
        self.is_response_server = is_response_server
        self._server = None
        self.recv_timeout = recv_timeout
        self.close_on_eof_recv = close_on_eof_recv
        self.close_on_eof_send = close_on_eof_send
        self._last_header = None
        self._work_comms = {}
        self.single_use = single_use
        self._used = False
        self._multiple_first_send = True
        self._n_sent = 0
        self._n_recv = 0
        self._bound = False
        self._last_send = None
        self._last_recv = None
        self._type_errors = []
        self._timeout_drain = False
        self._server_class = CommServer
        self._server_kwargs = {}
        self._send_serializer = True
        if self.single_use and (not self.is_response_server):
            self._send_serializer = False
        # Add interface tag
        if self.is_interface:
            self._name += '_I'
        # if self.is_interface:
        #     self._timeout_drain = False
        # else:
        #     self._timeout_drain = self.timeout
        self._closing_event = threading.Event()
        self._closing_thread = tools.YggThread(target=self.linger_close,
                                               name=self.name + '.ClosingThread')
        self._eof_recv = threading.Event()
        self._eof_sent = threading.Event()
        self._field_backlog = dict()
        if self.single_use:
            self._eof_recv.set()
            self._eof_sent.set()
        if self.is_response_client or self.is_response_server:
            self._eof_sent.set()  # Don't send EOF, these are single use
        if self.is_interface:
            atexit.register(self.atexit)
        self._init_before_open(**kwargs)
        if dont_open:
            self.bind()
        else:
            self.open()

    def _init_before_open(self, **kwargs):
        r"""Initialization steps that should be performed after base class, but
        before the comm is opened."""
        seri_cls = kwargs.pop('serializer_class', None)
        seri_kws = kwargs.pop('serializer_kwargs', {})
        if ('datatype' in self._schema_properties) and (self.datatype is not None):
            seri_kws.setdefault('datatype', self.datatype)
        if ((('serializer' not in self._schema_properties)
             and (not hasattr(self, 'serializer')))):
            self.serializer = self._default_serializer
        if isinstance(self.serializer, str):
            seri_kws.setdefault('seritype', self.serializer)
            self.serializer = None
        elif isinstance(self.serializer, dict):
            seri_kws.update(self.serializer)
            self.serializer = None
        # Only update serializer if not already set
        if self.serializer is None:
            # Get serializer class
            if seri_cls is None:
                if (((seri_kws['seritype'] == self._default_serializer)
                     and (self._default_serializer_class is not None))):
                    seri_cls = self._default_serializer_class
                else:
                    seri_cls = import_component('serializer',
                                                subtype=seri_kws['seritype'])
            # Recover keyword arguments for serializer passed to comm class
            for k in seri_cls.seri_kws():
                if k in kwargs:
                    seri_kws.setdefault(k, kwargs[k])
            # Create serializer instance
            self.debug('seri_kws = %s', str(seri_kws))
            self.serializer = seri_cls(**seri_kws)
        # Set send/recv converter based on the serializer
        dir_conv = '%s_converter' % self.direction
        if getattr(self, 'transform', []):
            assert(not getattr(self, dir_conv, []))
            # setattr(self, dir_conv, self.transform)
        elif getattr(self, dir_conv, []):
            self.transform = getattr(self, dir_conv)
        else:
            self.transform = getattr(self.serializer, dir_conv, [])
        if self.transform:
            if not isinstance(self.transform, list):
                self.transform = [self.transform]
            for i, iv in enumerate(self.transform):
                if isinstance(iv, str):
                    cls_conv = getattr(self.language_driver, dir_conv + 's')
                    iv = cls_conv.get(iv, iv)
                if isinstance(iv, str):
                    try:
                        iv = create_component('transform', subtype=iv)
                    except ValueError:
                        iv = None
                elif isinstance(iv, dict):
                    from yggdrasil.schema import get_schema
                    transform_schema = get_schema().get('transform')
                    transform_kws = dict(
                        iv,
                        subtype=transform_schema.identify_subtype(iv))
                    iv = create_component('transform', **transform_kws)
                elif isinstance(iv, TransformBase):
                    pass
                elif ((isinstance(iv, (types.BuiltinFunctionType, types.FunctionType,
                                       types.BuiltinMethodType, types.MethodType))
                       or hasattr(iv, '__call__'))):  # pragma: matlab
                    iv = create_component('transform', subtype='function',
                                          function=iv)
                else:  # pragma: debug
                    raise TypeError("Unsupported transform type: '%s'" % type(iv))
                self.transform[i] = iv
        self.transform = [x for x in self.transform if x]
        # Set filter
        if isinstance(self.filter, dict):
            from yggdrasil.schema import get_schema
            filter_schema = get_schema().get('filter')
            filter_kws = dict(self.filter,
                              subtype=filter_schema.identify_subtype(self.filter))
            self.filter = create_component('filter', **filter_kws)

    @staticmethod
    def before_registration(cls):
        r"""Operations that should be performed to modify class attributes prior
        to registration."""
        tools.YggClass.before_registration(cls)
        cls._default_serializer_class = import_component('serializer',
                                                         cls._default_serializer,
                                                         without_schema=True)
        
    @classmethod
    def get_testing_options(cls, serializer=None, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Args:
            serializer (str, optional): The name of the serializer that should
                be used. If not provided, the _default_serializer class
                attribute will be used.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for comms tested with the
                    provided content.
                send (list): List of objects to send to test file.
                recv (list): List of objects that will be received from a test
                    file that was sent the messages in 'send'.
                contents (bytes): Bytes contents of test file created by sending
                    the messages in 'send'.

        """
        if serializer is None:
            serializer = cls._default_serializer
        if (((serializer == cls._default_serializer)
             and (cls._default_serializer_class is not None))):
            seri_cls = cls._default_serializer_class
        else:
            seri_cls = import_component('serializer', serializer)
        out_seri = seri_cls.get_testing_options(**kwargs)
        out = {'kwargs': out_seri['kwargs'],
               'send': copy.deepcopy(out_seri['objects']),
               'msg': out_seri['objects'][0],
               'contents': out_seri['contents'],
               'objects': out_seri['objects']}
        out['recv'] = copy.deepcopy(out['send'])
        out['dict'] = seri_cls.object2dict(out['msg'], **out['kwargs'])
        if not out_seri.get('exact_contents', True):
            out['exact_contents'] = False
        msg_array = seri_cls.object2array(out['msg'], **out['kwargs'])
        if msg_array is not None:
            out['msg_array'] = msg_array
        if isinstance(out['msg'], bytes):
            out['msg_long'] = out['msg'] + (cls._maxMsgSize * b'0')
        else:
            out['msg_long'] = out['msg']
        for k in ['field_names', 'field_units']:
            if k in out_seri:
                out[k] = copy.deepcopy(out_seri[k])
        return out

    def get_status_message(self, nindent=0, extra_lines=None):
        r"""Return lines composing a status message.
        
        Args:
            nindent (int, optional): Number of tabs that should be used to
                indent each line. Defaults to 0.
            extra_lines (list, optional): Additional lines that should be
                added to the beginning of the default print message. Defaults to
                empty list if not provided.
                
        Returns:
            tuple(list, prefix): Lines composing the status message and the
                prefix string used for the last message.

        """
        if extra_lines is None:
            extra_lines = []
        prefix = nindent * '\t'
        lines = ['', '%s%s:' % (prefix, self.name)]
        prefix += '\t'
        lines += ['%s%s' % (prefix, x) for x in extra_lines]
        lines += ['%s%-15s: %s' % (prefix, 'address', self.address),
                  '%s%-15s: %s' % (prefix, 'direction', self.direction),
                  '%s%-15s: %s' % (prefix, 'open', self.is_open),
                  '%s%-15s: %s' % (prefix, 'nsent', self._n_sent),
                  '%s%-15s: %s' % (prefix, 'nrecv', self._n_recv)]
        return lines, prefix

    def printStatus(self, *args, **kwargs):
        r"""Print status of the communicator."""
        lines, _ = self.get_status_message(*args, **kwargs)
        self.info('\n'.join(lines))

    @classmethod
    def is_installed(cls, language=None):
        r"""Determine if the necessary libraries are installed for this
        communication class.

        Args:
            language (str, optional): Specific language that should be checked
                for compatibility. Defaults to None and all languages supported
                on the current platform will be checked. If set to 'any', the
                result will be True if this comm is installed for any of the
                supported languages.

        Returns:
            bool: Is the comm installed.

        """
        lang_list = tools.get_supported_lang()
        comm_class = str(cls).split("'")[1].split(".")[-1]
        use_any = False
        if language in [None, 'all']:
            language = lang_list
        elif language == 'any':
            use_any = True
            language = lang_list
        if isinstance(language, list):
            out = (not use_any)
            for l in language:
                if not cls.is_installed(language=l):
                    if not use_any:
                        out = False
                        break
                elif use_any:
                    out = True
                    break
        else:
            if comm_class in ['CommBase', 'AsyncComm', 'ForkComm',
                              'ErrorClass']:
                out = (language in lang_list)
            else:
                # Check driver
                try:
                    drv = import_component('model', language)
                    out = drv.is_comm_installed(commtype=cls._commtype)
                except ValueError:
                    out = False
        return out

    @property
    def maxMsgSize(self):
        r"""int: Maximum size of a single message that should be sent."""
        return self._maxMsgSize

    @property
    def empty_bytes_msg(self):
        r"""str: Empty serialized message."""
        return b''
        
    @property
    def comm_class(self):
        r"""str: Name of communication class."""
        # TODO: Change this to return self._commtype
        if self._comm_class is None:
            if getattr(self, '_is_error_class', False):
                name_cls = self.__class__.__bases__[0]
            else:
                name_cls = self.__class__
            self._comm_class = str(name_cls).split("'")[1].split(".")[-1]
        return self._comm_class

    @classmethod
    def underlying_comm_class(self):
        r"""str: Name of underlying communication class."""
        return None

    @classmethod
    def close_registry_entry(cls, value):
        r"""Close a registry entry."""
        return False

    @classmethod
    def cleanup_comms(cls):
        r"""Cleanup registered comms of this class."""
        return cleanup_comms(cls.underlying_comm_class())

    @classmethod
    def comm_registry(cls):
        r"""dict: Registry of comms of this class."""
        return get_comm_registry(cls.underlying_comm_class())

    def register_comm(self, key, value):
        r"""Register a comm."""
        self.debug("Registering %s comm: %s", self.comm_class, key)
        register_comm(self.comm_class, key, value)

    def unregister_comm(self, key, dont_close=False):
        r"""Unregister a comm."""
        self.debug("Unregistering %s comm: %s (dont_close = %s)",
                   self.comm_class, key, dont_close)
        unregister_comm(self.comm_class, key, dont_close=dont_close)

    @classmethod
    def comm_count(cls):
        r"""int: Number of communication connections."""
        out = len(cls.comm_registry())
        if out > 0:
            logger.info('There are %d %s comms: %s',
                        len(cls.comm_registry()), cls.__name__,
                        [k for k in cls.comm_registry().keys()])
        return out

    @classmethod
    def new_comm_kwargs(cls, *args, **kwargs):
        r"""Get keyword arguments for new comm."""
        kwargs.setdefault('address', 'address')
        return args, kwargs

    @classmethod
    def new_comm(cls, name, *args, **kwargs):
        r"""Initialize communication with new queue."""
        dont_create = kwargs.pop('dont_create', False)
        env = kwargs.get('env', {})
        if name in env:
            kwargs.setdefault('address', env[name])
        elif name in os.environ:
            kwargs.setdefault('address', os.environ[name])
        new_comm_class = kwargs.pop('new_comm_class', None)
        if dont_create:
            args = tuple([name] + list(args))
        else:
            args, kwargs = cls.new_comm_kwargs(name, *args, **kwargs)
        if new_comm_class is not None:
            new_cls = import_component('comm', new_comm_class)
            return new_cls(*args, **kwargs)
        return cls(*args, **kwargs)

    @property
    def opp_address(self):
        r"""str: Address for opposite comm."""
        return self.address

    @property
    def opp_comms(self):
        r"""dict: Name/address pairs for opposite comms."""
        return {self.name: self.opp_address}

    def opp_comm_kwargs(self):
        r"""Get keyword arguments to initialize communication with opposite
        comm object.

        Returns:
            dict: Keyword arguments for opposite comm object.

        """
        kwargs = {'comm': self.comm_class}
        kwargs['address'] = self.opp_address
        kwargs['serializer'] = self.serializer
        if self.direction == 'send':
            kwargs['direction'] = 'recv'
        else:
            kwargs['direction'] = 'send'
        kwargs.update(self.serializer.input_kwargs)
        return kwargs

    def bind(self):
        r"""Bind in place of open."""
        if self.is_client:
            self.signon_to_server()

    def open(self):
        r"""Open the connection."""
        self.bind()

    def _close(self, *args, **kwargs):
        r"""Close the connection."""
        pass

    def close(self, linger=False):
        r"""Close the connection.

        Args:
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        self.debug('')
        if linger and self.is_open:
            self.linger()
        else:
            self._closing_thread.set_terminated_flag()
            linger = False
        # Close with lock
        with self._closing_thread.lock:
            self._close(linger=linger)
            self._n_sent = 0
            self._n_recv = 0
            if self.is_client:
                self.debug("Signing off from server")
                self.signoff_from_server()
            if len(self._work_comms) > 0:
                self.debug(
                    "Cleaning up %d work comms", len(self._work_comms))
                keys = [k for k in self._work_comms.keys()]
                for c in keys:
                    self.remove_work_comm(c, linger=linger)
                self.debug("Finished cleaning up work comms")
        self.debug("done")

    def close_in_thread(self, no_wait=False, timeout=None):
        r"""In a new thread, close the comm when it is empty.

        Args:
            no_wait (bool, optional): If True, don't wait for closing thread
                to stop.
            timeout (float, optional): Time that should be waited for the comm
                to close. Defaults to None and is set to self.timeout. If False,
                this will block until the comm is closed.

        """
        if self.language_driver.comm_linger:  # pragma: matlab
            self.linger_close()
            self._closing_thread.set_terminated_flag()
        self.debug("current_thread = %s", threading.current_thread().name)
        try:
            self._closing_thread.start()
            _started_thread = True
        except RuntimeError:  # pragma: debug
            _started_thread = False
        if self._closing_thread.was_started and (not no_wait):  # pragma: debug
            self._closing_thread.wait(key=str(uuid.uuid4()), timeout=timeout)
            if _started_thread and not self._closing_thread.was_terminated:
                self.debug("Closing thread took too long")
                self.close()

    def linger_close(self):
        r"""Wait for messages to drain, then close."""
        self.close(linger=True)

    def linger(self):
        r"""Wait for messages to drain."""
        self.debug('')
        if self.direction == 'recv':
            self.wait_for_confirm(timeout=self._timeout_drain)
        else:
            self.drain_messages(variable='n_msg_send')
            self.wait_for_confirm(timeout=self._timeout_drain)
        self.debug("Finished (timeout_drain = %s)", str(self._timeout_drain))

    def language_atexit(self):  # pragma: debug
        r"""Close operations specific to the language."""
        if self.language_driver.comm_atexit is not None:
            self.language_driver.comm_atexit(self)

    def atexit(self):  # pragma: debug
        r"""Close operations."""
        self.debug('atexit begins')
        self.language_atexit()
        self.debug('atexit after language_atexit, but before close')
        self.close()
        self.debug(
            'atexit finished: closed=%s, n_msg=%d, close_alive=%s',
            self.is_closed, self.n_msg,
            self._closing_thread.is_alive())

    @property
    def is_open(self):
        r"""bool: True if the connection is open."""
        return False

    @property
    def is_closed(self):
        r"""bool: True if the connection is closed."""
        return (not self.is_open)

    @property
    def is_confirmed_send(self):
        r"""bool: True if all sent messages have been confirmed."""
        return True

    @property
    def is_confirmed_recv(self):
        r"""bool: True if all received messages have been confirmed."""
        return True

    @property
    def is_confirmed(self):
        r"""bool: True if all messages have been confirmed."""
        if self.direction == 'recv':
            return self.is_confirmed_recv
        else:
            return self.is_confirmed_send

    def wait_for_confirm(self, timeout=None, direction=None,
                         active_confirm=False, noblock=False):
        r"""Sleep until all messages are confirmed."""
        self.debug('')
        if direction is None:
            direction = self.direction
        T = self.start_timeout(t=timeout, key_suffix='.wait_for_confirm')
        flag = False
        while (not T.is_out) and (not getattr(self, 'is_confirmed_%s' % direction)):
            if active_confirm:
                flag = self.confirm(direction=direction, noblock=noblock)
                if flag:
                    break
            self.sleep()
        self.stop_timeout(key_suffix='.wait_for_confirm')
        if not flag:
            flag = getattr(self, 'is_confirmed_%s' % direction)
        self.debug('Done confirming')
        return flag

    def confirm(self, direction=None, noblock=False):
        r"""Confirm message."""
        if direction is None:
            direction = self.direction
        if direction == 'send':
            out = self.confirm_send(noblock=noblock)
        else:
            out = self.confirm_recv(noblock=noblock)
        return out

    def confirm_send(self, noblock=False):
        r"""Confirm that sent message was received."""
        return noblock

    def confirm_recv(self, noblock=False):
        r"""Confirm that message was received."""
        return noblock

    @property
    def n_msg(self):
        r"""int: The number of messages in the connection."""
        if self.direction == 'recv':
            return self.n_msg_recv
        else:
            return self.n_msg_send

    @property
    def n_msg_recv(self):
        r"""int: The number of incoming messages in the connection."""
        return 0

    @property
    def n_msg_send(self):
        r"""int: The number of outgoing messages in the connection."""
        return 0

    @property
    def n_msg_recv_drain(self):
        r"""int: The number of incoming messages in the connection to drain."""
        return self.n_msg_recv

    @property
    def n_msg_send_drain(self):
        r"""int: The number of outgoing messages in the connection to drain."""
        return self.n_msg_send

    @property
    def eof_msg(self):
        r"""str: Message indicating EOF."""
        return YGG_MSG_EOF

    def is_eof(self, msg):
        r"""Determine if a message is an EOF.

        Args:
            msg (obj): Message object to be tested.

        Returns:
            bool: True if the message indicates an EOF, False otherwise.

        """
        out = (isinstance(msg, bytes) and (msg == self.eof_msg))
        return out

    def apply_transform(self, msg_in):
        r"""Evaluate the transform to alter the emssage being sent/received.

        Args:
            msg_in (object): Message being transformed.

        Returns:
            object: Transformed message.

        """
        if not self.transform:
            return msg_in
        self.debug("Applying transformations to message being %s."
                   % self.direction)
        # If receiving, update the expected datatypes to use information
        # about the received datatype that was recorded by the serializer
        if (((self.direction == 'recv')
             and self.serializer.initialized
             and (not self.transform[0].original_datatype))):
            typedef = self.serializer.typedef
            for iconv in self.transform:
                if not iconv.original_datatype:
                    iconv.set_original_datatype(typedef)
                typedef = iconv.transformed_datatype
        # Actual conversion
        msg_out = msg_in
        no_init = ((self.direction == 'recv')
                   and (not self.serializer.initialized))
        for iconv in self.transform:
            msg_out = iconv(msg_out, no_init=no_init)
        return msg_out

    def evaluate_filter(self, *msg_in):
        r"""Evaluate the filter to determine how the message should be
        handled.

        Args:
            *msg_in (object): Parts of message being evaluated.
        
        Returns:
            bool: True if the filter evaluates to True, False otherwise.

        """
        out = True
        if len(msg_in) == 1:
            msg_in = msg_in[0]
        if self.filter and (not self.is_eof(msg_in)):
            out = self.filter(msg_in)
        assert(isinstance(out, bool))
        return out
        
    @property
    def empty_obj_recv(self):
        r"""obj: Empty message object."""
        emsg, _ = self.deserialize(self.empty_bytes_msg)
        emsg = self.apply_transform(emsg)
        return emsg

    def is_empty(self, msg, emsg):
        r"""Check that a message matches an empty message object.

        Args:
            msg (object): Message object.
            emsg (object): Empty message object.

        Returns:
            bool: True if the object is empty, False otherwise.

        """
        try:
            assert_equal(msg, emsg)
        except AssertionError:
            return False
        return True

    def is_empty_recv(self, msg):
        r"""Check if a received message object is empty.

        Args:
            msg (obj): Message object.

        Returns:
            bool: True if the object is empty, False otherwise.

        """
        
        if self.is_eof(msg):
            return False
        return self.is_empty(msg, self.empty_obj_recv)
    
    def is_empty_send(self, msg):
        r"""Check if a message object being sent is empty.

        Args:
            msg (obj): Message object.

        Returns:
            bool: True if the object is empty, False otherwise.

        """
        smsg = self.apply_transform(msg)
        emsg, _ = self.deserialize(self.empty_bytes_msg)
        return self.is_empty(smsg, emsg)
        
    def chunk_message(self, msg):
        r"""Yield chunks of message of size maxMsgSize

        Args:
            msg (str, bytes): Raw message bytes to be chunked.

        Returns:
            str: Chunks of message.

        """
        prev = 0
        while prev < len(msg):
            next = min(prev + self.maxMsgSize, len(msg))
            yield msg[prev:next]
            prev = next

    # CLIENT/SERVER METHODS
    def server_exists(self, srv_address):
        r"""Determine if a server exists.

        Args:
            srv_address (str): Address of server comm.

        Returns:
            bool: True if a server with the provided address exists, False
                otherwise.

        """
        global _registered_servers
        return (srv_address in _registered_servers)

    def new_server(self, srv_address):
        r"""Create a new server.

        Args:
            srv_address (str): Address of server comm.

        """
        return self._server_class(srv_address, **self._server_kwargs)

    def signon_to_server(self):
        r"""Add a client to an existing server or create one."""
        with _server_lock:
            global _registered_servers
            if self._server is None:
                if not self.server_exists(self.address):
                    self.debug("Creating new server")
                    self._server = self.new_server(self.address)
                    self._server.start()
                else:
                    self._server = _registered_servers[self.address]
                self._server.add_client()
                self.address = self._server.cli_address

    def signoff_from_server(self):
        r"""Remove a client from the server."""
        with _server_lock:
            if self._server is not None:
                self.debug("Signing off")
                self._server.remove_client()
                self._server = None

    # TEMP COMMS
    @property
    def get_work_comm_kwargs(self):
        r"""dict: Keyword arguments for an existing work comm."""
        return dict(comm=self.comm_class, direction='recv',
                    recv_timeout=self.recv_timeout,
                    is_interface=self.is_interface,
                    single_use=True)

    @property
    def create_work_comm_kwargs(self):
        r"""dict: Keyword arguments for a new work comm."""
        return dict(comm=self.comm_class, direction='send',
                    recv_timeout=self.recv_timeout,
                    is_interface=self.is_interface,
                    uuid=str(uuid.uuid4()), single_use=True)

    def get_work_comm(self, header, **kwargs):
        r"""Get temporary work comm, creating as necessary.

        Args:
            header (dict): Information that will be sent in the message header
                to the work comm.
            **kwargs: Additional keyword arguments are passed to header2workcomm.

        Returns:
            :class:.CommBase: Work comm.

        """
        c = self._work_comms.get(header['id'], None)
        if c is not None:
            return c
        c = self.header2workcomm(header, **kwargs)
        self.add_work_comm(c)
        return c

    def create_work_comm(self, work_comm_name=None, **kwargs):
        r"""Create a temporary work comm.

        Args:
            work_comm_name (str, optional): Name that should be used for the
                work comm. If not provided, one is created from the header id
                and the comm class.
            **kwargs: Keyword arguments for new_comm that should override
                work_comm_kwargs.

        Returns:
            :class:.CommBase: Work comm.

        """
        kws = self.create_work_comm_kwargs
        kws.update(**kwargs)
        if work_comm_name is None:
            cls = kws.get("comm", tools.get_default_comm())
            work_comm_name = '%s_temp_%s_%s.%s' % (
                self.name, cls, kws['direction'], kws['uuid'])
        c = new_comm(work_comm_name, **kws)
        self.add_work_comm(c)
        return c

    def add_work_comm(self, comm):
        r"""Add work comm to dict.

        Args:
            comm (:class:.CommBase): Comm that should be added.

        Raises:
            KeyError: If there is already a comm associated with the key.

        """
        key = comm.uuid
        if key in self._work_comms:
            raise KeyError("Comm already registered with key %s." % key)
        self._work_comms[key] = comm

    def remove_work_comm(self, key, in_thread=False, linger=False):
        r"""Close and remove a work comm.

        Args:
            key (str): Key of comm that should be removed.
            in_thread (bool, optional): If True, close the work comm in a thread.
                Defaults to False.
            linger (bool, optional): If True, drain messages before closing the
                comm. Defaults to False.

        """
        if key not in self._work_comms:
            return
        if not in_thread:
            c = self._work_comms.pop(key)
            c.close(linger=linger)
        else:  # pragma: debug
            # c = self._work_comms[key]
            # c.close_in_thread(no_wait=True)
            raise Exception("Closing in thread not recommended")

    def workcomm2header(self, work_comm, **kwargs):
        r"""Get header information from a comm.

        Args:
            work_comm (:class:.CommBase): Work comm that header describes.
            **kwargs: Additional keyword arguments are added to the header.

        Returns:
            dict: Header information that will be sent with a message.

        """
        header_kwargs = kwargs
        header_kwargs['address'] = work_comm.address
        header_kwargs['id'] = work_comm.uuid
        return header_kwargs

    def header2workcomm(self, header, work_comm_name=None, **kwargs):
        r"""Get a work comm based on header info.

        Args:
            header (dict): Information that will be sent in the message header
                to the work comm.
            work_comm_name (str, optional): Name that should be used for the
                work comm. If not provided, one is created from the header id
                and the comm class.
            **kwargs: Additional keyword arguments are added to the returned
                dictionary.

        Returns:
            :class:.CommBase: Work comm.

        """
        kws = self.get_work_comm_kwargs
        kws.update(**kwargs)
        kws['uuid'] = header['id']
        kws['address'] = header['address']
        if work_comm_name is None:
            cls = kws.get("comm", tools.get_default_comm())
            work_comm_name = '%s_temp_%s_%s.%s' % (
                self.name, cls, kws['direction'], header['id'])
        c = get_comm(work_comm_name, **kws)
        return c

    # SERIALIZATION/DESERIALIZATION METHODS
    def serialize(self, *args, **kwargs):
        r"""Serialize a message using the associated serializer."""
        # Don't send metadata for files
        # kwargs.setdefault('dont_encode', self.is_file)
        kwargs.setdefault('no_metadata', self.is_file)
        return self.serializer.serialize(*args, **kwargs)

    def deserialize(self, *args, **kwargs):
        r"""Deserialize a message using the associated deserializer."""
        # Don't serialize files using JSON
        # kwargs.setdefault('dont_decode', self.is_file)
        return self.serializer.deserialize(*args, **kwargs)

    # SEND METHODS
    def _safe_send(self, *args, **kwargs):
        r"""Send message checking if is 1st message and then waiting."""
        if (not self._used) and self._multiple_first_send:
            out = self._send_1st(*args, **kwargs)
        else:
            self.debug('is_closed = %s', self.is_closed)
            with self._closing_thread.lock:
                self.debug(
                    "inside safe_send lock, is_closed = %s", self.is_closed)
                if self.is_closed:  # pragma: debug
                    return False
                out = self._send(*args, **kwargs)
        if out:
            self._n_sent += 1
            self._last_send = time.perf_counter()
        return out
    
    def _send_1st(self, *args, **kwargs):
        r"""Send first message until it succeeds."""
        with self._closing_thread.lock:
            if self.is_closed:  # pragma: debug
                return False
            flag = self._send(*args, **kwargs)
        T = self.start_timeout(key_suffix='._send_1st')
        self.suppress_special_debug = True
        while (not T.is_out) and (self.is_open) and (not flag):  # pragma: debug
            with self._closing_thread.lock:
                if not self.is_open:
                    break
                flag = self._send(*args, **kwargs)
            if flag or (self.is_closed):
                break
            self.sleep()
        self.stop_timeout(key_suffix='._send_1st')
        self.suppress_special_debug = False
        return flag
        
    def _send(self, msg, *args, **kwargs):
        r"""Raw send. Should be overridden by inheriting class."""
        raise NotImplementedError("_send method needs implemented.")

    def _send_multipart(self, msg, **kwargs):
        r"""Send a message larger than maxMsgSize in multiple parts.

        Args:
            msg (str): Message to send.
            **kwargs: Additional keyword arguments are apssed to _send.

        Returns:
            bool: Success or failure of sending the message.

        """
        nsent = 0
        ret = True
        for imsg in self.chunk_message(msg):
            if self.is_closed:  # pragma: debug
                self.error("._send_multipart(): Connection closed.")
                return False
            ret = self._safe_send(imsg, **kwargs)
            if not ret:  # pragma: debug
                self.debug("Send interupted at %d of %d bytes.",
                           nsent, len(msg))
                break
            nsent += len(imsg)
            self.debug("%d of %d bytes sent", nsent, len(msg))
        if ret and len(msg) > 0:
            self.debug("%d bytes completed", len(msg))
        return ret

    def _send_multipart_worker(self, msg, info, **kwargs):
        r"""Send multipart message to the worker comm identified.

        Args:
            msg (str): Message to be sent.
            info (dict): Information about the outgoing message.
            **kwargs: Additional keyword arguments are passed to the
                workcomm _send_multipart method.

        Returns:
            bool: Success or failure of sending the message.

        """
        workcomm = self.get_work_comm(info)
        ret = workcomm._send_multipart(msg, **kwargs)
        # self.remove_work_comm(workcomm.uuid, in_thread=True)
        return ret
            
    def on_send_eof(self):
        r"""Actions to perform when EOF being sent.

        Returns:
            bool: True if EOF message should be sent, False otherwise.

        """
        self.debug('')
        msg_s = self.eof_msg
        with self._closing_thread.lock:
            if not self._eof_sent.is_set():
                self._eof_sent.set()
            else:  # pragma: debug
                return False, msg_s
        return True, msg_s

    def on_send(self, msg, header_kwargs=None):
        r"""Process message to be sent including handling serializing
        message and handling EOF.

        Args:
            msg (obj): Message to be sent
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header.

        Returns:
            tuple (bool, str, dict): Truth of if message should be sent, raw
                bytes message to send, and header info contained in the message.

        """
        work_comm = None
        if self.is_closed:
            self.debug('Comm closed')
            return False, self.empty_bytes_msg, work_comm
        if len(msg) == 1:
            msg = msg[0]
        if self.is_eof(msg):
            flag, msg_s = self.on_send_eof()
        else:
            flag = True
            # Covert object
            msg_ = self.apply_transform(msg)
            # Serialize
            add_sinfo = (self._send_serializer and (not self.is_file))
            if add_sinfo:
                self.debug('Sending sinfo: %s', self.serializer.serializer_info)
            msg_s = self.serialize(msg_, header_kwargs=header_kwargs,
                                   add_serializer_info=add_sinfo)
            if self.no_serialization:
                msg_len = 1
            else:
                msg_len = len(msg_s)
            # Create work comm if message too large to be sent all at once
            if (msg_len > self.maxMsgSize) and (self.maxMsgSize != 0):
                if header_kwargs is None:
                    header_kwargs = dict()
                work_comm = self.create_work_comm()
                # if 'address' not in header_kwargs:
                #     work_comm = self.create_work_comm()
                # else:
                #     work_comm = self.get_work_comm(header_kwargs)
                header_kwargs = self.workcomm2header(work_comm, **header_kwargs)
                msg_s = self.serialize(msg_, header_kwargs=header_kwargs)
        return flag, msg_s, header_kwargs

    def send(self, *args, **kwargs):
        r"""Send a message.

        Args:
            *args: All arguments are assumed to be part of the message.
            **kwargs: All keywords arguments are passed to comm _send method.

        Returns:
            bool: Success or failure of send.

        """
        if self.single_use and self._used:  # pragma: debug
            raise RuntimeError("This comm is single use and it was already used.")
        args = self.language_driver.language2python(args)
        if not self.evaluate_filter(*args):
            # Return True to indicate success because nothing should be done
            self.debug("Sent message skipped based on filter: %.100s", str(args))
            return True
        try:
            ret = self.send_multipart(args, **kwargs)
            if ret:
                self._used = True
                if self.serializer.initialized:
                    self._send_serializer = False
        except MetaschemaTypeError as e:  # pragma: debug
            self._type_errors.append(e)
            try:
                self.exception('Failed to send: %.100s.', str(args))
            except ValueError:  # pragma: debug
                self.exception('Failed to send (unyt array in message)')
            return False
        except BaseException:
            # Handle error caused by calling repr on unyt array that isn't float64
            try:
                self.exception('Failed to send: %.100s.', str(args))
            except ValueError:  # pragma: debug
                self.exception('Failed to send (unyt array in message)')
            return False
        if self.single_use and self._used:
            self.debug('Closing single use send comm [DISABLED]')
            # self.linger_close()
            # self.close_in_thread(no_wait=True)
        elif ret and self._eof_sent.is_set() and self.close_on_eof_send:
            self.debug('Close on send EOF')
            self.linger_close()
            # self.close_in_thread(no_wait=True, timeout=False)
        return ret

    def send_multipart(self, msg, header_kwargs=None, **kwargs):
        r"""Send a multipart message. If the message is smaller than maxMsgSize,
        it is sent using _send, otherwise it is sent to a worker comm using
        _send_multipart_worker.

        Args:
            msg (obj): Message to be sent.
            header_kwargs (dict, optional): Keyword arguments that should be
                added to the header.
            **kwargs: Additional keyword arguments are passed to _send or
                _send_multipart_worker.

        Returns:
            bool: Success or failure of send.
        
        """
        # Create serialized message that should be sent
        flag, msg_s, header = self.on_send(msg, header_kwargs=header_kwargs)
        if not flag:
            return flag
        if self.no_serialization:
            msg_len = 1
        else:
            msg_len = len(msg_s)
        # Sent first part of message which includes the header describing the
        # work comm
        self.special_debug('Sending %d bytes', msg_len)
        if (msg_len < self.maxMsgSize) or (self.maxMsgSize == 0):
            flag = self._safe_send(msg_s, **kwargs)
        else:
            flag = self._safe_send(msg_s[:self.maxMsgSize])
            if flag:
                # Send remainder of message using work comm
                flag = self._send_multipart_worker(msg_s[self.maxMsgSize:],
                                                   header, **kwargs)
            else:  # pragma: debug
                self.special_debug("Sending message header failed.")
        if flag:
            self.debug('Sent %d bytes', msg_len)
        else:  # pragma: debug
            self.special_debug('Failed to send %d bytes', msg_len)
        return flag

    def send_nolimit(self, *args, **kwargs):
        r"""Alias for send."""
        return self.send(*args, **kwargs)

    def send_eof(self, *args, **kwargs):
        r"""Send the EOF message as a short message.
        
        Args:
            *args: All arguments are passed to comm send.
            **kwargs: All keywords arguments are passed to comm send.

        Returns:
            bool: Success or failure of send.

        """
        return self.send(self.eof_msg, *args, **kwargs)
        # with self._closing_thread.lock:
        #     if not self._eof_sent.is_set():
        #         self._eof_sent.set()
        #         return self.send(self.eof_msg, *args, **kwargs)
        # return False

    # RECV METHODS
    def _safe_recv(self, *args, **kwargs):
        r"""Safe receive that does things for all comm classes."""
        with self._closing_thread.lock:
            if self.is_closed:
                return (False, self.empty_bytes_msg)
            out = self._recv(*args, **kwargs)
        if out[0] and (not self.is_empty(out[1], self.empty_bytes_msg)):
            self._n_recv += 1
            self._last_recv = time.perf_counter()
        return out

    def _recv(self, *args, **kwargs):
        r"""Raw recv. Should be overridden by inheriting class."""
        raise NotImplementedError("_recv method needs implemented.")

    def _recv_multipart(self, data, leng_exp, **kwargs):
        r"""Receive a message larger than YGG_MSG_MAX that is sent in multiple
        parts.

        Args:
            data (str): Initial data received.
            leng_exp (int): Size of message expected.
            **kwargs: All keyword arguments are passed to _recv.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        ret = True
        while len(data) < leng_exp:
            payload = self._safe_recv(**kwargs)
            if not payload[0]:  # pragma: debug
                self.debug("Read interupted at %d of %d bytes.",
                           len(data), leng_exp)
                ret = False
                break
            data = data + payload[1]
            # if len(payload[1]) == 0:
            #     self.sleep()
        payload = (ret, data)
        self.debug("Read %d/%d bytes", len(data), leng_exp)
        return payload

    def _recv_multipart_worker(self, info, **kwargs):
        r"""Receive a message in multiple parts from a worker comm.

        Args:
            info (dict): Information about the incoming message.
            **kwargs: Additional keyword arguments are passed to the
                workcomm _recv_multipart method.

        Returns:
            tuple (bool, str): The success or failure of receiving a message
                and the complete message received.

        """
        workcomm = self.get_work_comm(info)
        out = workcomm._recv_multipart(info['body'], info['size'], **kwargs)
        # self.remove_work_comm(info['id'], linger=True)
        return out
        
    def on_recv_eof(self):
        r"""Actions to perform when EOF received.

        Returns:
            bool: Flag that should be returned for EOF.

        """
        self.debug("Received EOF")
        self._eof_recv.set()
        if self.close_on_eof_recv:
            self.debug("Lingering close on EOF Received")
            self.linger_close()
            return False
        else:
            return True

    def on_recv(self, s_msg, second_pass=False):
        r"""Process raw received message including handling deserializing
        message and handling EOF.

        Args:
            s_msg (bytes, str): Raw bytes message.
            second_pass (bool, optional): If True, this is the second pass for
                a message and _last_header will not be set. Defaults to False.

        Returns:
            tuple (bool, str, dict): Success or failure, processed message, and
                header information.

        """
        flag = True
        metadata = None
        if second_pass:
            metadata = self._last_header
        msg_, header = self.deserialize(s_msg, metadata=metadata)
        if self.is_eof(msg_):
            flag = self.on_recv_eof()
            msg = msg_
        elif not header.get('incomplete', False):
            msg = self.apply_transform(msg_)
        else:
            msg = msg_
        if not second_pass:
            self._last_header = header
        if not header.get('incomplete', False):
            # if not self._used:
            #     self.serializer = serialize.get_serializer(**header)
            #     msg, _ = self.deserialize(s_msg)
            self._used = True
        return flag, msg, header

    def recv(self, *args, **kwargs):
        r"""Receive a message.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, obj): Success or failure of receive and received
                message.

        """
        if self.single_use and self._used:
            raise RuntimeError("This comm is single use and it was already used.")
        if self.is_closed:
            self.debug('Comm closed')
            return (False, None)
        try:
            flag, msg = self.recv_multipart(*args, **kwargs)
        except BaseException:
            self.exception('Failed to recv.')
            return (False, None)
        if flag and (not self.evaluate_filter(msg)):
            assert(not self.single_use)
            self.debug("Recieved message skipped based on filter: %.100s", str(msg))
            return self.recv(*args, **kwargs)
        if self.single_use and self._used:
            self.debug('Linger close on single use')
            self.linger_close()
        out = (flag, msg)
        out = self.language_driver.python2language(out)
        return out

    def recv_multipart(self, *args, **kwargs):
        r"""Receive a multipart message. If a message is received without a
        header, it assumed to be complete. Otherwise, the message is received
        in parts from a worker comm initialized by the sender.

        Args:
            *args: All arguments are passed to comm _recv method.
            **kwargs: All keywords arguments are passed to comm _recv method.

        Returns:
            tuple (bool, str): Success or failure of receive and received
                message.

        """
        # Receive first part of message
        flag, s_msg = self._safe_recv(*args, **kwargs)
        if not flag:
            return flag, s_msg
        # Parse message
        flag, msg, header = self.on_recv(s_msg)
        if not flag:
            if not header.get('raw', False):  # pragma: debug
                self.debug("Failed to receive message header.")
            return flag, msg
        # Receive remainder of message that was not received
        if header.get('incomplete', False):
            header['body'] = msg
            flag, s_msg = self._recv_multipart_worker(header, **kwargs)
            if not flag:  # pragma: debug
                return flag, s_msg
            # Parse complete message
            flag, msg, header2 = self.on_recv(s_msg, second_pass=True)
        if isinstance(s_msg, bytes):
            msg_len = len(s_msg)
        else:
            msg_len = 1
        if flag and (msg_len > 0):
            self.debug('%d bytes received', msg_len)
        return flag, msg
        
    def recv_nolimit(self, *args, **kwargs):
        r"""Alias for recv."""
        return self.recv(*args, **kwargs)

    def drain_messages(self, direction=None, timeout=None, variable=None):
        r"""Sleep while waiting for messages to be drained."""
        self.debug('')
        if direction is None:
            direction = self.direction
        if variable is None:
            variable = 'n_msg_%s_drain' % direction
        if timeout is None:
            timeout = self._timeout_drain
        if not hasattr(self, variable):
            raise ValueError("No attribute named '%s'" % variable)
        Tout = self.start_timeout(timeout, key_suffix='.drain_messages')
        while (not Tout.is_out) and self.is_open:
            n_msg = getattr(self, variable)
            if n_msg == 0:
                break
            else:  # pragma: debug
                self.verbose_debug("Draining %d %s messages.",
                                   n_msg, variable)
                self.sleep()
        self.stop_timeout(key_suffix='.drain_messages')
        self.debug('Done draining')

    def purge(self):
        r"""Purge all messages from the comm."""
        self._n_sent = 0
        self._n_recv = 0
        self._last_send = None
        self._last_recv = None

    # Send/recv dictionary of fields
    def send_dict(self, args_dict, **kwargs):
        r"""Send a message with fields specified in the input dictionary.

        Args:
            args_dict (dict): Dictionary of arguments to send.
            **kwargs: Additiona keyword arguments are passed to send.

        Returns:
            bool: Success/failure of send.

        Raises:
            RuntimeError: If the field order can not be determined.

        """
        metadata = kwargs.get('header_kwargs', {})
        if 'field_order' in kwargs:
            kwargs.setdefault('key_order', kwargs.pop('field_order'))
        if 'key_order' in kwargs:
            metadata['key_order'] = kwargs.pop('key_order')
        metadata.setdefault('key_order', self.serializer.get_field_names())
        if (((metadata['key_order'] is None)
             and isinstance(args_dict, dict)
             and (len(args_dict) <= 1))):
            metadata['key_order'] = [k for k in args_dict.keys()]
        if not self.serializer.initialized:
            metadata['field_names'] = metadata['key_order']
        args = JSONArrayMetaschemaType.coerce_type(args_dict, **metadata)
        # Add field order to kwargs so it can be reconstructed
        kwargs['header_kwargs'] = metadata
        return self.send(*args, **kwargs)

    def recv_dict(self, *args, **kwargs):
        r"""Return a received message as a dictionary of fields. If there are
        not any fields specified, the fields will have the form 'f0', 'f1',
        'f2', ...

        Args:
            *args: Arguments are passed to recv.
            **kwargs: Keyword arguments are passed to recv.

        Returns:
            tuple(bool, dict): Success/failure of receive and a dictionar of
                message fields.

        Raises:

        """
        if 'field_order' in kwargs:
            kwargs.setdefault('key_order', kwargs.pop('field_order'))
        key_order = kwargs.pop('key_order', None)
        flag, msg = self.recv(*args, **kwargs)
        if flag and (not self.is_eof(msg)):
            if self.serializer.typedef['type'] == 'array':
                metadata = copy.deepcopy(self._last_header)
                # if metadata is None:
                #     metadata = {}
                if key_order is not None:
                    metadata['key_order'] = key_order
                metadata.setdefault('key_order', self.serializer.get_field_names())
                msg_dict = JSONObjectMetaschemaType.coerce_type(msg, **metadata)
            else:
                msg_dict = {'f0': msg}
        else:
            msg_dict = msg
        return flag, msg_dict

    # SEND/RECV FIELDS
    # def recv_field(self, field, *args, **kwargs):
    #     r"""Receive an entry for a single field.

    #     Args:
    #         field (str): Name of the field that should be received.
    #         *args: All arguments are passed to recv method if there is not
    #             an existing entry for the requested field.
    #         **kwargs: All keyword arguments are passed to recv method if there
    #             is not an existing entry for the requested field.

    #     Returns:
    #         tuple (bool, obj): Success or failure of receive and received
    #             field entry.

    #     """
    #     flag = True
    #     field_msg = self.empty_obj_recv
    #     if not self._field_backlog.get(field, []):
    #         flag, msg = self.recv_dict(*args, **kwargs)
    #         if self.is_eof(msg):
    #             for k in self.fields:
    #                 self._field_backlog.setdefault(k, [])
    #                 self._field_backlog[k].append(msg)
    #         elif not self.is_empty_recv(msg):
    #             for k, v in msg.items():
    #                 self._field_backlog.setdefault(k, [])
    #                 self._field_backlog.append(v)
    #     if self._field_backlog.get(field, []):
    #         field_msg = self._field_backlog[field].pop(0)
    #     return flag, field_msg

    # ALIASES
    def send_array(self, *args, **kwargs):
        r"""Alias for send."""
        # TODO: Maybe explicitly handle transformation from array
        return self.send(*args, **kwargs)

    def recv_array(self, *args, **kwargs):
        r"""Alias for recv."""
        flag, out = self.recv(*args, **kwargs)
        if flag:
            out = self.serializer.consolidate_array(out)
        return flag, out
