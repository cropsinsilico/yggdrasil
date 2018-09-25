from cis_interface import backwards, tools, serialize
from cis_interface.communication import DefaultComm


CIS_MSG_MAX = tools.CIS_MSG_MAX
CIS_MSG_EOF = tools.CIS_MSG_EOF
CIS_MSG_BUF = tools.CIS_MSG_BUF


def maxMsgSize():
    r"""int: The maximum message size."""
    return CIS_MSG_MAX


def bufMsgSize():
    r"""int: Buffer size for average message."""
    return CIS_MSG_BUF


def eof_msg():
    r"""str: Message signalling end of file."""
    return CIS_MSG_EOF


def CisMatlab(_type, args=None):  # pragma: matlab
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
        _type = _type.replace('Psi', 'Cis', 1)
    elif _type.startswith('PSI'):
        _type = _type.replace('PSI', 'CIS', 1)
    cls = eval(_type)
    if isinstance(cls, (int, backwards.bytes_type, backwards.unicode_type)):
        obj = cls
    else:
        kwargs = {'matlab': True}
        obj = cls(*args, **kwargs)
    return obj


def CisInput(name, format_str=None, matlab=False):
    r"""Get class for handling input from a message queue.

    Args:
        name (str): The name of the message queue. Combined with the
            suffix '_IN', it should match an environment variable containing
            a message queue key.
        format_str (str, optional): C style format string that should be used
            to deserialize messages that are receieved into a list of python
            objects. Defaults to None and raw string messages are returned.

    Returns:
        DefaultComm: Communication object.
        
    """
    if matlab and format_str is not None:  # pragma: matlab
        format_str = backwards.decode_escape(format_str)
    return DefaultComm(name, direction='recv', format_str=format_str,
                       is_interface=True, recv_timeout=False, matlab=matlab)
    

def CisOutput(name, format_str=None, matlab=False):
    r"""Get class for handling output to a message queue.

    Args:
        name (str): The name of the message queue. Combined with the
            suffix '_OUT', it should match an environment variable containing
            a message queue key.
        format_str (str, optional): C style format string that should be used
            to create a message from a list of python ojbects. Defaults to None
            and raw string messages are sent.

    Returns:
        DefaultComm: Communication object.
        
    """
    if matlab and format_str is not None:  # pragma: matlab
        format_str = backwards.decode_escape(format_str)
    return DefaultComm(name, direction='send', format_str=format_str,
                       is_interface=True, recv_timeout=False, matlab=matlab)

    
def CisRpc(outname, outfmt, inname, infmt, matlab=False):
    r"""Get class for sending a message and then receiving a response.

    Args:
        outname (str): The name of the output message queue.
        outfmt (str): Format string used to format variables in a
            message sent to the output message queue.
        inname (str): The name of the input message queue.
        infmt (str): Format string used to recover variables from
            messages received from the input message queue.

    Returns:
        DefaultComm: Communication object.
        
    """
    from cis_interface.communication import RPCComm
    if matlab:  # pragma: matlab
        infmt = backwards.decode_escape(infmt)
        outfmt = backwards.decode_escape(outfmt)
    icomm_kwargs = dict(format_str=infmt)
    ocomm_kwargs = dict(format_str=outfmt)
    if inname == outname:
        name = inname
    else:
        name = '%s_%s' % (inname, outname)
        icomm_kwargs['name'] = inname
        ocomm_kwargs['name'] = outname
    out = RPCComm.RPCComm(name,
                          icomm_kwargs=icomm_kwargs,
                          ocomm_kwargs=ocomm_kwargs,
                          is_interface=True, recv_timeout=False,
                          matlab=matlab)
    return out


def CisRpcServer(name, infmt='%s', outfmt='%s', matlab=False):
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
    from cis_interface.communication import ServerComm
    if matlab:  # pragma: matlab
        infmt = backwards.decode_escape(infmt)
        outfmt = backwards.decode_escape(outfmt)
    icomm_kwargs = dict(format_str=infmt)
    ocomm_kwargs = dict(format_str=outfmt)
    out = ServerComm.ServerComm(name, response_kwargs=ocomm_kwargs,
                                is_interface=True, recv_timeout=False,
                                matlab=matlab, **icomm_kwargs)
    return out
    

def CisRpcClient(name, outfmt='%s', infmt='%s', matlab=False):
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
    from cis_interface.communication import ClientComm
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
def CisAsciiFileInput(name, src_type=1, matlab=False, **kwargs):
    r"""Get class for generic ASCII input from either a file or message
    queue.

    Args:
        name (str): Path to the local file that input should be read from (if
            src_type == 0) or the name of the input message queue that input
            should be received from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise input is received from a message queue. Defauts to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if src_type == 0:
        from cis_interface.communication import AsciiFileComm
        base = AsciiFileComm.AsciiFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
    kwargs.setdefault('direction', 'recv')
    return base(name, is_interface=True, recv_timeout=False,
                matlab=matlab, **kwargs)


def CisAsciiFileOutput(name, dst_type=1, matlab=False, **kwargs):
    r"""Get class for generic ASCII output to either a local file or message
    queue.

    Args:
        name (str): Path to the local file where output should be written (if
            dst_type == 0) or the name of the message queue where output
            should be sent.
        dst_type (int, optional): If 0, output is written to a local file.
            Otherwise, output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if dst_type == 0:
        from cis_interface.communication import AsciiFileComm
        base = AsciiFileComm.AsciiFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
    kwargs.setdefault('direction', 'send')
    return base(name, is_interface=True, recv_timeout=False,
                matlab=matlab, **kwargs)
            

# Specialized classes for ascii table IO
def CisAsciiTableInput(name, as_array=False, src_type=1, matlab=False, **kwargs):
    r"""Get class for handling table-like formatted input.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        as_array (bool, optional): If True, recv returns the entire table
            array and can only be called once. If False, recv returns row
            entries. Default to False.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if src_type == 0:
        from cis_interface.communication import AsciiTableComm
        base = AsciiTableComm.AsciiTableComm
        kwargs.setdefault('address', name)
        kwargs['as_array'] = as_array
    else:
        base = DefaultComm
        # TODO: This will be overwritten on recv
        kwargs['serializer_kwargs'] = dict(as_array=as_array)
    kwargs.setdefault('direction', 'recv')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisAsciiTableOutput(name, fmt, as_array=False, dst_type=1, matlab=False,
                        **kwargs):
    r"""Get class for handling table-like formatted output.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        fmt (str): A C style format string specifying how each 'row' of output
            should be formated. This should include the newline character.
        as_array (bool, optional): If True, send expects and entire array.
            If False, send expects the entries for one table row. Defaults to
            False.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if matlab:  # pragma: matlab
        fmt = backwards.decode_escape(fmt)
    if dst_type == 0:
        from cis_interface.communication import AsciiTableComm
        base = AsciiTableComm.AsciiTableComm
        kwargs.setdefault('address', name)
        kwargs.update(as_array=as_array, format_str=fmt)
    else:
        base = DefaultComm
        kwargs['serializer_kwargs'] = dict(as_array=as_array,
                                           format_str=fmt)
    kwargs.setdefault('direction', 'send')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out
    

def CisAsciiArrayOutput(name, fmt, dst_type=1, matlab=False, **kwargs):
    r"""Get class for handling table-like formatted output.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        fmt (str): A C style format string specifying how each 'row' of output
            should be formated. This should include the newline character.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if matlab:  # pragma: matlab
        kwargs['send_converter'] = serialize.consolidate_array
    return CisAsciiTableOutput(name, fmt, as_array=True, dst_type=dst_type,
                               matlab=matlab, **kwargs)


def CisAsciiArrayInput(name, src_type=1, matlab=False, **kwargs):
    r"""Get class for handling table-like formatted input as arrays.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    return CisAsciiTableInput(name, as_array=True, src_type=src_type,
                              matlab=matlab, **kwargs)


def CisPickleInput(name, src_type=1, matlab=False, **kwargs):
    r"""Get class for handling pickled input.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if src_type == 0:
        from cis_interface.communication import PickleFileComm
        base = PickleFileComm.PickleFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
        kwargs['serializer_kwargs'] = dict(stype=4)
    kwargs.setdefault('direction', 'recv')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisPickleOutput(name, dst_type=1, matlab=False, **kwargs):
    r"""Get class for handling pickled output.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if dst_type == 0:
        from cis_interface.communication import PickleFileComm
        base = PickleFileComm.PickleFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
        kwargs['serializer_kwargs'] = dict(stype=4)
    kwargs.setdefault('direction', 'send')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisPandasInput(name, src_type=1, matlab=False, **kwargs):
    r"""Get class for handling Pandas input.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if src_type == 0:
        from cis_interface.communication import PandasFileComm
        base = PandasFileComm.PandasFileComm
        kwargs.setdefault('address', name)
        if matlab:  # pragma: matlab
            kwargs['recv_converter'] = serialize.pandas2numpy
    else:
        base = DefaultComm
        if not matlab:
            kwargs['recv_converter'] = serialize.numpy2pandas
    kwargs.setdefault('direction', 'recv')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisPandasOutput(name, dst_type=1, matlab=False, **kwargs):
    r"""Get class for handling pandasd output.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if dst_type == 0:
        from cis_interface.communication import PandasFileComm
        base = PandasFileComm.PandasFileComm
        kwargs.setdefault('address', name)
        if matlab:  # pragma: matlab
            kwargs['send_converter'] = serialize.numpy2pandas
    else:
        base = DefaultComm
        if matlab:  # pragma: matlab
            kwargs['send_converter'] = serialize.consolidate_array
        else:
            kwargs['send_converter'] = serialize.pandas2numpy
    kwargs.setdefault('direction', 'send')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisPlyInput(name, src_type=1, matlab=False, **kwargs):
    r"""Get class for handling Ply input.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if src_type == 0:
        from cis_interface.communication import PlyFileComm
        base = PlyFileComm.PlyFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
        kwargs['serializer_kwargs'] = dict(stype=8)
    kwargs.setdefault('direction', 'recv')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisPlyOutput(name, dst_type=1, matlab=False, **kwargs):
    r"""Get class for handling Ply output.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if dst_type == 0:
        from cis_interface.communication import PlyFileComm
        base = PlyFileComm.PlyFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
        kwargs['serializer_kwargs'] = dict(stype=8)
    kwargs.setdefault('direction', 'send')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisObjInput(name, src_type=1, matlab=False, **kwargs):
    r"""Get class for handling Obj input.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if src_type == 0:
        from cis_interface.communication import ObjFileComm
        base = ObjFileComm.ObjFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
        kwargs['serializer_kwargs'] = dict(stype=9)
    kwargs.setdefault('direction', 'recv')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out


def CisObjOutput(name, dst_type=1, matlab=False, **kwargs):
    r"""Get class for handling Obj output.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    Returns:
        DefaultComm: Communication object.
        
    """
    if dst_type == 0:
        from cis_interface.communication import ObjFileComm
        base = ObjFileComm.ObjFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
        kwargs['serializer_kwargs'] = dict(stype=9)
    kwargs.setdefault('direction', 'send')
    out = base(name, is_interface=True, recv_timeout=False,
               matlab=matlab, **kwargs)
    return out
