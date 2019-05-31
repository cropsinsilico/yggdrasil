from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty


class ClassMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'class' property."""

    name = 'class'
    schema = {'description': ('One or more classes that the object should be '
                              'an instance of.'),
              'anyOf': [{'type': 'class'},
                        {'type': 'array',
                         'items': {'type': 'class'},
                         'minItems': 1}]}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'class' property."""
        return type(instance)

    @classmethod
    def _validate(cls, validator, value, instance, schema):
        r"""Validator for 'class' property."""
        # TODO: Normalization can be removed if metadata is normalized
        from yggdrasil.metaschema import validate_instance
        value = validate_instance(value, cls.schema, normalize=True)
        if not isinstance(instance, value):
            yield "Instance %s is not of type(s) %s" % (instance, value)
        
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
        # TODO: Normalization can be removed if metadata is normalized
        from yggdrasil.metaschema import validate_instance
        prop1 = validate_instance(prop1, cls.schema, normalize=True)
        prop2 = validate_instance(prop2, cls.schema, normalize=True)
        if not isinstance(prop1, (list, tuple)):
            prop1 = (prop1, )
        if not isinstance(prop2, (list, tuple)):
            prop2 = (prop2, )
        if not (set(prop1) & set(prop2)):
            yield 'No overlap between %s and %s' % (prop1, prop2)
