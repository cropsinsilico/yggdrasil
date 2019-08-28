from yggdrasil.components import ComponentBase


class TransformBase(ComponentBase):
    r"""Base class for message transforms.

    Args:
        initial_state (dict, optional): Dictionary of initial state variables
            that should be set when the transform is created.
        serializer (yggdrasil.serialize.SerializeBase, optional): Serializer
            that should be used to information on parts of the transformation.

    """

    _transformtype = None
    _schema_type = 'transform'
    _schema_subtype_key = 'transformtype'
    _schema_properties = {'initial_state': {'type': 'object'},
                          'serializer': {'$ref': '#/definitions/serializer'}}

    def __init__(self, *args, **kwargs):
        self._state = {}
        super(TransformBase, self).__init__(*args, **kwargs)
        if self.initial_state:
            self._state = self.initial_state

    def set_serializer(self, serializer):
        r"""Set serializer if not already set.

        Args:
            serializer (yggdrasil.serialize.SerializeBase): Serializer to add
                to class for use with aspects of the transformation.

        """
        if not self.serializer:
            self.serializer = serializer

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

    def __call__(self, x, no_copy=False):
        r"""Call transform on the provided message.

        Args:
            x (object): Message object to transform.
            no_copy (bool, optional): If True, the transformation occurs in
                place. Otherwise a copy is created and transformed. Defaults
                to False.

        Returns:
            object: The transformed message.

        """
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
        return [{'in/out': [(1, NotImplementedError)]}]
