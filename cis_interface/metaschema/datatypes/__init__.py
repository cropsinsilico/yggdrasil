import os
import glob
import json
import jsonschema
import copy
import importlib
from cis_interface import backwards
from cis_interface.metaschema.properties import get_metaschema_property


_type_registry = {}
_schema_dir = os.path.join(os.path.dirname(__file__), 'schemas')
_base_validator = jsonschema.validators.validator_for({"$schema": ""})
CIS_MSG_HEAD = backwards.unicode2bytes('CIS_MSG_HEAD')


class MetaschemaTypeError(TypeError):
    r"""Error that should be raised when a class encounters a type it cannot handle."""
    pass


def register_type(type_class):
    r"""Register a type class, recording methods for encoding/decoding.

    Args:
        type_class (class): Class to be registered.

    Raises:
        ValueError: If the type is already registered.
        ValueError: If the type is a default JSON type.
        ValueError: If any of the type's properties are not registered.

    """
    global _type_registry
    type_name = type_class.name
    if type_name in _type_registry:
        raise ValueError("Type '%s' already registered." % type_name)
    if (((not type_class._replaces_existing)
         and (type_name in _base_validator.DEFAULT_TYPES))):  # pragma: debug
        raise ValueError("Type '%s' is a JSON default type which cannot be replaced."
                         % type_name)
    # Check properties
    for p in type_class.properties:
        prop_class = get_metaschema_property(p)
        if prop_class.name != p:
            raise ValueError("Type '%s' has unregistered property '%s'."
                             % (type_name, p))
        # Update property class with this type's info
        # TODO: Make sure this actually modifies the class
        # Type strings
        old = list(prop_class.types)
        new = tuple(set(copy.deepcopy(old) + [type_name]))
        prop_class.types = new
        # Python types
        old = list(prop_class.python_types)
        new = tuple(set(copy.deepcopy(old) + list(type_class.python_types)))
        prop_class.python_types = new
    # Add to registry
    type_class._datatype = type_name
    type_class._schema_type = 'type'
    # type_class._schema_required = type_class.definition_schema()['required']
    # type_class._schema_properties = {}  # TODO: Transfer from
    # TODO: Enable schema tracking once ported to jsonschema
    # from cis_interface.schema import register_component
    # register_component(type_class)
    _type_registry[type_name] = type_class
    return type_class


def add_type_from_schema(path_to_schema, **kwargs):
    r"""Add a type from a schema in a file.

    Args:
        path_to_schema (string): Full path to the location of a schema file that
            can be loaded.
        target_globals (dict, optional): Globals dictionary for module where the
            fixed class should be added. If None, the new class is returned.
            Defaults to local globals.
        **kwargs: Additional keyword arguments are assumed to be attributes for
            the new class.

    """
    from cis_interface.metaschema.datatypes.FixedMetaschemaType import (
        create_fixed_type_class)
    if 'target_globals' not in kwargs:
        kwargs['target_globals'] = globals()
    if not os.path.isfile(path_to_schema):
        raise ValueError("The 'path_to_schema' attribute is not a valid path: "
                         + "'%s'" % path_to_schema)
    with open(path_to_schema, 'r') as fd:
        out = json.load(fd)
    jsonschema.validate(out, {'type': 'object',
                              'required': ['title', 'description', 'type']})
    name = out['title']
    if name in _type_registry:
        return name
    description = out['description']
    base = get_type_class(out['type'])
    fixed_properties = out
    return create_fixed_type_class(name, description, base,
                                   fixed_properties, **kwargs)


def register_type_from_file(path_to_schema):
    r"""Decorator for registering a type by loading the schema describing it
    from a file. The original base class is discarded and replaced by one
    determined from the 'type' key in the schema. All attributes/methods
    for the class are preserved.

    Args:
        path_to_schema (str): Full path to the location of a schema file that
            can be loaded.

    Returns:
        function: Decorator that will modify a class according to the information
            provided in the schema.

    """
    def _wrapped_decorator(type_class):
        out = add_type_from_schema(path_to_schema, target_globals=None,
                                   **type_class.__dict__)
                                   
        return out
    return _wrapped_decorator


def get_registered_types():
    r"""Return a dictionary of registered types.

    Returns:
        dict: Registered type/class pairs.

    """
    return _type_registry


def import_all_types():
    r"""Import all types to ensure they are registered."""
    for x in glob.glob(os.path.join(os.path.dirname(__file__), '*.py')):
        type_mod = os.path.basename(x)[:-3]
        if not type_mod.startswith('__'):
            importlib.import_module('cis_interface.metaschema.datatypes.%s' % type_mod)
    # Load types from schema
    schema_files = glob.glob(os.path.join(_schema_dir, '*.json'))
    names = []
    for f in schema_files:
        names.append(add_type_from_schema(f))
    # TODO: Need to make sure metaschema updated if it was already loaded
    from cis_interface.metaschema import _metaschema
    if _metaschema is not None:
        reload = False
        curr = _metaschema
        new_names = []
        for n in names:
            if n not in curr['definitions']['simpleTypes']['enum']:  # pragma: debug
                reload = True
                new_names.append(n)
        if reload:  # pragma: debug
            raise Exception("The metaschema needs to be regenerated to include the "
                            + "following new schemas found in schema files: %s"
                            % new_names)
    

def complete_typedef(typedef):
    r"""Complete the type definition by converting it into the standard format.

    Args:
        typedef (str, dict, list): A type name, type definition dictionary,
            dictionary of subtype definitions, or a list of subtype definitions.

    Returns:
        dict: Type definition dictionary.

    Raises:
        TypeError: If typedef is not a valid type.

    """
    if isinstance(typedef, str):
        out = {'type': typedef}
    elif isinstance(typedef, dict):
        if 'type' in typedef:
            out = copy.deepcopy(typedef)
        else:
            contents = {k: complete_typedef(v) for k, v in typedef.items()}
            out = {'type': 'object', 'properties': contents}
    elif isinstance(typedef, (list, tuple)):
        contents = [complete_typedef(v) for v in typedef]
        out = {'type': 'array', 'items': contents}
    else:
        raise TypeError("Cannot parse type '%s' as type definition." % type(typedef))
    return out


def get_type_class(type_name):
    r"""Return a type class given it's name.

    Args:
        type_name (str): Name of type class.

    Returns:
        class: Type class.

    """
    if type_name not in _type_registry:
        raise ValueError("Class for type '%s' could not be found." % type_name)
    return _type_registry[type_name]


def get_type_from_def(typedef):
    r"""Return the type instance based on the provided type definition.

    Args:
        typedef (obj): This can be the name of a type, a dictionary containing a
            type definition (the 'typename' keyword must be specified), or a
            complex type (a list or dictionary containing types).

    Returns:
        MetaschemaType: Instance of the appropriate type class.

    """
    typedef = complete_typedef(typedef)
    out = get_type_class(typedef['type'])(**typedef)
    return out


def guess_type_from_msg(msg):
    r"""Guess the type class from a message.

    Args:
        msg (str, bytes): Message containing metadata.

    Raises:
        ValueError: If a type class cannot be determined.

    Returns:
        MetaschemaType: Instance of the appropriate type class.

    """
    try:
        if CIS_MSG_HEAD in msg:
            metadata, data = msg.split(CIS_MSG_HEAD, 1)
            metadata = json.loads(backwards.bytes2unicode(metadata))
            cls = _type_registry[metadata['type']]
        else:
            raise Exception
        return cls
    except BaseException:
        raise ValueError("Could not guess type.")


def guess_type_from_obj(obj):
    r"""Guess the type class for a given Python object.

    Args:
        obj (object): Python object.

    Returns:
        MetaschemaType: Instance of the appropriate type class.

    Raises:
        ValueError: If a type class cannot be determined.

    """
    type_encoder = get_metaschema_property('type')
    cls = get_type_class(type_encoder.encode(obj))
    return cls


def encode_type(obj, typedef=None):
    r"""Encode an object into a JSON schema that can be used to both
    describe the object and validate others.

    Args:
        obj (object): Python object to be encoded.
        typedef (dict, optional): Type properties that should be used to
            initialize the encoded type definition in certain cases.
            Defaults to None and is ignored.

    Returns:
        dict: Encoded JSON schema describing the object.

    """
    cls = guess_type_from_obj(obj)
    return cls.encode_type(obj, typedef=typedef)


def encode_data(obj, typedef=None):
    r"""Encode an object into a JSON serializable object.

    Args:
        obj (object): Python object to be encoded.
        typedef (dict, optional): JSON schema describing the object. Defaults
            to None and class is determined from the object.

    Returns:
        object: JSON serializable version of the object.

    """
    if isinstance(typedef, dict) and ('type' in typedef):
        cls = get_type_class(typedef['type'])
    else:
        cls = guess_type_from_obj(obj)
        if typedef is None:
            metadata = cls.encode_type(obj)
            typedef = cls.extract_typedef(metadata)
    return cls.encode_data(obj, typedef=typedef)


def encode(obj):
    r"""Encode an object into a message.

    Args:
        obj (object): Python object to be encoded.

    Returns:
        bytes: Encoded message.

    """
    cls = guess_type_from_obj(obj)
    metadata = cls.encode_type(obj)
    typedef = cls.extract_typedef(metadata)
    cls_inst = cls(**typedef)
    msg = cls_inst.serialize(obj)
    return msg


def decode(msg):
    r"""Decode an object from a message.

    Args:
        msg (bytes): Bytes encoded message.

    Returns:
        object: Decoded Python object.

    """
    cls = guess_type_from_msg(msg)
    metadata = json.loads(backwards.bytes2unicode(msg.split(CIS_MSG_HEAD, 1)[0]))
    typedef = cls.extract_typedef(metadata)
    cls_inst = cls(**typedef)
    obj = cls_inst.deserialize(msg)[0]
    return obj


# def resolve_schema_references(schema, resolver=None):
#     r"""Resolve references within a schema.
#
#     Args:
#         schema (dict): Schema with references to resolve.
#         top_level (dict, optional): Reference to the top level schema.
#
#     Returns:
#         dict: Schema with references replaced with internal references.
#
#     """
#     if resolver is None:
#         if 'definitions' not in schema:
#             return schema
#         out = copy.deepcopy(schema)
#         resolver = jsonschema.RefResolver.from_schema(out)
#     else:
#         out = schema
#     if isinstance(out, dict):
#         if (len(out) == 1) and ('$ref' in out):
#             scope, resolved = resolver.resolve(out['$ref'])
#             out = resolved
#         else:
#             for k, v in out.items():
#                 out[k] = resolve_schema_references(v, resolver=resolver)
#     elif isinstance(out, (list, tuple)):
#         for i in range(len(out)):
#             out[i] = resolve_schema_references(out[i])
#     return out


def compare_schema(schema1, schema2):
    r"""Compare two schemas for compatibility.

    Args:
        schema1 (dict): First schema.
        schema2 (dict): Second schema.

    Yields:
        str: Comparision failure messages.

    """
    # TODO: Resolve references
    # schema1 = resolve_schema_references(schema1)
    # schema2 = resolve_schema_references(schema2)
    # Convert fixed types to base types
    if ('type' in schema2) and ('type' in schema1):
        type_cls1 = get_type_class(schema1['type'])
        type_cls2 = get_type_class(schema2['type'])
        if type_cls1.is_fixed:
            schema1 = type_cls1.typedef_fixed2base(schema1)
        if type_cls2.is_fixed:
            schema2 = type_cls2.typedef_fixed2base(schema2)
    elif (schema1 == schema2) and (len(schema1) == 1) and ('$ref' in schema1):
        pass
    else:
        yield "Type required in both schemas for comparison."
    # Compare contents of schema
    for k, v in schema2.items():
        if k not in schema1:
            yield "Missing entry for required key '%s'" % k
            continue
        else:
            prop_cls = get_metaschema_property(k)
        for e in prop_cls.compare(schema1[k], v):
            yield e
