import os
from yggdrasil import tools, constants
from yggdrasil.communication.DefaultComm import DefaultComm


YGG_MSG_MAX = tools.get_YGG_MSG_MAX()
YGG_MSG_EOF = constants.YGG_MSG_EOF
YGG_MSG_BUF = constants.YGG_MSG_BUF
YGG_SERVER_INPUT = os.environ.get('YGG_SERVER_INPUT', False)
YGG_SERVER_OUTPUT = os.environ.get('YGG_SERVER_OUTPUT', False)
YGG_MODEL_NAME = os.environ.get('YGG_MODEL_NAME', False)
_global_scope_comms = {}


def maxMsgSize():
    r"""int: The maximum message size."""
    return YGG_MSG_MAX


def bufMsgSize():
    r"""int: Buffer size for average message."""
    return YGG_MSG_BUF


def eof_msg():
    r"""str: Message signalling end of file."""
    return YGG_MSG_EOF


def YggInit(_type, args=None, kwargs=None):
    r"""Short interface to identify functions called by another language.

    Args:
        _type (str): Name of class that should be returned.
        args (list, optional): Additional arguments that should be passed to
            the class initializer.
        kwargs (dict, optional): Additional keyword arguments that should be
            passed to the class initializer.

    Returns:
        obj: An instance of the requested class.

    """
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    if _type.startswith('Psi'):
        _type = _type.replace('Psi', 'Ygg', 1)
    elif _type.startswith('PSI'):
        _type = _type.replace('PSI', 'YGG', 1)
    if _type.startswith('Cis'):
        _type = _type.replace('Cis', 'Ygg', 1)
    elif _type.startswith('CIS'):
        _type = _type.replace('CIS', 'YGG', 1)
    cls = eval(_type)
    if isinstance(cls, (int, bytes, str)):
        obj = cls
    else:
        obj = cls(*args, **kwargs)
    return obj


def InterfaceComm(name, comm_class=None, global_scope=False, **kwargs):
    r"""Short hand for initializing a default comm for use as an interface.

    Args:
        name (str): The name of the message queue.
        comm_class (CommBase, optional): Communication class that should be
            used. Defaults to DefaultComm if not provided.
        global_scope (bool, optional): If True, the comm will be checked
            for in the global scope before creating a new one. Defaults to
            False.
        **kwargs: Additional keyword arguments are passed to DefaultComm.

    """
    global _global_scope_comms
    if global_scope and (name in _global_scope_comms):
        return _global_scope_comms[name]
    if comm_class is None:
        comm_class = DefaultComm
    kwargs.update(is_interface=True)
    if 'language' not in kwargs:
        kwargs['language'] = tools.get_subprocess_language()
    out = comm_class(name, **kwargs)
    if global_scope:
        _global_scope_comms[name] = out
    return out


def YggInput(name, format_str=None, **kwargs):
    r"""Get class for handling input from a message queue.

    Args:
        name (str): The name of the message queue. Combined with the
            suffix '_IN', it should match an environment variable containing
            a message queue key.
        format_str (str, optional): C style format string that should be used
            to deserialize messages that are receieved into a list of python
            objects. Defaults to None and raw string messages are returned.
        **kwargs: Additional keyword arguments are passed to the underlying comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if ((YGG_SERVER_INPUT
         and ((name == YGG_SERVER_INPUT)
              or (('%s:%s' % (YGG_MODEL_NAME, name)) == YGG_SERVER_INPUT)))):
        return YggRpcServer(YGG_MODEL_NAME, infmt=format_str,
                            outfmt=None, global_scope=True)
    if format_str is not None:
        kwargs['format_str'] = format_str
    kwargs.update(direction='recv', recv_timeout=False)
    return InterfaceComm(name, **kwargs)
    

def YggOutput(name, format_str=None, **kwargs):
    r"""Get class for handling output to a message queue.

    Args:
        name (str): The name of the message queue. Combined with the
            suffix '_OUT', it should match an environment variable containing
            a message queue key.
        format_str (str, optional): C style format string that should be used
            to create a message from a list of python ojbects. Defaults to None
            and raw string messages are sent.
        **kwargs: Additional keyword arguments are passed to the underlying comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if ((YGG_SERVER_OUTPUT
         and ((name == YGG_SERVER_OUTPUT)
              or (('%s:%s' % (YGG_MODEL_NAME, name)) == YGG_SERVER_OUTPUT)))):
        return YggRpcServer(YGG_MODEL_NAME, outfmt=format_str,
                            infmt=None, global_scope=True)
    if format_str is not None:
        kwargs['format_str'] = format_str
    kwargs.update(direction='send')
    return InterfaceComm(name, **kwargs)

    
def YggRpcServer(name, infmt=None, outfmt=None, **kwargs):
    r"""Get class for handling requests and response for an RPC Server.

    Args:
        name (str): The name of the server queues.
        infmt (str, optional): Format string used to recover variables from
            messages received from the request queue. Defaults to '%s'.
        outfmt (str, optional): Format string used to format variables in a
            message sent to the response queue. Defautls to '%s'.
        **kwargs: Additional keyword arguments are passed to InterfaceComm.

    Returns:
        :class:.ServerComm: Communication object.
        
    """
    from yggdrasil.communication import ServerComm
    icomm_kwargs = {}
    ocomm_kwargs = {}
    if infmt is not None:
        icomm_kwargs['format_str'] = infmt
    if outfmt is not None:
        ocomm_kwargs['format_str'] = outfmt
    kwargs.update(icomm_kwargs, comm_class=ServerComm.ServerComm,
                  response_kwargs=ocomm_kwargs)
    kwargs.setdefault('recv_timeout', False)
    return InterfaceComm(name, **kwargs)


def YggRpcClient(name, outfmt=None, infmt=None, **kwargs):
    r"""Get class for handling requests and response to an RPC Server from a
    client.

    Args:
        name (str): The name of the server queues.
        outfmt (str, optional): Format string used to format variables in a
            message sent to the request queue. Defautls to '%s'.
        infmt (str, optional): Format string used to recover variables from
            messages received from the response queue. Defautls to '%s'.
        **kwargs: Additional keyword arguments are passed to InterfaceComm.

    Returns:
        :class:.ClientComm: Communication object.
        
    """
    from yggdrasil.communication import ClientComm
    icomm_kwargs = {}
    ocomm_kwargs = {}
    if infmt is not None:
        icomm_kwargs['format_str'] = infmt
    if outfmt is not None:
        ocomm_kwargs['format_str'] = outfmt
    kwargs.update(ocomm_kwargs, comm_class=ClientComm.ClientComm,
                  response_kwargs=icomm_kwargs)
    kwargs.setdefault('recv_timeout', False)
    return InterfaceComm(name, **kwargs)


def YggTimesyncServer(name='timesync', **kwargs):
    r"""Get class for handling timestep synchronization requests on
    the driver side.

    Args:
        name (str, optional): The name of the server queues. Defaults
            to 'timesync'.
        **kwargs: Additional keyword arguments are passed to InterfaceComm.

    Returns:
        :class:.ServerComm: Communication object.
        
    """
    from yggdrasil.communication import ServerComm
    kwargs['comm_class'] = ServerComm.ServerComm
    kwargs.setdefault('recv_timeout', False)
    return InterfaceComm(name, **kwargs)
    

def YggTimesync(name='timesync', **kwargs):
    r"""Get class for handling timestep synchronization requests.

    Args:
        name (str, optional): The name of the server queues. Defaults
            to 'timesync'.
        **kwargs: Additional keyword arguments are passed to InterfaceComm.

    Returns:
        :class:.ClientComm: Communication object.
        
    """
    from yggdrasil.communication import ClientComm
    kwargs['comm_class'] = ClientComm.ClientComm
    kwargs.setdefault('recv_timeout', False)
    return InterfaceComm(name, **kwargs)


# Specialized classes for ascii IO
def YggAsciiFileInput(name, **kwargs):
    r"""Get class for generic ASCII input.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        **kwargs: Additional keyword arguments are passed to YggInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    return YggInput(name, **kwargs)


def YggAsciiFileOutput(name, **kwargs):
    r"""Get class for generic ASCII output.

    Args:
        name (str): The name of the message queue where output should be sent.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    return YggOutput(name, **kwargs)
            

# Specialized classes for ascii table IO
def YggAsciiTableInput(name, as_array=False, **kwargs):
    r"""Get class for handling table-like formatted input.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        as_array (bool, optional): If True, recv returns the entire table
            array and can only be called once. If False, recv returns row
            entries. Default to False.
        **kwargs: Additional keyword arguments are passed to YggInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['serializer_kwargs'] = dict(as_array=as_array)
    return YggInput(name, **kwargs)


def YggAsciiTableOutput(name, fmt=None, as_array=False, **kwargs):
    r"""Get class for handling table-like formatted output.

    Args:
        name (str): The name of the message queue where output should be sent.
        fmt (str): A C style format string specifying how each 'row' of output
            should be formated. This should include the newline character.
        as_array (bool, optional): If True, send expects and entire array.
            If False, send expects the entries for one table row. Defaults to
            False.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['serializer_kwargs'] = dict(as_array=as_array)
    if fmt is not None:
        kwargs['serializer_kwargs']['format_str'] = fmt
    return YggOutput(name, **kwargs)
    

# Specialized classes for ascii table IO arrays
def YggAsciiArrayInput(name, **kwargs):
    r"""Get class for handling table-like formatted input as arrays.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        **kwargs: Additional keyword arguments are passed to YggAsciiTableInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs.update(as_array=True, recv_converter='table')
    return YggAsciiTableInput(name, **kwargs)


def YggAsciiArrayOutput(name, fmt=None, **kwargs):
    r"""Get class for handling table-like formatted output as arrays.

    Args:
        name (str): The name of the message queue where output should be sent.
        fmt (str): A C style format string specifying how each 'row' of output
            should be formated. This should include the newline character.
        **kwargs: Additional keyword arguments are passed to YggAsciiTableOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    if 'language' not in kwargs:
        kwargs['language'] = tools.get_subprocess_language()
    kwargs.update(as_array=True, send_converter='table')
    return YggAsciiTableOutput(name, fmt, **kwargs)


# Specialized classes for receiving consolidated arrays
def YggArrayInput(name, **kwargs):
    r"""Get class for handling table-like formatted input as arrays.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        **kwargs: Additional keyword arguments are passed to YggInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs.update(recv_converter='array')
    return YggInput(name, **kwargs)


def YggArrayOutput(name, **kwargs):
    r"""Get class for handling table-like formatted output as arrays.

    Args:
        name (str): The name of the message queue where output should be sent.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs.update(send_converter='array')
    return YggOutput(name, **kwargs)


# Pickle io (for backwards compatibility)
def YggPickleInput(name, **kwargs):
    r"""Get class for handling pickled input.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        **kwargs: Additional keyword arguments are passed to YggInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    return YggInput(name, **kwargs)


def YggPickleOutput(name, **kwargs):
    r"""Get class for handling pickled output.

    Args:
        name (str): The name of the message queue where output should be sent.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    return YggOutput(name, **kwargs)


# Pandas io
def YggPandasInput(name, **kwargs):
    r"""Get class for handling Pandas input.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        **kwargs: Additional keyword arguments are passed to YggInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['recv_converter'] = 'pandas'
    return YggInput(name, **kwargs)


def YggPandasOutput(name, **kwargs):
    r"""Get class for handling Pandas output.

    Args:
        name (str): The name of the message queue where output should be sent.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['send_converter'] = 'pandas'
    return YggOutput(name, **kwargs)


# Ply io
def YggPlyInput(name, **kwargs):
    r"""Get class for handling Ply input.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        **kwargs: Additional keyword arguments are passed to YggInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['serializer_kwargs'] = {'type': 'ply'}
    return YggInput(name, **kwargs)


def YggPlyOutput(name, **kwargs):
    r"""Get class for handling Ply output.

    Args:
        name (str): The name of the message queue where output should be sent.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['serializer_kwargs'] = {'type': 'ply'}
    return YggOutput(name, **kwargs)


# Obj io
def YggObjInput(name, **kwargs):
    r"""Get class for handling Obj input.

    Args:
        name (str): The name of the input message queue that input should be
            received from.
        **kwargs: Additional keyword arguments are passed to YggInput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['serializer_kwargs'] = {'type': 'obj'}
    return YggInput(name, **kwargs)


def YggObjOutput(name, **kwargs):
    r"""Get class for handling Obj output.

    Args:
        name (str): The name of the message queue where output should be sent.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    kwargs['serializer_kwargs'] = {'type': 'obj'}
    return YggOutput(name, **kwargs)
