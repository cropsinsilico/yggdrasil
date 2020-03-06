from yggdrasil.components import ComponentBase
from yggdrasil.metaschema.datatypes import encode_type, generate_data


class TransformBase(ComponentBase):
    r"""Base class for message transforms.

    Args:
        initial_state (dict, optional): Dictionary of initial state variables
            that should be set when the transform is created.
        original_datatype (dict, optional): Datatype associated with expected
            messages. Defaults to None.

    """

    _transformtype = None
    _schema_type = 'transform'
    _schema_subtype_key = 'transformtype'
    _schema_properties = {'initial_state': {'type': 'object'},
                          'original_datatype': {'type': 'schema'}}

    def __init__(self, *args, **kwargs):
        self._state = {}
        super(TransformBase, self).__init__(*args, **kwargs)
        if self.initial_state:
            self._state = self.initial_state
        self.transformed_datatype = None
        if self.original_datatype:
            self.set_original_datatype(self.original_datatype)

    def set_original_datatype(self, datatype):
        r"""Set datatype.

        Args:
            datatype (dict): Datatype.

        """
        self.validate_datatype(datatype)
        self.original_datatype = datatype
        self.transformed_datatype = self.transform_datatype(self.original_datatype)

    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        pass
        
    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        try:
            out = encode_type(self(generate_data(datatype)))
            if (((out['type'] == 'array') and (datatype['type'] == 'array')
                 and isinstance(out['items'], list)
                 and isinstance(datatype['items'], list)
                 and (len(out['items']) == len(datatype['items'])))):
                for x, y in zip(out['items'], datatype['items']):
                    if 'title' in y:
                        x.setdefault('title', y['title'])
            return out
        except NotImplementedError:
            return datatype

    def evaluate_transform(self, x, no_copy=False):
        r"""Call transform on the provided message.

        Args:
            x (object): Message object to transform.
            no_copy (bool, optional): If True, the transformation occurs in
                place. Otherwise a copy is created and transformed. Defaults
                to False.

        Returns:
            object: The transformed message.

        """
        raise NotImplementedError

    def __call__(self, x, no_copy=False, no_init=False):
        r"""Call transform on the provided message.

        Args:
            x (object): Message object to transform.
            no_copy (bool, optional): If True, the transformation occurs in
                place. Otherwise a copy is created and transformed. Defaults
                to False.
            no_init (bool, optional): If True, the datatype is not initialized
                if it is not already set. Defaults to False.

        Returns:
            object: The transformed message.

        """
        if (not self.original_datatype) and (not no_init):
            self.set_original_datatype(encode_type(x))
        if isinstance(x, bytes) and (len(x) == 0) and no_init:
            return b''
        out = self.evaluate_transform(x, no_copy=no_copy)
        return out

    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [{'in/out': [(1, NotImplementedError)],
                 'kwargs': {'initial_state': {'test': 1},
                            'original_datatype': {
                                'type': 'int'}}}]
