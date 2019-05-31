from yggdrasil.metaschema.properties.MetaschemaProperty import (
    MetaschemaProperty)


class LengthMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'length' property."""
    
    name = 'length'
    schema = {'description': 'Number of elements in the 1D array.',
              'type': 'number',
              'minimum': 1}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'length' 1darray property."""
        return len(instance)


class ShapeMetaschemaProperty(MetaschemaProperty):
    r"""Property class for 'shape' property."""
    
    name = 'shape'
    schema = {'description': 'Shape of the ND array in each dimension.',
              'type': 'array',
              'items': {'type': 'integer',
                        'minimum': 1}}

    @classmethod
    def encode(cls, instance, typedef=None):
        r"""Encoder for the 'shape' ndarray property."""
        return list(instance.shape)

    @classmethod
    def compare(cls, prop1, prop2, root1=None, root2=None):
        r"""Comparison method for the 'shape' ndarray property."""
        if len(prop1) != len(prop2):
            yield '%d dimensions not compatible with %d dimensions' % (
                len(prop1), len(prop2))
        else:
            for i, (p1, p2) in enumerate(zip(prop1, prop2)):
                if p1 != p2:
                    yield "Size in dimension %d dosn't match. %d vs. %s" % (i, p1, p2)
