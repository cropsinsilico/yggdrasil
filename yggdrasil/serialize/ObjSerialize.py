from yggdrasil.serialize.PlySerialize import PlySerialize
from yggdrasil.metaschema.datatypes.ObjMetaschemaType import ObjDict


class ObjSerialize(PlySerialize):
    r"""Class for serializing/deserializing .obj file formats. Reader
    adapted from https://www.pygame.org/wiki/OBJFileLoader."""

    _seritype = 'obj'
    _schema_subtype_description = ('Serialize 3D structures using Obj format.')
    default_datatype = {'type': 'obj'}

    def func_serialize(self, args):
        r"""Serialize a message.

        Args:
            args: List of arguments to be formatted or numpy array to be
                serialized.

        Returns:
            bytes: Serialized message.

        """
        return self.datatype.encode_data(args, self.typedef).encode("utf-8")

    def func_deserialize(self, msg):
        r"""Deserialize a message.

        Args:
            msg (bytes): Message to be deserialized.

        Returns:
            obj: Deserialized message.

        """
        return ObjDict(self.datatype.decode_data(msg, self.typedef))

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing.

        """
        out = super(ObjSerialize, cls).get_testing_options()
        obj = ObjDict({'vertices': [{'x': float(0), 'y': float(0), 'z': float(0)},
                                    {'x': float(0), 'y': float(0), 'z': float(1)},
                                    {'x': float(0), 'y': float(1), 'z': float(1)}],
                       'faces': [[{'vertex_index': int(0)},
                                  {'vertex_index': int(1)},
                                  {'vertex_index': int(2)}]]})
        out['objects'] = [obj, obj]
        out['contents'] = (b'# Author ygg_auto\n'
                           + b'# Generated by yggdrasil\n\n'
                           + b'v 0.0000 0.0000 0.0000\n'
                           + b'v 0.0000 0.0000 1.0000\n'
                           + b'v 0.0000 1.0000 1.0000\n'
                           + b'v 0.0000 0.0000 0.0000\n'
                           + b'v 0.0000 0.0000 1.0000\n'
                           + b'v 0.0000 1.0000 1.0000\n'
                           + b'f 1// 2// 3//\n'
                           + b'f 4// 5// 6//\n')
        return out