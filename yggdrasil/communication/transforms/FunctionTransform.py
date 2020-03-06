from yggdrasil.communication.transforms.TransformBase import TransformBase


class FunctionTransform(TransformBase):
    r"""Class for transforming messages based on a provided Python function.

    Args:
        function (func): The handle for a callable Python object (e.g. function)
            that should be used to transform messages or a string of the form
            "<function file>:<function name>" identifying a function where
            "<function file>" is the module or Python file containing the function
            and "<function name>" is the name of the function. The function should
            take the message as input and return the transformed message.

    """
    _transformtype = 'function'
    _schema_required = ['function']
    _schema_properties = {'function': {'type': 'function'}}

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
        return self.function(x)
    
    @classmethod
    def get_testing_options(cls):
        r"""Get testing options for the transform class.

        Returns:
            list: Multiple dictionaries of keywords and messages before/after
                pairs that will result from the transform created by the provided
                keywords.
        
        """

        def ftran(x):
            if isinstance(x, list):
                return [ftran(ix) for ix in x]
            return x**3
        
        return [{'kwargs': {'function': ftran},
                 'in/out': [(1, 1), (2, 8)],
                 'in/out_t': [
                     ({'type': 'array',
                       'items': [
                           {'type': 'int', 'title': x,
                            'precision': 64, 'units': ''}
                           for x in 'abc']},
                      {'type': 'array',
                       'items': [
                           {'type': 'int', 'title': x,
                            'precision': 64, 'units': ''}
                           for x in 'abc']})]}]
