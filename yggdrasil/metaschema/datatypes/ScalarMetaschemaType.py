import numpy as np
import copy
import warnings
import base64
from yggdrasil import units, constants
from yggdrasil.metaschema import data2dtype, definition2dtype
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.datatypes.FixedMetaschemaType import (
    create_fixed_type_class)
from yggdrasil.metaschema.properties import get_metaschema_property


class ScalarMetaschemaType(MetaschemaType):
    r"""Type associated with a scalar.

    Developer Notes:
        |yggdrasil| defines scalars as an umbrella type encompassing int, uint,
        float, bytes, and unicode.

    """

    name = 'scalar'
    description = 'A scalar value with or without units.'
    properties = ['subtype', 'precision', 'units']
    definition_properties = ['subtype']
    metadata_properties = ['subtype', 'precision', 'units']
    extract_properties = ['subtype', 'precision', 'units']
    python_types = units.ALL_PYTHON_SCALARS_WITH_UNITS

    @classmethod
    def validate(cls, obj, raise_errors=False):
        r"""Validate an object to check if it could be of this type.

        Args:
            obj (object): Object to validate.
            raise_errors (bool, optional): If True, errors will be raised when
                the object fails to be validated. Defaults to False.

        Returns:
            bool: True if the object could be of this type, False otherwise.

        """
        if isinstance(obj, np.ndarray) and (obj.ndim == 0):
            obj = obj.reshape((1, ))[0]
        if super(ScalarMetaschemaType, cls).validate(units.get_data(obj),
                                                     raise_errors=raise_errors):
            dtype = data2dtype(obj)
            if cls.is_fixed and ('subtype' in cls.fixed_properties):
                type_list = [
                    constants.VALID_TYPES[cls.fixed_properties['subtype']]]
            else:
                type_list = constants.NUMPY_TYPES
            if dtype.name.startswith(tuple(type_list)):
                return True
            else:
                if raise_errors:
                    raise ValueError(("dtype %s dosn't corresponding with any "
                                      + "of the accepted types: %s") %
                                     (str(dtype), str(type_list)))
        return False
        
    # @classmethod
    # def coerce_type(cls, obj, typedef=None, **kwargs):
    #     r"""Coerce objects of specific types to match the data type.

    #     Args:
    #         obj (object): Object to be coerced.
    #         typedef (dict, optional): Type defintion that object should be
    #             coerced to. Defaults to None.
    #         **kwargs: Additional keyword arguments are metadata entries that may
    #             aid in coercing the type.

    #     Returns:
    #         object: Coerced object.

    #     """
    #     if ((cls.is_fixed and ('subtype' in cls.fixed_properties)
    #          and (cls.fixed_properties['subtype'] in ['bytes', 'unicode']))):
    #         obj = cls.normalize(obj)
    #     return obj
        
    @classmethod
    def normalize(cls, obj):
        r"""Normalize an object, if possible, to conform to this type.

        Args:
            obj (object): Object to normalize.

        Returns:
            object: Normalized object.

        """
        if cls.is_fixed and ('subtype' in cls.fixed_properties):
            if (cls.fixed_properties['subtype'] == 'bytes'):
                if isinstance(obj, str):
                    obj = obj.encode("utf-8")
                elif not isinstance(obj, bytes):
                    obj = str(obj).encode("utf-8")
            elif (cls.fixed_properties['subtype'] == 'unicode'):
                if isinstance(obj, bytes):
                    obj = obj.decode("utf-8")
                else:
                    obj = str(obj)
            else:
                dtype = units.PYTHON_SCALARS_WITH_UNITS[
                    cls.fixed_properties['subtype']][0]
                try:
                    obj = dtype(obj)
                except (TypeError, ValueError):
                    pass
        return obj

    @classmethod
    def encode_data(cls, obj, typedef):
        r"""Encode an object's data.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        arr = cls.to_array(obj)
        out = base64.encodebytes(arr.tobytes()).decode('ascii')
        return out

    @classmethod
    def encode_data_readable(cls, obj, typedef):
        r"""Encode an object's data in a readable format that may not be
        decoded in exactly the same way.

        Args:
            obj (object): Object to encode.
            typedef (dict): Type definition that should be used to encode the
                object.

        Returns:
            string: Encoded object.

        """
        arr = cls.to_array(obj)
        if isinstance(typedef, dict):
            subtype = typedef.get('subtype', typedef.get('type', None))
        else:
            subtype_cls = get_metaschema_property('subtype')
            subtype = subtype_cls.encode(obj)
        if (cls.name in ['1darray', 'ndarray']):
            return arr.tolist()
        assert(arr.ndim > 0)
        if subtype in ['int', 'uint']:
            return int(arr[0])
        elif subtype in ['float']:
            return float(arr[0])
        elif subtype in ['complex']:
            return str(complex(arr[0]))
        elif subtype in ['bytes', 'unicode']:
            out = arr[0]
            if isinstance(out, bytes):
                out = out.decode("utf-8")
            else:
                out = str(out)
            return out
        else:  # pragma: debug
            warnings.warn(("No method for handling readable serialization of "
                           + "subtype '%s', falling back to default.") % subtype)
            return super(ScalarMetaschemaType, cls).encode_data_readable(obj, typedef)

    @classmethod
    def decode_data(cls, obj, typedef):
        r"""Decode an object.

        Args:
            obj (string): Encoded object to decode.
            typedef (dict): Type definition that should be used to decode the
                object.

        Returns:
            object: Decoded object.

        """
        bytes = base64.decodebytes(obj.encode('ascii'))
        dtype = definition2dtype(typedef)
        arr = np.frombuffer(bytes, dtype=dtype)
        # arr = np.fromstring(bytes, dtype=dtype)
        if 'shape' in typedef:
            arr = arr.reshape(typedef['shape'])
        out = cls.from_array(arr, unit_str=typedef.get('units', None),
                             dtype=dtype, typedef=typedef)
        return out

    @classmethod
    def transform_type(cls, obj, typedef=None):
        r"""Transform an object based on type info.

        Args:
            obj (object): Object to transform.
            typedef (dict, optional): Type definition that should be used to
                transform the object. Defaults to None.

        Returns:
            object: Transformed object.

        """
        if typedef is None:
            return obj
        typedef0 = cls.encode_type(obj)
        typedef1 = copy.deepcopy(typedef0)
        typedef1.update(**typedef)
        dtype = definition2dtype(typedef1)
        arr = cls.to_array(obj).astype(dtype, casting='same_kind')
        out = cls.from_array(arr, unit_str=typedef0.get('units', None),
                             dtype=dtype, typedef=typedef)
        return units.convert_to(out, typedef1.get('units', None))

    @classmethod
    def to_array(cls, obj):
        r"""Get np.array representation of the data.

        Args:
            obj (object): Object to get array for.

        Returns:
            np.ndarray: Array representation of object.

        """
        obj_nounits = units.get_data(obj)
        if isinstance(obj_nounits, np.ndarray):
            arr = obj_nounits
        else:
            dtype = data2dtype(obj_nounits)
            arr = np.array([obj_nounits], dtype=dtype)
        return arr
        
    @classmethod
    def from_array(cls, arr, unit_str=None, dtype=None, typedef=None):
        r"""Get object representation of the data.

        Args:
            arr (np.ndarray): Numpy array.
            unit_str (str, optional): Units that should be added to returned
                object.
            dtype (np.dtype, optional): Numpy data type that should be maintained
                as a base class when adding units. Defaults to None and is
                determined from the object or typedef (if provided).
            typedef (dict, optional): Type definition that should be used to
                decode the object. Defaults to None and is determined from the
                object or dtype (if provided).

        Returns:
            object: Object representation of the data in the input array.

        """
        # if (typedef is None) and (dtype is not None):
        #     typedef = dtype2definition(dtype)
        # elif (dtype is None) and (typedef is not None):
        #     dtype = definition2dtype(typedef)
        if (cls.name not in ['1darray', 'ndarray']) and (arr.ndim > 0):
            out = arr[0]
        else:
            out = arr
        if typedef is not None:
            # Cast numpy type to native python type if they are equivalent
            out = cls.as_python_type(out, typedef)
        if unit_str is not None:
            if dtype is None:
                dtype = data2dtype(out)
            out = units.add_units(out, unit_str, dtype=dtype)
        return out

    @classmethod
    def get_extract_properties(cls, metadata):
        r"""Get the list of properties that should be kept when extracting a
        typedef from message metadata.

        Args:
            metadata (dict): Metadata that typedef is being extracted from.

        Returns:
            list: Keywords that should be kept in the typedef.

        """
        out = super(ScalarMetaschemaType, cls).get_extract_properties(metadata)
        dtype = metadata.get('subtype', metadata['type'])
        if (((dtype in constants.FLEXIBLE_TYPES)
             and (metadata['type'] not in ['1darray', 'ndarray'])
             and (not metadata.get('fixed_precision', False)))):
            out.remove('precision')
        if units.is_null_unit(metadata.get('units', '')):
            out.remove('units')
        return out

    @classmethod
    def as_python_type(cls, obj, typedef):
        r"""Convert a possible numpy type into a native Python type if possible.

        Args:
            obj (object): Object to convert.
            typedef (dict): Type definition for the object.

        Returns:
            object: Native Python version of input object if conversion possible.

        """
        if ((isinstance(typedef, dict)
             and (typedef.get('type', '1darray') not in ['1darray', 'ndarray']))):
            stype = typedef.get('subtype', typedef.get('type', None))
            py_type = units.PYTHON_SCALARS_WITH_UNITS[stype][0]
            if np.dtype(py_type) == type(obj):
                obj = py_type(obj)
        return obj

    @classmethod
    def _generate_data(cls, typedef, numeric_value=None):
        r"""Generate mock data for the specified type.

        Args:
            typedef (dict): Type definition.

        Returns:
            object: Python object of the specified type.

        """
        dtype = definition2dtype(typedef)
        subtype = typedef.get('subtype', typedef['type'])
        if subtype in ['bytes', 'unicode']:
            if subtype == 'bytes':
                value = b'x' * int(typedef['precision'] / 8)
            else:
                value = 'x' * int(typedef['precision'] / 32)
        elif numeric_value is not None:
            value = numeric_value
        else:
            value = 1.0
        if typedef['type'] == '1darray':
            out = np.repeat(np.array([value], dtype),
                            typedef.get('length', 2))
        elif typedef['type'] == 'ndarray':
            out = np.tile(np.array([value], dtype),
                          typedef.get('shape', (4, 5)))
        else:
            out = np.array([value], dtype)[0]
        out = units.add_units(out, typedef.get('units', ''))
        return out

    @classmethod
    def get_test_data(cls, typedef=None):
        r"""object: Test data."""
        if typedef is None:
            typedef = {'type': cls.name}
        if not hasattr(cls, 'fixed_properties'):
            typedef.setdefault('subtype', 'float')
        subtype = typedef.get('subtype', typedef['type'])
        if subtype in ['bytes', 'unicode']:
            typedef.setdefault('precision', 3 * 32)
        elif subtype == 'complex':
            typedef.setdefault('precision', 64)
        else:
            typedef.setdefault('precision', 32)
        return super(ScalarMetaschemaType, cls).get_test_data(typedef)


# Dynamically create explicity scalar classes for shorthand
for t in constants.VALID_TYPES.keys():
    short_doc = 'A %s value with or without units.' % t
    long_doc = ('%s\n\n'
                '    Developer Notes:\n'
                '        Precision X is preserved.\n\n') % short_doc
    kwargs = {'target_globals': globals(),
              '__doc__': long_doc,
              '__module__': ScalarMetaschemaType.__module__,
              'python_types': units.PYTHON_SCALARS_WITH_UNITS[t]}
    create_fixed_type_class(t, short_doc, ScalarMetaschemaType,
                            {'subtype': t}, **kwargs)
