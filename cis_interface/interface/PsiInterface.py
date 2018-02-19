from cis_interface import backwards, tools
from cis_interface.communication import (
    DefaultComm, RPCComm, ServerComm, ClientComm)
from cis_interface.serialize import (
    AsciiTableSerialize, AsciiTableDeserialize,
    PickleSerialize, PickleDeserialize)


PSI_MSG_MAX = tools.CIS_MSG_MAX
PSI_MSG_EOF = tools.CIS_MSG_EOF
PSI_MSG_BUF = tools.CIS_MSG_BUF


def maxMsgSize():
    r"""int: The maximum message size."""
    return PSI_MSG_MAX


def bufMsgSize():
    r"""int: Buffer size for average message."""
    return PSI_MSG_BUF


def eof_msg():
    r"""str: Message signalling end of file."""
    return PSI_MSG_EOF


def PsiMatlab(_type, args=None):
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
    cls = eval(_type)
    if isinstance(cls, (int, backwards.bytes_type, backwards.unicode_type)):
        obj = cls
    else:
        kwargs = {'matlab': True}
        obj = cls(*args, **kwargs)
    return obj


def PsiInput(name, format_str=None, matlab=False):
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
                       is_interface=True, recv_timeout=False)
    

def PsiOutput(name, format_str=None, matlab=False):
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
                       is_interface=True, recv_timeout=False)

    
def PsiRpc(outname, outfmt, inname, infmt, matlab=False):
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
    # from cis_interface.communication import RPCComm
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
                          is_interface=True, recv_timeout=False)
    return out


def PsiRpcServer(name, infmt='%s', outfmt='%s', matlab=False):
    r"""Get class for handling requests and response for an RPC Server.

    Args:
        name (str): The name of the server queues.
        infmt (str, optional): Format string used to recover variables from
            messages received from the request queue. Defaults to '%s'.
        outfmt (str, optional): Format string used to format variables in a
            message sent to the response queue. Defautls to '%s'.

    Returns:
        ServerComm: Communication object.
        
    """
    # from cis_interface.communication import ServerComm
    if matlab:  # pragma: matlab
        infmt = backwards.decode_escape(infmt)
        outfmt = backwards.decode_escape(outfmt)
    icomm_kwargs = dict(format_str=infmt)
    ocomm_kwargs = dict(format_str=outfmt)
    out = ServerComm.ServerComm(name, response_kwargs=ocomm_kwargs,
                                is_interface=True, recv_timeout=False,
                                **icomm_kwargs)
    return out
    

def PsiRpcClient(name, outfmt='%s', infmt='%s', matlab=False):
    r"""Get class for handling requests and response to an RPC Server from a
    client.

    Args:
        name (str): The name of the server queues.
        outfmt (str, optional): Format string used to format variables in a
            message sent to the request queue. Defautls to '%s'.
        infmt (str, optional): Format string used to recover variables from
            messages received from the response queue. Defautls to '%s'.

    Returns:
        ClientComm: Communication object.
        
    """
    # from cis_interface.communication import ClientComm
    if matlab:  # pragma: matlab
        infmt = backwards.decode_escape(infmt)
        outfmt = backwards.decode_escape(outfmt)
    icomm_kwargs = dict(format_str=infmt)
    ocomm_kwargs = dict(format_str=outfmt)
    out = ClientComm.ClientComm(name, response_kwargs=icomm_kwargs,
                                is_interface=True, recv_timeout=False,
                                **ocomm_kwargs)
    return out
    

# Specialized classes for ascii IO
def PsiAsciiFileInput(name, src_type=1, matlab=False, **kwargs):
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
    return base(name, is_interface=True, recv_timeout=False, **kwargs)


def PsiAsciiFileOutput(name, dst_type=1, matlab=False, **kwargs):
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
    return base(name, is_interface=True, recv_timeout=False, **kwargs)
            

# Specialized classes for ascii table IO
def PsiAsciiTableInput(name, as_array=False, src_type=1, matlab=False, **kwargs):
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
    else:
        base = DefaultComm
    kwargs.setdefault('direction', 'recv')
    if src_type == 0:
        kwargs['as_array'] = as_array
    out = base(name, is_interface=True, recv_timeout=False, **kwargs)
    if src_type == 1:
        ret, format_str = out.recv(timeout=out.timeout)
        if not ret:  # pragma: debug
            raise Exception('PsiAsciiTableInput could not receive format' +
                            'string from input.')
    else:
        format_str = out.file.format_str
    out.meth_deserialize = AsciiTableDeserialize.AsciiTableDeserialize(
        format_str=backwards.decode_escape(format_str),
        as_array=as_array)
    return out


def PsiAsciiTableOutput(name, fmt, as_array=False, dst_type=1, matlab=False,
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
    if dst_type == 0:
        from cis_interface.communication import AsciiTableComm
        base = AsciiTableComm.AsciiTableComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
    if matlab:  # pragma: matlab
        fmt = backwards.decode_escape(fmt)
    kwargs.setdefault('direction', 'send')
    if dst_type == 0:
        kwargs['as_array'] = as_array
        kwargs['format_str'] = fmt
    out = base(name, is_interface=True, recv_timeout=False, **kwargs)
    if dst_type == 1:
        ret = out.send(backwards.decode_escape(fmt))
        if not ret:  # pragma: debug
            raise Exception('PsiAsciiTableOutput could not send format ' +
                            'string to output.')
    else:
        out.file.writeformat()
    out.meth_serialize = AsciiTableSerialize.AsciiTableSerialize(
        format_str=fmt, as_array=as_array)
    return out
    

def PsiPickleInput(name, src_type=1, matlab=False, **kwargs):
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
    kwargs.setdefault('direction', 'recv')
    out = base(name, is_interface=True, recv_timeout=False, **kwargs)
    out.meth_deserialize = PickleDeserialize.PickleDeserialize()
    return out


def PsiPickleOutput(name, dst_type=1, matlab=False, **kwargs):
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
    kwargs.setdefault('direction', 'send')
    out = base(name, is_interface=True, recv_timeout=False, **kwargs)
    out.meth_serialize = PickleSerialize.PickleSerialize()
    return out
