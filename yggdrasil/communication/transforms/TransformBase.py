from yggdrasil.components import ComponentBase


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
        return datatype

    def transform_field_names(self, field_names):
        r"""Determine the field names that will result from applying the
        transform to the supplied field_names.
        
        Args:
            field_names (list): Field names to transform.

        Returns:
            list: Transformed field names.

        """
        return field_names

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
