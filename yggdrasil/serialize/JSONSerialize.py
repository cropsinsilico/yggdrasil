from yggdrasil.metaschema.encoder import (
    indent_char2int, encode_json, decode_json,
    JSONReadableEncoder)
from yggdrasil.serialize.SerializeBase import SerializeBase


class JSONSerialize(SerializeBase):
    r"""Class for serializing a python object into a bytes message using JSON.

    Args:
        indent (str, int, optional): String or number of spaces that should be
            used to indent each level within the seiralized structure. Defaults
            to '\t'.
        sort_keys (bool, optional): If True, the serialization of dictionaries
            will be in key sorted order. Defaults to True.

    """

    _seritype = 'json'
    _schema_subtype_description = ('Serializes Python objects using the JSON '
                                   'standard.')
    _schema_properties = {
        'indent': {'type': ['string', 'int'], 'default': '\t'},
        'sort_keys': {'type': 'boolean', 'default': True}}
    default_datatype = {'type': 'object'}
    concats_as_str = False

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (obj): Python object to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        return encode_json(args, indent=self.indent, cls=JSONReadableEncoder)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (str, bytes): Message to be deserialized.

        Returns:
            obj: Deserialized Python object.

        """
        return decode_json(msg)

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
        if all([isinstance(x, dict) for x in objects]):
            total = dict()
            for x in objects:
                total.update(x)
            out = [total]
        elif all([isinstance(x, list) for x in objects]):
            total = list()
            for x in objects:
                total += x
            out = [total]
        else:
            # Adding additional list then causes set of objects to be serialized
            # as a JSON array
            out = [objects]
        return out
        
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        # iobj = {'a': ['b', int(1), float(1.0)], 'c': {'z': 'hello'}}
        iobj1 = {'a': ['b', int(1), float(1.0)], 'c': {'z': 'hello'}}
        iobj2 = {'d': 'new field'}
        # iobj3 = int(2)
        # iobj4 = [float(2.0)]
        out = {'kwargs': {},
               'empty': {}, 'dtype': None,
               'extra_kwargs': {},
               'objects': [iobj1, iobj2],  # , iobj3, iobj4],
               'typedef': {'type': 'object'}}
        out['contents'] = (b'{\n\t"a": [\n\t\t"b",\n\t\t1,\n\t\t1.0\n\t],'
                           b'\n\t"c": {\n\t\t"z": "hello"\n\t},'
                           b'\n\t"d": "new field"\n}')
        out['concatenate'] = [([{'a': 1}, {'b': 2}], [{'a': 1, 'b': 2}]),
                              ([['a'], ['b']], [['a', 'b']]),
                              ([['a'], {'b': 2}], [[['a'], {'b': 2}]])]
        # Version that allows for list concatentation
        # out['contents'] = (b'[\n\t'
        #                    b'{\n\t\t"a": [\n\t\t\t"b",\n\t\t\t1,\n\t\t\t1.0\n\t\t],'
        #                    b'\n\t\t"c": {\n\t\t\t"z": "hello"\n\t\t},'
        #                    b'\n\t\t"d": "new field"\n\t},'
        #                    b'\n\t2,\n\t2.0\n]')
        tab_rep = indent_char2int('\t') * b' '
        out['contents'] = out['contents'].replace(b'\t', tab_rep)
        return out
