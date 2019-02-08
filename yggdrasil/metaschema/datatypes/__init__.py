import os
import glob
import jsonschema
import copy
import importlib
from collections import OrderedDict
from yggdrasil.metaschema.encoder import decode_json
from yggdrasil.metaschema.properties import get_metaschema_property


_jsonschema_ver_maj = int(float(jsonschema.__version__.split('.')[0]))
_type_registry = OrderedDict()
_schema_dir = os.path.join(os.path.dirname(__file__), 'schemas')
_base_validator = jsonschema.validators.validator_for({"$schema": ""})
YGG_MSG_HEAD = b'YGG_MSG_HEAD'


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
    if (not type_class._replaces_existing):  # pragma: debug
        if _jsonschema_ver_maj < 3:
            exist_flag = (type_name in _base_validator.DEFAULT_TYPES)
        else:
            exist_flag = (type_name in _base_validator.TYPE_CHECKER._type_checkers)
        if exist_flag:
            raise ValueError(("Type '%s' is a JSON default type "
                              "which cannot be replaced.") % type_name)
    # Check properties
    for p in type_class.properties:
        prop_class = get_metaschema_property(p)
        if prop_class.name != p:
            raise ValueError("Type '%s' has unregistered property '%s'."
                             % (type_name, p))
        # Update property class with this type's info
        # TODO: Make sure this actually modifies the class
        # Type strings
        old = copy.deepcopy(list(prop_class.types))
        new = [type_name]
        prop_class.types = tuple(set(old + new))
        # Python types
        old = copy.deepcopy(list(prop_class.python_types))
        try:
            new = list(type_class.python_types)
        except TypeError:
            new = [type_class.python_types]
        prop_class.python_types = tuple(set(old + new))
    # Add to registry
    type_class._datatype = type_name
    type_class._schema_type = 'type'
    # type_class._schema_required = type_class.definition_schema()['required']
    # type_class._schema_properties = {}  # TODO: Transfer from
    # TODO: Enable schema tracking once ported to jsonschema
    # from yggdrasil.schema import register_component
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
    from yggdrasil.metaschema.datatypes.FixedMetaschemaType import (
        create_fixed_type_class)
    if 'target_globals' not in kwargs:
        kwargs['target_globals'] = globals()
    if not os.path.isfile(path_to_schema):
        raise ValueError("The 'path_to_schema' attribute is not a valid path: "
                         + "'%s'" % path_to_schema)
    with open(path_to_schema, 'r') as fd:
        out = decode_json(fd)
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
            importlib.import_module('yggdrasil.metaschema.datatypes.%s' % type_mod)
    # Load types from schema
    schema_files = glob.glob(os.path.join(_schema_dir, '*.json'))
    names = []
    for f in schema_files:
        names.append(add_type_from_schema(f))
    # TODO: Need to make sure metaschema updated if it was already loaded
    from yggdrasil.metaschema import _metaschema
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
    schema_type = get_type_class('schema')
    out = schema_type.normalize(typedef)
    if not isinstance(out, dict) or ('type' not in out):
        raise TypeError("Cannot parse '%s' (type=%s) as type definition." % (
            typedef, type(typedef)))
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


def get_type_from_def(typedef, dont_complete=False):
    r"""Return the type instance based on the provided type definition.

    Args:
        typedef (obj): This can be the name of a type, a dictionary containing a
            type definition (the 'typename' keyword must be specified), or a
            complex type (a list or dictionary containing types).
        dont_complete (bool, optional): If True, the type definition will be
            used as-is. Otherwise it will be completed using normalization which
            can be time consuming. Defaults to False.

    Returns:
        MetaschemaType: Instance of the appropriate type class.

    """
    if not dont_complete:
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
        if YGG_MSG_HEAD in msg:
            _, metadata, data = msg.split(YGG_MSG_HEAD, 2)
            metadata = decode_json(metadata)
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


def encode_data_readable(obj, typedef=None):
    r"""Encode an object into a JSON serializable object that is human readable
    but dosn't guarantee identical deserialization.

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
    return cls.encode_data_readable(obj, typedef=typedef)


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
    metadata = decode_json(msg.split(YGG_MSG_HEAD, 2)[1])
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


def compare_schema(schema1, schema2, root1=None, root2=None):
    r"""Compare two schemas for compatibility.

    Args:
        schema1 (dict): First schema.
        schema2 (dict): Second schema.
        root1 (dict, optional): Root for first schema. Defaults to None and is
            set to schema1.
        root2 (dict, optional): Root for second schema. Defaults to None and is
            set to schema2.

    Yields:
        str: Comparision failure messages.

    """
    try:
        if root1 is None:
            root1 = jsonschema.RefResolver.from_schema(schema1)
        if root2 is None:
            root2 = jsonschema.RefResolver.from_schema(schema2)
        if (len(schema2) == 1) and ('$ref' in schema2):
            with root2.resolving(schema2['$ref']) as resolved_schema2:
                for e in compare_schema(schema1, resolved_schema2,
                                        root1=root1, root2=root2):
                    yield e
        elif (len(schema1) == 1) and ('$ref' in schema1):
            with root1.resolving(schema1['$ref']) as resolved_schema1:
                for e in compare_schema(resolved_schema1, schema2,
                                        root1=root1, root2=root2):
                    yield e
        elif ('type' not in schema2) or ('type' not in schema1):
            yield "Type required in both schemas for comparison."
        elif (schema1 != schema2):
            # Convert fixed types to base types
            type_cls1 = get_type_class(schema1['type'])
            if type_cls1.is_fixed:
                schema1 = type_cls1.typedef_fixed2base(schema1)
            type_list = schema2['type']
            if not isinstance(schema2['type'], list):
                type_list = [type_list]
            all_errors = []
            for itype in type_list:
                itype_cls2 = get_type_class(itype)
                ischema2 = copy.deepcopy(schema2)
                ischema2['type'] = itype
                if itype_cls2.is_fixed:
                    ischema2 = itype_cls2.typedef_fixed2base(ischema2)
                # Compare contents of schema
                ierrors = []
                for k, v in ischema2.items():
                    prop_cls = get_metaschema_property(k, skip_generic=True)
                    if (prop_cls is None) or (k in ['title', 'default']):
                        continue
                    if k not in schema1:
                        ierrors.append("Missing entry for required key '%s'" % k)
                        continue
                    if (k == 'properties') and ('required' in ischema2):
                        vcp = copy.deepcopy(v)
                        for k2 in list(vcp.keys()):
                            if (((k2 not in schema1[k])
                                 and (k2 not in ischema2['required']))):
                                del vcp[k2]
                    else:
                        vcp = v
                    ierrors += list(prop_cls.compare(schema1[k], vcp,
                                                     root1=root1, root2=root2))
                if len(ierrors) == 0:
                    all_errors = []
                    break
                else:
                    all_errors += ierrors
            for e in all_errors:
                yield e
    except BaseException as e:
        yield e
