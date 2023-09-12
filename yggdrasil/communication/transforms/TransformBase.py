import copy
import collections
from yggdrasil import rapidjson
from yggdrasil.components import ComponentBase


class TransformBase(ComponentBase):
    r"""Base class for message transforms.

    Args:
        original_datatype (dict, optional): Datatype associated with expected
            messages. Defaults to None.

    """

    _transformtype = None
    _schema_type = 'transform'
    _schema_subtype_key = 'transformtype'
    _schema_properties = {'original_datatype': {'type': 'schema'}}
    _schema_additional_kwargs = {'allowSingular': 'transformtype'}

    def __init__(self, *args, **kwargs):
        self._state = {}
        super(TransformBase, self).__init__(*args, **kwargs)
        self._transformed_datatype = None
        if self.original_datatype:
            self.set_original_datatype(self.original_datatype)

    @property
    def transformed_datatype(self):
        r"""dict: The transformed datatype."""
        if self._transformed_datatype is None:
            out = None
            if self.original_datatype:
                out = self.transform_datatype(self.original_datatype)
            return out
        return self._transformed_datatype

    def set_original_datatype(self, datatype):
        r"""Set datatype.

        Args:
            datatype (dict): Datatype.

        """
        self.validate_datatype(datatype)
        self.original_datatype = datatype

    def set_original_datatype_from_data(self, data):
        r"""Set datatype from data.

        Args:
            data (object): Data object.

        """
        self.set_original_datatype(rapidjson.encode_schema(data, minimal=True))

    def set_transformed_datatype(self, datatype):
        r"""Set datatype.

        Args:
            datatype (dict): Datatype.

        """
        self._transformed_datatype = datatype

    def set_transformed_datatype_from_data(self, data):
        r"""Set datatype from data.

        Args:
            data (object): Data object.

        """
        if isinstance(data, collections.abc.Iterator):
            item_type = None
            for x in copy.deepcopy(data):
                x_type = rapidjson.encode_schema(x, minimal=True)
                if item_type is None:
                    item_type = x_type
                elif item_type != x_type:
                    item_type = {"type": "any"}
                    break
            return self.set_transformed_datatype(item_type)
        self.set_transformed_datatype(
            rapidjson.encode_schema(data, minimal=True))
        
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
            out = rapidjson.encode_schema(self(rapidjson.generate_data(datatype)),
                                          minimal=True)
            if (((out['type'] == 'array') and (datatype['type'] == 'array')
                 and isinstance(out['items'], list)
                 and isinstance(datatype['items'], list)
                 and (len(out['items']) == len(datatype['items'])))):
                for x, y in zip(out['items'], datatype['items']):
                    if 'title' in y:
                        x.setdefault('title', y['title'])
            return out
        except NotImplementedError:  # pragma: debug
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
        raise NotImplementedError  # pragma: debug

    def call_transform(self, x, no_init=False, **kwargs):
        r"""Call transform, setting datatypes during the process.

        Args:
            x (object): Message object to transform.
            no_init (bool, optional): If True, the datatype is not initialized
                if it is not already set. Defaults to False.
            **kwargs: Additional keyword arguments are passed to
                evaluate_transform.
        
        Returns:
            object: The transformed message.

        """
        if (not self.original_datatype) and (not no_init):
            self.set_original_datatype_from_data(x)
        out = self.evaluate_transform(x, **kwargs)
        if (not self._transformed_datatype) and (not no_init):
            self.set_transformed_datatype_from_data(out)
        return out

    def __call__(self, x, no_init=False, **kwargs):
        r"""Call transform on the provided message.

        Args:
            x (object): Message object to transform.
            no_init (bool, optional): If True, the datatype is not initialized
                if it is not already set. Defaults to False.
            **kwargs: Additional keyword arguments are passed to
                call_transform.

        Returns:
            object: The transformed message.

        """
        if isinstance(x, bytes) and (len(x) == 0) and no_init:
            return b''
        if isinstance(x, collections.abc.Iterator):
            xlist = list(x)
            out = iter([
                self.call_transform(xx, no_init=no_init, **kwargs)
                for xx in xlist
            ])
        else:
            out = self.call_transform(x, no_init=no_init, **kwargs)
        return out
