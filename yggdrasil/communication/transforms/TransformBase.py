import copy
import collections
from yggdrasil import datatypes
from yggdrasil.components import ComponentBase


class TransformError(ValueError):
    r"""Errors encountered during transformation."""
    pass


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
    _transform_datatype = None

    def __init__(self, *args, **kwargs):
        self._state = {}
        super(TransformBase, self).__init__(*args, **kwargs)
        self._transformed_datatype = None
        if self.original_datatype:
            self.set_original_datatype(self.original_datatype, force=True)

    @classmethod
    def _get_datatype(cls, data):
        from yggdrasil.communication.CommBase import CommMessage
        if isinstance(data, collections.abc.Iterator):
            item_type = None
            for x in copy.deepcopy(data):
                x_type = cls._get_datatype(x)
                if item_type is None:
                    item_type = x_type
                elif item_type != x_type:
                    item_type = datatypes.Datatype({"type": "any"})
                    break
            return item_type
        elif isinstance(data, CommMessage):
            if data.stype:
                assert isinstance(data.stype, datatypes.Datatype)
                return data.stype
            data = data.args
        return datatypes.Datatype.from_data(data, minimal=True)

    @property
    def transformed_datatype(self):
        r"""dict: The transformed datatype."""
        if self._transformed_datatype is None:
            out = None
            if self.original_datatype:
                out = self.transform_datatype(self.original_datatype)
            return out
        return self._transformed_datatype

    def set_original_datatype(self, datatype, force=False, **kwargs):
        r"""Set datatype if not already set.

        Args:
            datatype (datatypes.Datatype, dict): Datatype.
            force (bool, optional): If True, set the original datatype
                even if it is already set.
            **kwargs: Additional keyword arguments are passed to the
                Datatype constructor.

        """
        if force or not self.original_datatype:
            datatype = datatypes.Datatype(datatype, **kwargs)
            self.validate_datatype(datatype)
            self.original_datatype = datatype

    def set_original_datatype_from_data(self, data, force=False,
                                        **kwargs):
        r"""Set datatype from data.

        Args:
            data (object): Data object.
            force (bool, optional): If True, set the original datatype
                even if it is already set.
            **kwargs: Additional keyword arguments are passed to
                set_original_datatype.

        """
        self.set_original_datatype(self._get_datatype(data),
                                   force=force, **kwargs)

    def set_transformed_datatype(self, datatype, **kwargs):
        r"""Set datatype.

        Args:
            datatype (datatypes.Datatype, dict): Datatype.
            **kwargs: Additional keyword arguments are passed to the
                Datatype constructor.

        """
        self._transformed_datatype = datatypes.Datatype(datatype, **kwargs)

    def set_transformed_datatype_from_data(self, data, **kwargs):
        r"""Set datatype from data.

        Args:
            data (object): Data object.
            **kwargs: Additional keyword arguments are passed to
                set_transformed_datatype.

        """
        self.set_transformed_datatype(self._get_datatype(data), **kwargs)

    def _validate_datatype(self, datatype):
        pass
        
    def validate_datatype(self, datatype):
        r"""Assert that the provided datatype is valid for this transformation.
        
        Args:
            datatype (dict): Datatype to validate.

        Raises:
            AssertionError: If the datatype is not valid.

        """
        if not isinstance(datatype, datatypes.Datatype):
            datatype = datatypes.Datatype(datatype)
        self._validate_datatype(datatype)

    def transform_datatype(self, datatype, skip_class_method=False,
                           **kwargs):
        r"""Determine the datatype that will result from applying the transform
        to the supplied datatype.

        Args:
            datatype (dict): Datatype to transform.
            skip_class_method (bool, optional): If True, the class's
                _transform_datatype method will not be called.
            **kwargs: Additional keyword arguments are passed to
                _transform_datatype if it is defined.

        Returns:
            dict: Transformed datatype.

        """
        if not isinstance(datatype, datatypes.Datatype):
            datatype = datatypes.Datatype(datatype)
        if (not skip_class_method) and self._transform_datatype is not None:
            return self._transform_datatype(datatype, **kwargs)
        try:
            out = datatypes.Datatype.from_data(
                self(datatype.example_data), minimal=True)
            out_nfields = out.nfields
            if ((out_nfields is not None and not out.field_names
                 and out_nfields == datatype.nfields
                 and datatype.field_names)):
                out.field_names = datatype.field_names
                assert out.field_names == datatype.field_names
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
        from yggdrasil.communication.CommBase import CommMessage, FLAG_EMPTY
        if not no_init:
            self.set_original_datatype_from_data(x)
        if isinstance(x, CommMessage):
            out = CommMessage(flag=x.flag, header=copy.deepcopy(x.header))
            if self._transform_datatype is not None:
                out.stype = self._transform_datatype(x.stype)
            if x.flag == FLAG_EMPTY and out.stype:
                out.args = out.stype.empty_msg
            else:
                out.args = self.evaluate_transform(x.args, **kwargs)
        else:
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
