import copy
from yggdrasil.communication.transforms.SelectFieldsTransform import (
    SelectFieldsTransform)


class SelectScalarTransform(SelectFieldsTransform):
    r"""Class for selecting a single element from an array or dict
    and returning it as a scalar.

    Args:
        index (int, string, optional): Array index or dictionary
            key to select. Defaults to selecting the first element in
            an array or the first key alphabetically.

    """
    _transformtype = 'select_scalar'
    _schema_required = []
    _schema_properties = {'index': {'type': ['integer', 'string'],
                                    'default': 0}}
    _schema_excluded_from_inherit = ['selected', 'single_as_scalar']
    _schema_subtype_description = "Select a single field from a message"

    def __init__(self, *args, **kwargs):
        self.single_as_scalar = True
        super(SelectScalarTransform, self).__init__(*args, **kwargs)

    @property
    def selected(self):
        r"""list: Selected fields for use by base class."""
        return [self.index]
    
    def transform_datatype(self, datatype):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.

        Returns:
            dict: Transformed datatype.

        """
        if isinstance(self.index, int):
            if ((datatype.get('type', None) == 'array'
                 and isinstance(datatype.get('items', None), list))):
                return copy.deepcopy(datatype['items'][self.index])
            elif datatype.get('type', None) == 'object':
                self.index = sorted(list(datatype['properties'].keys()))[self.index]
        return super(SelectScalarTransform, self).transform_datatype(
            datatype)

    def evaluate_transform(self, x, **kwargs):
        r"""Call transform on the provided message.

        Args:
            x (object): Message object to transform.
            **kwargs: Additional keyword arguments are passed to the
                parent class.

        Returns:
            object: The transformed message.

        """
        if isinstance(self.index, int):
            if isinstance(x, dict):
                self.index = sorted(x.keys())[0]
            else:
                return x[self.index]
        assert isinstance(self.index, str)
        return super(SelectScalarTransform, self).evaluate_transform(x, **kwargs)
        
    @classmethod
    def get_testing_options(cls, **kwargs):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """
        return [
            {'kwargs': {'index': 'a',
                        'original_datatype': {
                            'type': 'object',
                            'properties': {x: {'type': 'int'}
                                           for x in 'abc'}}},
             'in/out': [(dict(zip('abc', range(3))), 0)],
             'in/out_t': [({'type': 'object',
                            'properties': {x: {'type': 'int'}
                                           for x in 'abc'}},
                           {'type': 'int', 'title': 'a'})]},
            {'kwargs': {'original_datatype': {
                'type': 'object',
                'properties': {x: {'type': 'int'}
                               for x in 'abc'}}},
             'in/out': [(dict(zip('abc', range(3))), 0)],
             'in/out_t': [({'type': 'object',
                            'properties': {x: {'type': 'int'}
                                           for x in 'abc'}},
                           {'type': 'int', 'title': 'a'})]},
            {'kwargs': {'index': 0,
                        'original_datatype': {
                            'type': 'object',
                            'properties': {x: {'type': 'int'}
                                           for x in 'abc'}}},
             'in/out': [(dict(zip('abc', range(3))), 0)],
             'in/out_t': [({'type': 'object',
                            'properties': {x: {'type': 'int'}
                                           for x in 'abc'}},
                           {'type': 'int', 'title': 'a'})]},
            {'kwargs': {'index': 'a',
                        'original_datatype': {
                            'type': 'array',
                            'items': [
                                {'type': 'int', 'title': x}
                                for x in 'abc']}},
             'in/out': [([0, 1, 2], 0)],
             'in/out_t': [({'type': 'array',
                            'items': [
                                {'type': 'int', 'title': x}
                                for x in 'abc']},
                           {'type': 'int', 'title': 'a'})]},
            {'kwargs': {'original_datatype': {
                'type': 'array',
                'items': [
                    {'type': 'int', 'title': x}
                    for x in 'abc']}},
             'in/out': [([0, 1, 2], 0)],
             'in/out_t': [({'type': 'array',
                            'items': [
                                {'type': 'int', 'title': x}
                                for x in 'abc']},
                           {'type': 'int', 'title': 'a'})]},
            {'kwargs': {'index': 0,
                        'original_datatype': {
                            'type': 'array',
                            'items': [
                                {'type': 'int'} for x in 'abc']}},
             'in/out': [([0, 1, 2], 0)],
             'in/out_t': [({'type': 'array',
                            'items': [
                                {'type': 'int'} for x in 'abc']},
                           {'type': 'int'})]},
            {'kwargs': {'index': 0,
                        'original_datatype': {
                            'type': 'array',
                            'items': {'type': 'int'}}},
             'in/out': [([0, 1, 2], 0)],
             'in/out_t': [({'type': 'array',
                            'items': {'type': 'int'}},
                           {'type': 'int'})]}]
