from yggdrasil import tools, constants, rapidjson
from yggdrasil.serialize.SerializeBase import SerializeBase


class AsciiMapSerialize(SerializeBase):
    r"""Class for serializing/deserializing name/value mapping.

    Args:
        delimiter (str, optional): Delimiter that should be used to
            separate name/value pairs in the map. Defaults to \t.

    """
    
    _seritype = 'map'
    _schema_subtype_description = ('Serialzation of mapping between key/value '
                                   'pairs with one pair per line and using a '
                                   'character delimiter to separate keys and '
                                   'values.')
    _schema_properties = {
        'delimiter': {'type': 'string',
                      'default': constants.DEFAULT_DELIMITER_STR}}
    _attr_conv = SerializeBase._attr_conv  # + ['delimiter']
    default_datatype = {'type': 'object'}
    concats_as_str = False

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args (dict): Python dictionary to be serialized.

        Returns:
            bytes, str: Serialized message.

        """
        out = ''
        order = sorted([k for k in args.keys()])
        newline_str = tools.bytes2str(self.newline)
        for k in order:
            v = args[k]
            out += tools.bytes2str(k)
            out += self.delimiter
            out += rapidjson.dumps(v, yggdrasil_mode=rapidjson.YM_READABLE)
            out += newline_str
        return tools.str2bytes(out)

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (bytes): Message to be deserialized.

        Returns:
            dict: Deserialized Python dictionary.

        """
        out = dict()
        lines = tools.bytes2str(msg.split(self.newline), recurse=True)
        for line in lines:
            kv = [x for x in line.split(self.delimiter) if x]
            if len(kv) <= 1:
                # TODO: Allow empty?
                continue
            elif len(kv) == 2:
                if kv[1].startswith("'") and kv[1].endswith("'"):
                    out[kv[0]] = kv[1].strip("'")
                else:
                    try:
                        out[kv[0]] = rapidjson.loads(kv[1])
                    except BaseException:
                        out[kv[0]] = kv[1]
            else:
                raise ValueError("Line has more than one delimiter: " + str(line))
        return out

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
        total = dict()
        for x in objects:
            total.update(x)
        return [total]
        
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(AsciiMapSerialize, cls).get_testing_options()
        out['objects'] = [{'args1': int(1), 'args2': 'this'},
                          {'args3': float(1), 'args4': [int(1), int(2)]}]
        out['empty'] = dict()
        out['contents'] = (b'args1\t1\n'
                           + b'args2\t"this"\n'
                           + b'args3\t1.0\n'
                           + b'args4\t[1,2]\n')
        out['invalid_objects'] = [{'args1': int(1), 1: 'this'}]
        return out
