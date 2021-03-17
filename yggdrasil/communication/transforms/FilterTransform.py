from yggdrasil.communication.transforms.TransformBase import TransformBase


class FilterTransform(TransformBase):
    r"""Class for applying a filter."""
    _transformtype = 'filter'
    _schema_required = ['filter']
    _schema_properties = {'filter': {'$ref': '#/definitions/filter'}}

    def __init__(self, *args, **kwargs):
        super(FilterTransform, self).__init__(*args, **kwargs)
        if isinstance(self.filter, dict):
            from yggdrasil.schema import get_schema
            from yggdrasil.components import create_component
            filter_schema = get_schema().get('filter')
            filter_kws = dict(self.filter,
                              subtype=filter_schema.identify_subtype(self.filter))
            self.filter = create_component('filter', **filter_kws)
    
    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        # Filter should not actually modify the message
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
        if self.filter(x):
            return x
        return iter([])

    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [
            {'kwargs': {'filter': {'statement': '%x% > 1'}},
             'in/out': [(0, iter([])),
                        (2, 2)],
             'in/out_t': [({'type': 'int'}, {'type': 'int'})]}
        ]
