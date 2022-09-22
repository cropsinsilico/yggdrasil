from yggdrasil import rapidjson
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.datatypes.PlyMetaschemaType import trimesh
from yggdrasil.serialize.ObjSerialize import ObjDict


if trimesh:
    python_types = (dict, rapidjson.geometry.ObjWavefront, ObjDict,
                    trimesh.base.Trimesh)
else:
    python_types = (dict, rapidjson.geometry.ObjWavefront, ObjDict)

   
class ObjMetaschemaType(MetaschemaType):
    r"""Obj 3D structure map."""

    name = 'obj'
    description = "ObjWavefront 3D structure."
    _empty_msg = {'vertices': [], 'faces': []}
    python_types = python_types

    @classmethod
    def encode_data_readable(cls, obj, typedef):
        r"""Encode an object's data in a readable format.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        if trimesh and isinstance(obj, trimesh.base.Trimesh):
            obj = ObjDict.from_trimesh(obj)
        elif not isinstance(obj, ObjDict):
            try:
                obj = ObjDict(obj)
            except BaseException:
                pass
        return str(obj)
    
    @classmethod
    def coerce_type(cls, obj, typedef=None, **kwargs):
        r"""Coerce objects of specific types to match the data type.

        Args:
            obj (object): Object to be coerced.
            typedef (dict, optional): Type defintion that object should be
                coerced to. Defaults to None.
            **kwargs: Additional keyword arguments are metadata entries that may
                aid in coercing the type.

        Returns:
            object: Coerced object.

        """
        if trimesh and isinstance(obj, trimesh.base.Trimesh):
            obj = ObjDict.from_trimesh(obj)
        elif not isinstance(obj, ObjDict):
            obj = ObjDict(obj)
        # if isinstance(obj, dict) and ('material' in obj):
        #     obj['material'] = tools.bytes2str(obj['material'])
        return super(ObjMetaschemaType, cls).coerce_type(
            obj, typedef=typedef, **kwargs)
