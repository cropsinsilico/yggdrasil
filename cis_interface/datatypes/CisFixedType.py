import copy
from cis_interface.datatypes import register_type
from cis_interface.datatypes.CisBaseType import CisBaseType


def create_fixed_type_class(name, description, base, fixed_properties,
                            target_globals):
    r"""Create a fixed class.

    Args:

    """
    iattr = {'name': name,
             'description': description,
             'fixed_properties': fixed_properties}
    new_cls = register_type(type('Cis%sType' % name.title(),
                                 (CisFixedType, base, ), iattr))
    target_globals[new_cls.__name__] = new_cls
    # globals()[new_cls.__name__] = new_cls
    del new_cls


class CisFixedType(CisBaseType):
    r"""Class that should be used to alias another type, but with certain
    properties fixed.

    Arguments:
        **kwargs: All keyword arguments are assumed to be type definition
            properties which will be used to validate serialized/deserialized
            messages.

    Attributes:
        fixed_properties (dict): Type properties of the parent class that are
            fixed and the values they are fixed to.

    """

    fixed_properties = {}

    @classmethod
    def base(cls):
        r"""Get the type that this type is a fixed version of."""
        return cls.__bases__[-1]

    @classmethod
    def typedef_base2fixed(cls, typedef):
        r"""Transform a type definition from the unfixed base type to the fixed
        type alias by removing fixed properties.

        Args:
            typedef (dict): Type definition for the unfixed base type that might
                include properties that are fixed in the base.
        
        Returns:
            dict: Copy of type definition with fixed properties removed.

        """
        out = copy.deepcopy(typedef)
        if out.get('typename', None) == cls.base().name:
            for k, v in cls.fixed_properties.items():
                if k in out:
                    assert(out[k] == v)
                    del out[k]
            out['typename'] = cls.name
        return out

    @classmethod
    def typedef_fixed2base(cls, typedef):
        r"""Transform a type definition from the fixed alias to the unfixed base by
        setting the fixed properties if they are not already present.

        Args:
            typedef (dict): Type definition for the fixed alias type.

        Returns:
            dict: Copy of type definition with fixed properties added.

        """
        out = copy.deepcopy(typedef)
        if out.get('typename', None) == cls.name:
            for k, v in cls.fixed_properties.items():
                if k in out:
                    assert(out[k] == v)
                else:
                    out[k] = v
            out['typename'] = cls.base().name
        return out

    @classmethod
    def encode_type(cls, obj):
        r"""Encode an object's type definition.

        Args:
            obj (object): Object to encode.

        Raises:
            CisTypeError: If the object is not the correct type.

        Returns:
            dict: Encoded type definition.

        """
        out = super(CisFixedType, cls).encode_type(obj)
        out = cls.typedef_base2fixed(out)
        return out

    @classmethod
    def definition_schema(cls):
        r"""JSON schema for validating a type definition."""
        out = super(CisFixedType, cls).definition_schema()
        for k in cls.fixed_properties.keys():
            if k in out['required']:
                out['required'].remove(k)
            del out['properties'][k]
        return out

    @classmethod
    def metadata_schema(cls):
        r"""JSON schema for validating a JSON serialization of the type."""
        out = super(CisFixedType, cls).metadata_schema()
        for k in cls.fixed_properties.keys():
            if k in out['required']:
                out['required'].remove(k)
        return out

    @classmethod
    def check_encoded(cls, metadata, typedef=None):
        r"""Checks if the metadata for an encoded object matches the type
        definition.

        Args:
            metadata (dict): Meta data to be tested.
            typedef (dict, optional): Type properties that object should
                be tested against. Defaults to None and object may have
                any values for the type properties (so long as they match
                the schema.

        Returns:
            bool: True if the metadata matches the type definition, False
                otherwise.

        """
        out = cls.typedef_base2fixed(metadata)
        return super(CisFixedType, cls).check_encoded(out, typedef=typedef)

    @classmethod
    def extract_typedef(cls, metadata):
        r"""Extract the minimum typedef required for this type from the provided
        metadata.

        Args:
            metadata (dict): Message metadata.

        Returns:
            dict: Encoded type definition with unncessary properties removed.

        """
        out = cls.typedef_base2fixed(metadata)
        out = super(CisFixedType, cls).extract_typedef(out)
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
        typename = kwargs.get('typename', None)
        if typename == self.__class__.base().name:
            kwargs = self.__class__.typedef_base2fixed(kwargs)
        out = super(CisFixedType, self).update_typedef(**kwargs)
        return out
