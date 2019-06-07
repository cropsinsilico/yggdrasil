from yggdrasil.metaschema.datatypes import (
    get_registered_types, get_type_class, MetaschemaTypeError)
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


def _specificity_sort_key(item):
    return -item[1].specificity


class TypeMetaschemaProperty(MetaschemaProperty):
    r"""Type property with validation of new properties."""

    name = 'type'
    _replaces_existing = True
    _validate = False

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Method to encode the property given the object.

        Args:
            instance (object): Object to get property for.
            typedef (object, None): Template value in type definition to use
                for initializing encoding some cases. Defaults to None and
                is ignored.

        Returns:
            object: Encoded property for instance.

        """
        type_registry = get_registered_types()
        for t, cls in sorted(type_registry.items(), key=_specificity_sort_key):
            if (t != 'any') and cls.validate(instance):
                return t
        raise MetaschemaTypeError(
            "Could not encode 'type' property for Python type: %s"
            % type(instance))

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Method to determine compatiblity of one property value with another.
        This method is not necessarily symmetric in that the second value may
        not be compatible with the first even if the first is compatible with
        the second.

        Args:
            prop1 (object): Property value to compare against prop2.
            prop2 (object): Property value to compare against.
            
        Yields:
            str: Comparision failure messages.

        """
        type_cls = get_type_class(prop1)
        if not type_cls.issubtype(prop2):
            yield "Type '%s' is not a subtype of type '%s'" % (prop1, prop2)

    @classmethod
    def normalize(cls, normalizer, value, instance, schema):
        r"""Method to normalize the instance based on the property value.

        Args:
            normalizer (Normalizer): Normalizer class.
            value (object): Property value.
            instance (object): Object to normalize.
            schema (dict): Schema containing this property.

        Returns:
            object: Normalized object.

        """
        if isinstance(value, (list, tuple)):
            v0 = value[0]
            for v in value:
                t = get_type_class(v)
                # if normalizer.is_type(instance, v):
                if t.validate(v):
                    v0 = v
                    break
            type_cls = get_type_class(v0)
        else:
            type_cls = get_type_class(value)
        return type_cls.normalize(instance)
