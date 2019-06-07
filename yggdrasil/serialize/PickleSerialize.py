from yggdrasil import backwards
from yggdrasil.serialize.DefaultSerialize import DefaultSerialize


class PickleSerialize(DefaultSerialize):
    r"""Class for serializing a python object into a bytes message by pickling.
    """

    _seritype = 'pickle'
    _schema_subtype_description = ('Serialize any Python object using a Python '
                                   'pickle.')
    _default_type = {'type': 'bytes'}
    is_framed = True

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        out = backwards.pickle.dumps(args)
        return backwards.as_bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        out = backwards.pickle.loads(msg)
        return out

    @classmethod
    def get_first_frame(cls, msg):
        r"""Extract one frame from the provided message that may contain one
        or more frames.

        Args:
            msg (bytes): Message containing one or more frames.

        Returns:
            bytes: Portion of message containing the first frame. If no frames
                are found, an empty string will be returned.

        """
        fd = backwards.BytesIO(msg)
        try:
            backwards.pickle.load(fd)
            used = fd.tell()
        except BaseException:
            used = 0
        fd.close()
        return msg[:used]

    @classmethod
    def concatenate(cls, objects, **kwargs):
        r"""Concatenate objects to get object that would be recieved if
        the concatenated serialization were deserialized.

        Args:
            objects (list): Objects to be concatenated.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            list: Set of objects that results from concatenating those provided.

        """
        return objects
    
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(PickleSerialize, cls).get_testing_options()
        if backwards.PY2:  # pragma: Python 2
            out['contents'] = ("S'Test message\\n'\np1\n."
                               + "S'Test message 2\\n'\np1\n.")
        else:  # pragma: Python 3
            out['contents'] = (b'\x80\x03C\rTest message\nq\x00.'
                               + b'\x80\x03C\x0fTest message 2\nq\x00.')
        return out
