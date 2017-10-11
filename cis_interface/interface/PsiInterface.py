from logging import debug
import os
import time
import sysv_ipc
from cis_interface.backwards import pickle
from cis_interface.interface.scanf import scanf
from cis_interface.dataio.AsciiFile import AsciiFile
from cis_interface.dataio.AsciiTable import AsciiTable
from cis_interface import backwards, tools
from cis_interface.tools import PSI_MSG_MAX, PSI_MSG_EOF
from cis_interface.communication import (
    DefaultComm, RPCComm, AsciiFileComm, AsciiTableComm)
from cis_interface.serialize import (
    AsciiTableSerialize, AsciiTableDeserialize)


def PsiMatlab(_type, args=[]):
    r"""Short interface to identify functions called by Matlab.

    Args:
        _type (str): Name of class that should be returned.
        args (list): Additional arguments that should be passed to class
            initializer.

    Returns:
        obj: An instance of the requested class.

    """
    cls = eval(_type)
    if isinstance(cls, (int, backwards.bytes_type, backwards.unicode_type)):
        obj = cls
    else:
        kwargs = {'matlab': True}
        obj = cls(*args, **kwargs)
    return obj


class PsiInput(DefaultComm):
    r"""Class for handling input from a message queue.

    Args:
        name (str): The name of the message queue. Combined with the
            suffix '_INT', it should match an environment variable containing
            a message queue key.
        format_str (str, optional): C style format string that should be used
            to deserialize messages that are receieved into a list of python
            objects. Defaults to None and raw string messages are returned.
        
    """
    
    def __init__(self, name, format_str=None, matlab=False):
        if matlab and format_str is not None:  # pragma: matlab
            format_str = backwards.decode_escape(format_str)
        super(PsiInput, self).__init__(name, direction='recv',
                                       format_str=format_str)
        

class PsiOutput(DefaultComm):
    r"""Class for handling output to a message queue.

    Args:
        name (str): The name of the message queue. Combined with the
            suffix '_OUT', it should match an environment variable containing
            a message queue key.
        format_str (str, optional): C style format string that should be used
            to create a message from a list of python ojbects. Defaults to None
            and raw string messages are sent.
        
    """
    def __init__(self, name, format_str=None, matlab=False):
        if matlab and format_str is not None:  # pragma: matlab
            format_str = backwards.decode_escape(format_str)
        super(PsiOutput, self).__init__(name, direction='send',
                                        format_str=format_str)

    
class PsiRpc(RPCComm.RPCComm):
    r"""Class for sending a message and then receiving a response.

    Args:
        outname (str): The name of the output message queue.
        outfmt (str): Format string used to format variables in a
            message sent to the output message queue.
        inname (str): The name of the input message queue.
        infmt (str): Format string used to recover variables from
            messages received from the input message queue.

    """
    def __init__(self, outname, outfmt, inname, infmt, matlab=False):
        if matlab:  # pragma: matlab
            infmt = backwards.decode_escape(infmt)
            outfmt = backwards.decode_escape(outfmt)
        icomm_kwargs = dict(name=inname, format_str=infmt)
        ocomm_kwargs = dict(name=outname, format_str=outfmt)
        super(PsiRpc, self).__init__('%s_%s' % (inname, outname),
                                     icomm_kwargs=icomm_kwargs,
                                     ocomm_kwargs=ocomm_kwargs)

    def call(self, *args):
        r"""Send arguments using the output format string to format a message
        and then receive values back by parsing the response message with the
        input format string.

        Args:
            *args: All arguments are formatted using the output format string
                to create the message.

        Returns:
            tuple (bool, tuple): Success or failure of receiving a message and
                the tuple of arguments retreived by parsing the message using
                the input format string.
        
        """
        ret = self.send_nolimit(*args)
        if ret:
            return self.recv_nolimit(timeout=False)


class PsiRpcServer(PsiRpc):
    r"""Class for handling requests and response for an RPC Server.

    Args:
        name (str): The name of the server queues.
        infmt (str): Format string used to recover variables from
            messages received from the request queue.
        outfmt (str): Format string used to format variables in a
            message sent to the response queue.

    """
    def __init__(self, name, infmt, outfmt, matlab=False):
        super(PsiRpcServer, self).__init__(name, outfmt, name, infmt)
    

class PsiRpcClient(PsiRpc):
    r"""Class for handling requests and response to an RPC Server from a
    client.

    Args:
        name (str): The name of the server queues.
        outfmt (str): Format string used to format variables in a
            message sent to the request queue.
        infmt (str): Format string used to recover variables from
            messages received from the response queue.

    """
    def __init__(self, name, outfmt, infmt, matlab=False):
        super(PsiRpcClient, self).__init__(name, outfmt, name, infmt)
    

# Specialized classes for ascii IO
def PsiAsciiFileInput(name, src_type=1, **kwargs):
    r"""Wrapper to create interface with the correct base comm.

    Args:
        name (str): Path to the local file that input should be read from (if
            src_type == 0) or the name of the input message queue that input
            should be received from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise input is received from a message queue. Defauts to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    """

    if src_type == 0:
        base = AsciiFileComm.AsciiFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
    
    class PsiAsciiFileInput(base):
        r"""Class for generic ASCII input from either a file or message queue.

        Args:
            name (str): Path to the local file that input should be read from (if
                src_type == 0) or the name of the input message queue that input
                should be received from.
            **kwargs: Additional keyword arguments are passed to the base comm.

        """

        def __init__(self, name, matlab=False, **kwargs):
            kwargs.setdefault('direction', 'recv')
            super(PsiAsciiFileInput, self).__init__(name, **kwargs)

    return PsiAsciiFileInput(name, **kwargs)


def PsiAsciiFileOutput(name, dst_type=1, **kwargs):
    r"""Wrapper to create interface with the correct base comm.

    Args:
        name (str): Path to the local file where output should be written (if
            dst_type == 0) or the name of the message queue where output
            should be sent.
        dst_type (int, optional): If 0, output is written to a local file.
            Otherwise, output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    """
    
    if dst_type == 0:
        base = AsciiFileComm.AsciiFileComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
        
    class PsiAsciiFileOutput(base):
        r"""Class for generic ASCII output to either a local file or message
        queue.

        Args:
            name (str): Path to the local file where output should be written (if
                dst_type == 0) or the name of the message queue where output
                should be sent.
            **kwargs: Additional keyword arguments are passed to the base comm.

        """
        def __init__(self, name, matlab=False, **kwargs):
            kwargs.setdefault('direction', 'send')
            super(PsiAsciiFileOutput, self).__init__(name, **kwargs)

    return PsiAsciiFileOutput(name, **kwargs)
            

# Specialized classes for ascii table IO
def PsiAsciiTableInput(name, src_type=1, **kwargs):
    r"""Wrapper to create interface with the correct base comm.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    """

    if src_type == 0:
        base = AsciiTableComm.AsciiTableComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
    kwargs['src_type'] = src_type
    
    class PsiAsciiTableInput(base):
        r"""Class for handling table-like formatted input.

        Args:
            name (str): The path to the local file to read input from (if src_type
                == 0) or the name of the message queue input should be received
                from.
            src_type (int, optional): If 0, input is read from a local file.
                Otherwise, the input is received from a message queue. Defaults to
                1.
            as_array (bool, optional): If True, recv returns the entire table
                array and can only be called once. If False, recv returns row
                entries. Default to False.
            **kwargs: Additional keyword arguments are passed to the base comm.

        """

        def __init__(self, name, matlab=False, src_type=1, as_array=False,
                     **kwargs):
            kwargs.setdefault('direction', 'recv')
            if src_type == 0:
                kwargs['as_array'] = as_array
            super(PsiAsciiTableInput, self).__init__(name, **kwargs)
            if src_type == 1:
                ret, format_str = self.recv(timeout=self.timeout)
                if not ret:  # pragma: debug
                    raise Exception('PsiAsciiTableInput could not receive format' +
                                    'string from input.')
            else:
                format_str = self.file.format_str
            # TODO: Have serialize, deserialize for Ascii comms
            self.meth_deserialize = AsciiTableDeserialize.AsciiTableDeserialize(
                format_str=backwards.decode_escape(format_str),
                as_array=as_array)

        def recv(self, *args, **kwargs):
            r"""Alias so recv defaults to recv_nolimit."""
            return self.recv_nolimit(*args, **kwargs)

    return PsiAsciiTableInput(name, **kwargs)


def PsiAsciiTableOutput(name, fmt, dst_type=1, **kwargs):
    r"""Wrapper to create interface with the correct base comm.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        fmt (str): A C style format string specifying how each 'row' of output
            should be formated. This should include the newline character.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.
        **kwargs: Additional keyword arguments are passed to the base comm.

    """

    if dst_type == 0:
        base = AsciiTableComm.AsciiTableComm
        kwargs.setdefault('address', name)
    else:
        base = DefaultComm
    kwargs['dst_type'] = dst_type
    
    class PsiAsciiTableOutput(base):
        r"""Class for handling table-like formatted output.

        Args:
            name (str): The path to the local file where output should be saved
                (if dst_type == 0) or the name of the message queue where the
                output should be sent.
            fmt (str): A C style format string specifying how each 'row' of output
                should be formated. This should include the newline character.
            dst_type (int, optional): If 0, output is sent to a local file.
                Otherwise, the output is sent to a message queue. Defaults to 1.
            as_array (bool, optional): If True, send expects and entire array.
                If False, send expects the entries for one table row. Defaults to
                False.
            **kwargs: Additional keyword arguments are passed to the base comm.

        """

        def __init__(self, name, fmt, dst_type=1, as_array=False, matlab=False,
                     **kwargs):
            if matlab:  # pragma: matlab
                fmt = backwards.decode_escape(fmt)
            kwargs.setdefault('direction', 'send')
            if dst_type == 0:
                kwargs['as_array'] = as_array
                kwargs['format_str'] = fmt
            super(PsiAsciiTableOutput, self).__init__(name, **kwargs)
            if dst_type == 1:
                ret = self.send(backwards.decode_escape(fmt))
                if not ret:  # pragma: debug
                    raise Exception('PsiAsciiTableOutput could not send format ' +
                                    'string to output.')
            else:
                self.file.writeformat()
            self.meth_serialize = AsciiTableSerialize.AsciiTableSerialize(
                format_str=fmt, as_array=as_array)

        def send(self, *args, **kwargs):
            r"""Alias so send defaults to send_nolimit."""
            return self.send_nolimit(*args, **kwargs)

    return PsiAsciiTableOutput(name, fmt, **kwargs)
    
    
class PsiPickleInput(object):
    r"""Class for handling pickled input.

    Args:
        name (str): The path to the local file to read input from (if src_type
            == 0) or the name of the message queue input should be received
            from.
        src_type (int, optional): If 0, input is read from a local file.
            Otherwise, the input is received from a message queue. Defaults to
            1.

    """
    _name = None
    _type = 1
    _file = None
    _psi = None

    def __init__(self, name, src_type=1, matlab=False):
        self._name = name
        self._type = src_type
        if self._type == 0:
            self._file = open(name, 'rb')
        else:
            self._psi = PsiInput(name)

    def __del__(self):
        if self._type == 0 and (self._file is not None):
            self._file.close()
            self._file = None

    def recv(self):
        r"""Receive a single pickled object.

        Returns:
            tuple(bool, object): Success or failure of receiving a pickled
                object and the unpickled object that was received.

        """
        if self._type == 0:
            try:
                obj = pickle.load(self._file)
                eof = False
            except EOFError:  # pragma: debug
                obj = None
                eof = True
            ret = (not eof)
        else:
            ret, obj = self._psi.recv_nolimit()
            try:
                obj = pickle.loads(obj)
            except pickle.UnpicklingError:  # pragma: debug
                obj = None
                ret = False
        return ret, obj


class PsiPickleOutput(object):
    r"""Class for handling pickled output.

    Args:
        name (str): The path to the local file where output should be saved
            (if dst_type == 0) or the name of the message queue where the
            output should be sent.
        fmt (str): A C style format string specifying how each 'row' of output
            should be formated. This should include the newline character.
        dst_type (int, optional): If 0, output is sent to a local file.
            Otherwise, the output is sent to a message queue. Defaults to 1.

    """
    _name = None
    _type = 0
    _file = None
    _psi = None

    def __init__(self, name, dst_type=1, matlab=False):
        self._name = name
        self._type = dst_type
        if self._type == 0:
            self._file = open(name, 'wb')
        else:
            self._psi = PsiOutput(name)

    def __del__(self):
        if self._type == 0 and (self._file is not None):
            self._file.close()
            self._file = None

    def send(self, obj):
        r"""Output an object as a pickled string to either a local file or
        message queue.

        Args:
            obj (object): Any python object that can be pickled.

        Returns:
            bool: Success or failure of outputing the pickled object.

        """
        if self._type == 0:
            try:
                pickle.dump(obj, self._file)
                ret = True
            except pickle.PicklingError:  # pragma: debug
                ret = False
        else:
            try:
                msg = pickle.dumps(obj)
                ret = True
            except pickle.PicklingError:  # pragma: debug
                ret = False
            if ret:
                ret = self._psi.send_nolimit(msg)
        return ret
