import jsonschema
import copy
from yggdrasil.metaschema.datatypes import (
    compare_schema, generate_data, resolve_schema_references)
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType


def create_fixed_type_class(name, description, base, fixed_properties,
                            target_globals=None, class_name=None, **kwargs):
    r"""Create a fixed class.

    Args:
        name (str); Name of the fixed type.
        description (str): Description of the fixed type.
        base (MetaschemaType): Base class that should be used.
        fixed_properties (dict): Mapping between properties that are fixed
            and the value they are fixed to.
        target_globals (dict, optional): Globals dictionary for module where the
            fixed class should be added. If None, the new class is returned.
            Defaults to None.
        class_name (str, optional): Name that should be given to the class.
            If not provided, defaults to '<name.title()>MetaschemaType'.
        **kwargs: Additional keyword arguments are treated as attributes that
            should be set on the fixed class.

    Returns:
        str, class: The name of the class created if target_globals is provided,
            the created class if target_globals is None.

    """
    if class_name is None:
        class_name = str('%sMetaschemaType' % name.title())
    iattr = {'name': name,
             'description': description,
             'fixed_properties': fixed_properties,
             'specificity': base.specificity + 1}
    iattr.update(kwargs)
    for k in ['properties', 'definition_properties', 'metadata_properties']:
        iattr[k] = copy.deepcopy(getattr(base, k))
        for x in fixed_properties.keys():
            if x == 'type':
                continue
            if x in iattr[k]:
                iattr[k].remove(x)
    new_cls = type(class_name, (FixedMetaschemaType, base, ), iattr)
    if target_globals is not None:
        target_globals[new_cls.__name__] = new_cls
        del new_cls
        return name
    else:
        return new_cls


class FixedMetaschemaType(MetaschemaType):
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

    is_fixed = True
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
        if out.get('type', None) == cls.base().name:
            out.update(cls.fixed_properties)
            errors = [e for e in compare_schema(typedef, out)]
            if errors:
                error_msg = "Error(s) in comparison with fixed properties.\n"
                for e in errors:
                    error_msg += '\t%s\n' % e
                raise Exception(error_msg)
            for k, v in cls.fixed_properties.items():
                if k in out:
                    del out[k]
            out['type'] = cls.name
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
        if out.get('type', None) == cls.name:
            for k, v in cls.fixed_properties.items():
                if (k == 'type') or (k not in cls.base().properties):
                    continue
                if k in out:
                    assert(out[k] == v)
                else:
                    out[k] = v
            out['type'] = cls.base().name
        if 'definitions' in cls.fixed_properties:
            out['definitions'] = cls.fixed_properties['definitions']
            out = resolve_schema_references(out)
            out.pop('definitions')
        # if cls.base().is_fixed:
        #     out = cls.base().typedef_fixed2base(out)
        return out

    @classmethod
    def issubtype(cls, t):
        r"""Determine if this type is a subclass of the provided type.

        Args:
            t (str): Type name to check against.

        Returns:
            bool: True if this type is a subtype of the specified type t.

        """
        if super(FixedMetaschemaType, cls).issubtype(t):
            return True
        if cls.base().issubtype(t):
            return True
        return False

    @classmethod
    def updated_fixed_properties(cls, obj):
        r"""Get a version of the fixed properties schema that includes information
        from the object.

        Args:
            obj (object): Object to use to put constraints on the fixed properties
                schema.

        Returns:
            dict: Fixed properties schema with object dependent constraints.

        """
        return copy.deepcopy(cls.fixed_properties)

    @classmethod
    def validate(cls, obj, raise_errors=False):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.
            raise_errors (bool, optional): If True, errors will be raised when
                the object fails to be validated. Defaults to False.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if not super(FixedMetaschemaType, cls).validate(obj,
                                                        raise_errors=raise_errors):
            return False
        try:
            jsonschema.validate(obj, cls.updated_fixed_properties(obj),
                                cls=cls.validator())
        except (jsonschema.exceptions.ValidationError, AssertionError):
            if raise_errors:
                raise
            return False
        return True

    # This code was unused by any of the test cases, but is kept in case it is
    # needed in the future
    # @classmethod
    # def encode_type(cls, obj, typedef=None, **kwargs):
    #     r"""Encode an object's type definition.

    #     Args:
    #         obj (object): Object to encode.
    #         typedef (dict, optional): Type properties that should be used to
    #             initialize the encoded type definition in certain cases.
    #             Defaults to None and is ignored.
    #         **kwargs: Additional keyword arguments are treated as additional
    #             schema properties.

    #     Raises:
    #         YggTypeError: If the object is not the correct type.

    #     Returns:
    #         dict: Encoded type definition.

    #     """
    #     type_from_base = False
    #     if typedef is None:
    #         typedef = {}
    #     for k, v in cls.fixed_properties.items():
    #         if (k == 'type'):
    #             continue
    #         elif (typedef.get(k, v) != v) or (kwargs.get(k, v) != v):
    #             type_from_base = True
    #             break
    #     if not type_from_base:
    #         return super(FixedMetaschemaType, cls).encode_type(
    #             obj, typedef=typedef, **kwargs)
    #     if isinstance(typedef, dict):
    #         typedef = cls.typedef_fixed2base(typedef)
    #     kwargs = cls.typedef_fixed2base(kwargs)
    #     out = cls.base().encode_type(obj, typedef=typedef, **kwargs)
    #     out = cls.typedef_base2fixed(out)
    #     return out

    @classmethod
    def check_encoded(cls, metadata, typedef=None, raise_errors=False, **kwargs):
        r"""Checks if the metadata for an encoded object matches the type
        definition.

        Args:
            metadata (dict): Meta data to be tested.
            typedef (dict, optional): Type properties that object should
                be tested against. Defaults to None and object may have
                any values for the type properties (so long as they match
                the schema.
            raise_errors (bool, optional): If True, any errors determining that
                encoded object is not of this type will be raised. Defaults to
                False.
            **kwargs: Additional keyword arguments are passed to the parent class.

        Returns:
            bool: True if the metadata matches the type definition, False
                otherwise.

        """
        try:
            out = cls.typedef_base2fixed(metadata)
        except Exception:
            if raise_errors:
                raise
            return False
        return super(FixedMetaschemaType, cls).check_encoded(
            out, typedef=typedef, raise_errors=raise_errors, **kwargs)

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
        out = super(FixedMetaschemaType, cls).extract_typedef(out)
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
        typename = kwargs.get('type', None)
        if typename == self.__class__.base().name:
            kwargs = self.__class__.typedef_base2fixed(kwargs)
        out = super(FixedMetaschemaType, self).update_typedef(**kwargs)
        return out

    @classmethod
    def _generate_data(cls, typedef):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        typedef0 = cls.typedef_fixed2base(typedef)
        return generate_data(typedef0)
