from yggdrasil.serialize.SerializeBase import SerializeBase


class FunctionalSerialize(SerializeBase):
    r"""Class for serializing/deserializing a Python object into/from a bytes
    message using defined functions.

    Args:
        encoded_datatype (schema, optional): JSON schema describing the type
            that serialized objects should conform to. Defaults to the class
            attribute default_encoded_datatype. If either func_serialize or
            func_deserialize are not provided, this needs to be specified in
            order to serialize non-bytes objects.
        func_serialize (func, optional): Callable object that takes Python
            objects as input and returns a representation that conforms to
            encoded_datatype. Defaults to None and the default serialization
            for encoded_datatype will be used.
        func_deserialize (func, optional): Callable object that takes objects
            of a type that conforms to encoded_datatype and returns a
            deserialized Python object. Defaults to None and the default
            deserialization for encoded_datatype will be used.
        **kwargs: Additional keyword args are passed to the parent class's
            constructor.

    """

    _seritype = 'functional'
    _schema_subtype_description = ('Serializer that uses provied function to '
                                   'serialize messages.')
    _schema_requried = []
    _schema_properties = {
        'encoded_datatype': {'type': 'schema'},
        'func_serialize': {'type': 'function'},
        'func_deserialize': {'type': 'function'}}
    func_serialize = None
    func_deserialize = None
    
    def __init__(self, **kwargs):
        if isinstance(kwargs.get('func_serialize', None), SerializeBase):
            kwargs['func_serialize'] = kwargs['func_serialize'].func_serialize
        if isinstance(kwargs.get('func_deserialize', None), SerializeBase):
            kwargs['func_deserialize'] = kwargs['func_deserialize'].func_deserialize
        super(FunctionalSerialize, self).__init__(**kwargs)

    # @property
    # def base_class(self):
    #     r"""DefaultSerialize: Default version of serialization."""
    #     if getattr(self, '_base_class', None) is None:
    #         self._base_class = DefaultSerialize(datatype=self.typedef,
    #                                             **self.serializer_info)
    #     return self._base_class

    # TODO: In some cases this should be the object typedef
    # @property
    # def typedef(self):
    #     r"""dict: Type definition."""
    #     return self.encoded_typedef

    @property
    def serializer_info(self):
        r"""dict: Serializer info."""
        raise RuntimeError("Cannot define serializer information for user "
                           + "supplied functions.")

    @property
    def empty_msg(self):
        r"""obj: Object indicating empty message."""
        return self.encoded_datatype._empty_msg
