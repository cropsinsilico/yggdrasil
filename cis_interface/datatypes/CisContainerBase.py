import json
import base64
from cis_interface import backwards
from cis_interface.datatypes import (get_type_class, complete_typedef,
                                     guess_type_from_obj)
from cis_interface.datatypes.CisBaseType import CisBaseType, CisTypeError


class CisContainerBase(CisBaseType):
    r"""Type associated with a container of subtypes."""

    name = 'container'
    description = 'A container of other types.'
    properties = {'contents': {'description': 'Subtypes of container contents.',
                               'type': 'object',  # TODO: expansion 'cistype' type
                               'minProperties': 1}}
    definition_properties = ['contents']
    metadata_properties = ['contents']
    _python_types = tuple()
    _container_type = None

    def __init__(self, *args, **kwargs):
        self._typecls = self._container_type()
        super(CisContainerBase, self).__init__(*args, **kwargs)

    @classmethod
    def _iterate(cls, container):
        r"""Iterate over the contents of the container. Each element returned
        should be a tuple including an index and a value.

        Args:
            container (obj): Object to be iterated over.

        Returns:
            iterator: Iterator over elements in the container.

        """
        raise NotImplementedError("This must be overwritten by the subclass.")

    @classmethod
    def _assign(cls, container, index, value):
        r"""Assign an element in the container to the specified value.

        Args:
            container (obj): Object that element will be assigned to.
            index (obj): Index in the container object where element will be
                assigned.
            value (obj): Value that will be assigned to the element in the
                container object.

        """
        raise NotImplementedError("This must be overwritten by the subclass.")

    @classmethod
    def _has_element(cls, container, index):
        r"""Check to see if an index is in the container.

        Args:
            container (obj): Object that should be checked for index.
            index (obj): Index that should be checked for.

        Returns:
            bool: True if the index is in the container.

        """
        raise NotImplementedError("This must be overwritten by the subclass.")

    @classmethod
    def encode_type(cls, obj):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.

        Returns:
            dict: Encoded type definition.

        """
        if not isinstance(obj, cls._python_types):
            raise CisTypeError("Only '%s' types can be encoded as this type."
                               % str(cls._python_types))
        # Encode subtypes in metadata
        out = {'contents': cls._container_type()}
        for k, v in cls._iterate(obj):
            cls._assign(out['contents'], k,
                        guess_type_from_obj(v).__class__.encode_type(v))
        out.setdefault('typename', cls.name)
        return out

    @classmethod
    def encode_data(cls, obj, typedef):
        r"""Encode an object's data.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        container = cls._container_type()
        for k, v in cls._iterate(typedef['contents']):
            vcls = get_type_class(v['typename'])
            vbytes = vcls.encode_data(obj[k], v)
            cls._assign(container, k,
                        base64.encodestring(vbytes).decode('ascii'))
            # backwards.bytes2unicode(vcls.encode_data(obj[k], v)))
        bytes = backwards.unicode2bytes(json.dumps(container))
        return bytes

    @classmethod
    def decode_data(cls, obj, typedef):
        r"""Decode an object.

        Args:
            obj (string): Encoded object to decode.
            typedef (dict): Type definition that should be used to decode the
                object.

        Returns:
            object: Decoded object.

        """
        container = json.loads(backwards.bytes2unicode(obj))
        for k, v in cls._iterate(typedef['contents']):
            vcls = get_type_class(v['typename'])
            vbytes = base64.decodestring(container[k].encode('ascii'))
            cls._assign(container, k, vcls.decode_data(vbytes, v))
        return container

    @classmethod
    def transform_type(cls, obj, typedef=None):
        r"""Transform an object based on type info.

        Args:
            obj (object): Object to transform.
            typedef (dict, optional): Type definition that should be used to
                transform the object. Defaults to None and no transformation
                is performed.

        Returns:
            object: Transformed object.

        """
        if typedef is None:
            return obj
        for k, v in cls._iterate(typedef['contents']):
            vcls = get_type_class(v['typename'])
            cls._assign(obj, k, vcls.transform_type(obj[k], typedef=v))
        return obj

    @classmethod
    def extract_typedef(cls, metadata):
        r"""Extract the minimum typedef required for this type from the provided
        metadata.

        Args:
            metadata (dict): Message metadata.

        Returns:
            dict: Encoded type definition with unncessary properties removed.

        """
        out = super(CisContainerBase, cls).extract_typedef(metadata)
        contents = out['contents']
        if isinstance(contents, cls._python_types):
            for k, v in cls._iterate(contents):
                if 'typename' in v:
                    vcls = get_type_class(v['typename'])
                    cls._assign(contents, k, vcls.extract_typedef(v))
            out['contents'] = contents
        return out

    def update_typedef(self, **kwargs):
        r"""Update the current typedef with new values.

        Args:
            **kwargs: All keyword arguments are considered to be new type
                definitions. If they are a valid definition property, they
                will be copied to the typedef associated with the instance.

        Returns:
            dict: A dictionary of keyword arguments that were not added to the
                type definition.

        """
        map = kwargs.get('contents', None)
        map_out = self._container_type()
        if isinstance(map, self._python_types):
            for k, v in self._iterate(map):
                v_typedef = complete_typedef(v)
                if self._has_element(self._typecls, k):
                    self._assign(map_out, k,
                                 self._typecls[k].update_typedef(**v_typedef))
                else:
                    self._assign(self._typecls, k,
                                 get_type_class(v_typedef['typename'])(**v_typedef))
                self._assign(map, k, self._typecls[k]._typedef)
            kwargs['contents'] = map
        out = super(CisContainerBase, self).update_typedef(**kwargs)
        if map_out:
            out['contents'] = map_out
        return out

    @classmethod
    def check_meta_compat(cls, k, v1, v2):
        r"""Check that two metadata values are compatible.

        Args:
            k (str): Key for the entry.
            v1 (object): Value 1.
            v2 (object): Value 2.

        Returns:
            bool: True if the two entries are compatible going from v1 to v2,
                False otherwise.

        """
        if k == 'contents':
            assert(isinstance(v1, cls._python_types))
            assert(isinstance(v2, cls._python_types))
            if len(v1) != len(v2):
                return False
            for kt, vt1 in cls._iterate(v1):
                vt2 = v2[kt]
                if ('typename' not in vt1) or ('typename' not in vt2):
                    return False
                tcls = get_type_class(vt2['typename'])
                if not tcls.check_encoded(vt1, vt2):
                    # print("Encoding for '%s' incorrect" % kt)
                    # print(tcls)
                    # print(vt1)
                    # print(vt2)
                    return False
            out = True
        else:
            out = super(CisContainerBase, cls).check_meta_compat(k, v1, v2)
        return out
