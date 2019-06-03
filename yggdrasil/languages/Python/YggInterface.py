from yggdrasil import backwards, tools, serialize
from yggdrasil.communication.DefaultComm import DefaultComm


YGG_MSG_MAX = tools.get_YGG_MSG_MAX()
YGG_MSG_EOF = tools.YGG_MSG_EOF
YGG_MSG_BUF = tools.YGG_MSG_BUF


def maxMsgSize():
    r"""int: The maximum message size."""
    return YGG_MSG_MAX


def bufMsgSize():
    r"""int: Buffer size for average message."""
    return YGG_MSG_BUF


def eof_msg():
    r"""str: Message signalling end of file."""
    return YGG_MSG_EOF


def YggMatlab(_type, args=None):  # pragma: matlab
    r"""Short interface to identify functions called by Matlab.

    Args:
        _type (str): Name of class that should be returned.
        args (list): Additional arguments that should be passed to class
            initializer.

    Returns:
        obj: An instance of the requested class.

    """
    if args is None:
        args = []
    if _type.startswith('Psi'):
        _type = _type.replace('Psi', 'Ygg', 1)
    elif _type.startswith('PSI'):
        _type = _type.replace('PSI', 'YGG', 1)
    if _type.startswith('Cis'):
        _type = _type.replace('Cis', 'Ygg', 1)
    elif _type.startswith('CIS'):
        _type = _type.replace('CIS', 'YGG', 1)
    cls = eval(_type)
    if isinstance(cls, (int, backwards.bytes_type, backwards.unicode_type)):
        obj = cls
    else:
        kwargs = {'matlab': True}
        obj = cls(*args, **kwargs)
    return obj


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
    if format_str is not None:
        if kwargs.get('matlab', False):  # pragma: matlab
            format_str = backwards.decode_escape(format_str)
        kwargs['format_str'] = format_str
    kwargs.update(direction='recv', is_interface=True, recv_timeout=False)
    return DefaultComm(name, **kwargs)
    

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
    if format_str is not None:
        if kwargs.get('matlab', False):  # pragma: matlab
            format_str = backwards.decode_escape(format_str)
        kwargs['format_str'] = format_str
    kwargs.update(direction='send', is_interface=True, recv_timeout=False)
    return DefaultComm(name, **kwargs)

    
def YggRpcServer(name, infmt='%s', outfmt='%s', matlab=False):
    r"""Get class for handling requests and response for an RPC Server.

    Args:
        name (str): The name of the server queues.
        infmt (str, optional): Format string used to recover variables from
            messages received from the request queue. Defaults to '%s'.
        outfmt (str, optional): Format string used to format variables in a
            message sent to the response queue. Defautls to '%s'.

    Returns:
        :class:.ServerComm: Communication object.
        
    """
    from yggdrasil.communication import ServerComm
    if matlab:  # pragma: matlab
        infmt = backwards.decode_escape(infmt)
        outfmt = backwards.decode_escape(outfmt)
    icomm_kwargs = dict(format_str=infmt)
    ocomm_kwargs = dict(format_str=outfmt)
    out = ServerComm.ServerComm(name, response_kwargs=ocomm_kwargs,
                                is_interface=True, recv_timeout=False,
                                matlab=matlab, **icomm_kwargs)
    return out
    

def YggRpcClient(name, outfmt='%s', infmt='%s', matlab=False):
    r"""Get class for handling requests and response to an RPC Server from a
    client.

    Args:
        name (str): The name of the server queues.
        outfmt (str, optional): Format string used to format variables in a
            message sent to the request queue. Defautls to '%s'.
        infmt (str, optional): Format string used to recover variables from
            messages received from the response queue. Defautls to '%s'.

    Returns:
        :class:.ClientComm: Communication object.
        
    """
    from yggdrasil.communication import ClientComm
    if matlab:  # pragma: matlab
        infmt = backwards.decode_escape(infmt)
        outfmt = backwards.decode_escape(outfmt)
    icomm_kwargs = dict(format_str=infmt)
    ocomm_kwargs = dict(format_str=outfmt)
    out = ClientComm.ClientComm(name, response_kwargs=icomm_kwargs,
                                is_interface=True, recv_timeout=False,
                                matlab=matlab, **ocomm_kwargs)
    return out
    

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


def YggAsciiTableOutput(name, fmt, as_array=False, **kwargs):
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
    if kwargs.get('matlab', False):  # pragma: matlab
        fmt = backwards.decode_escape(fmt)
    kwargs['serializer_kwargs'] = dict(as_array=as_array,
                                       format_str=fmt)
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
    kwargs['as_array'] = True
    return YggAsciiTableInput(name, **kwargs)


def YggAsciiArrayOutput(name, fmt, **kwargs):
    r"""Get class for handling table-like formatted output as arrays.

    Args:
        name (str): The name of the message queue where output should be sent.
        fmt (str): A C style format string specifying how each 'row' of output
            should be formated. This should include the newline character.
        **kwargs: Additional keyword arguments are passed to YggAsciiTableOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    if kwargs.get('matlab', False):  # pragma: matlab
        kwargs['send_converter'] = serialize.consolidate_array
    kwargs['as_array'] = True
    return YggAsciiTableOutput(name, fmt, **kwargs)


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
    if kwargs.get('matlab', False):  # pragma: matlab
        kwargs['recv_converter'] = 'array'
    else:
        kwargs['recv_converter'] = 'pandas'
    return YggInput(name, **kwargs)


def YggPandasOutput(name, **kwargs):
    r"""Get class for handling pandasd output.

    Args:
        name (str): The name of the message queue where output should be sent.
        **kwargs: Additional keyword arguments are passed to YggOutput.

    Returns:
        DefaultComm: Communication object.
        
    """
    if kwargs.get('matlab', False):  # pragma: matlab
        kwargs['send_converter'] = serialize.consolidate_array
    else:
        kwargs['send_converter'] = serialize.pandas2list
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
