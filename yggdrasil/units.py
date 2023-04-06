import re
import numpy as np
import pandas as pd
import deprecation
from collections import OrderedDict
from ._version import get_versions
from yggdrasil import tools, constants
from yggdrasil.rapidjson import units as units_
# Use get_versions to prevent circular import from importing it
#   from yggdrasil's __init__
__version__ = get_versions()['version']
# TODO: This import fails saying yggdrasil.rapidjson is not a package so
# we need to find a work around
# from yggdrasil.rapidjson.units import Quantity, QuantityArray, Units, UnitsError
Quantity = units_.Quantity
QuantityArray = units_.QuantityArray
Units = units_.Units
UnitsError = units_.UnitsError
_unit_quantity = Quantity
_unit_array = QuantityArray


PYTHON_SCALARS_WITH_UNITS = OrderedDict([
    (k, tuple(list(v) + [_unit_quantity]))
    for k, v in constants.PYTHON_SCALARS.items()])
ALL_PYTHON_ARRAYS_WITH_UNITS = tuple(
    list(constants.ALL_PYTHON_ARRAYS) + [_unit_array])
ALL_PYTHON_SCALARS_WITH_UNITS = tuple(
    list(constants.ALL_PYTHON_SCALARS) + [_unit_quantity])


def convert_to_pandas_timedelta(x):
    r"""Convert variable with time units to a pandas.Timedelta instance.

    Args:
        x (object): Scalar/array with units to convert to a pandas.Timedelta
            instance.

    Returns:
        pandas.Timedelta: Equivalent Timedelta variable.

    """
    assert has_units(x)
    t_data = get_data(x)
    t_unit = get_units(x)
    unit_map = {'ns': 'ns',
                (tools.bytes2str(b'\xc2\xb5') + 's'): 'us',
                (tools.bytes2str(b'\xce\xbcs') + 's'): 'us',
                'ms': 'ms',
                's': 's',
                'min': 'm',
                'hr': 'h',
                'day': 'D'}
    return pd.Timedelta(t_data, unit=unit_map[t_unit])


def convert_from_pandas_timedelta(x):
    r"""Covert a pandas.Timedelta instance to a scalar/array with
    time units.

    Args:
        x (pandas.Timedelta): Timedelta variable to convert.

    Returns:
        object: Equivalent scalar/array with units.

    """
    return add_units(x.total_seconds(), 's')


def convert_julia_unit_string(in_str):  # pragma: julia
    r"""Convert unit string to version that julia Unitful package can
    understand.

    Args:
        in_str (str): String unit to convert.

    Returns:
        str: Converted string.

    """
    replacements = [('**', '^'),
                    ('days', 'd'),
                    ('day', 'd'),
                    ('degC', '°C'),
                    ('degF', '°F')]
    out = in_str
    for a, b in replacements:
        out = out.replace(a, b)
    return out


def convert_matlab_unit_string(m_str):  # pragma: matlab
    r"""Convert Matlab unit string to string that the Python package
    can understand.

    Args:
        m_str (str): Matlab units string to convert.

    Returns:
        str: Converted string.

    """
    out = m_str
    replacements = {'h': 'hr'}
    regex_mu = [tools.bytes2str(b'\xc2\xb5'),
                tools.bytes2str(b'\xce\xbcs')]
    regex = r'(?P<name>[A-Za-z%s]+)' % ''.join(regex_mu)
    for x in re.finditer(regex, m_str):
        xdict = x.groupdict()
        if xdict['name'] in replacements:
            xdict['name'] = replacements[xdict['name']]
            out = out[:(x.start())] + xdict['name'] + out[(x.end()):]
    return out


@deprecation.deprecated(deprecated_in="2.0", removed_in="3.0",
                        current_version=__version__,
                        details=("This method is no longer necessary and "
                                 "units can be parsed directly"))
def convert_R_unit_string(r_str):  # pragma: deprecated
    r"""Convert R unit string to string that the Python package can
    understand.

    Args:
        r_str (str): R units string to convert.

    Returns:
        str: Converted string.

    """
    return convert_unit_string(r_str)


@deprecation.deprecated(deprecated_in="2.0", removed_in="3.0",
                        current_version=__version__,
                        details=("This method is no longer necessary and "
                                 "units can be parsed directly"))
def convert_unit_string(orig_str, replacements=None):  # pragma: deprecated
    r"""Convert unit string to string that the Python package can
    understand.

    Args:
        orig_str (str): Original units string to convert.
        replacements (dict, optional): Mapping from unit to another.
            Defaults to empty dict.

    Returns:
        str: Converted string.

    """
    return orig_str


def has_units(obj, check_dimensionless=False):
    r"""Determine if a Python object has associated units.

    Args:
        obj (object): Object to be tested for units.
        check_dimensionless (bool, optional): If True, an object with
            dimensionless units will return True.

    Returns:
        bool: True if the object has units, False otherwise.

    """
    out = (isinstance(obj, (_unit_quantity, _unit_array))
           and not (obj.is_dimensionless()
                    and (not check_dimensionless)))
    # out = hasattr(obj, 'units')
    return out


def get_units(obj, for_language=None):
    r"""Get the string representation of the units.

    Args:
        obj (object): Object to get units for.
        for_language (str, optional): Language requesting units.

    Returns:
        str: Units, empty if input object has none.
        
    """
    if has_units(obj):
        out = str(obj.units)
    else:
        out = ''
    if for_language == "R":  # pragma: extern
        # udunits dosn't support Δ
        out = out.replace('Δ', '')
    return out


def get_data(obj):
    r"""Get the array/scalar assocaited with the object.

    Args:
        obj (object): Object to get data for.

    Returns:
        np.ndarray: Numpy array representation of the underlying data.

    """
    if has_units(obj, check_dimensionless=True):
        out = obj.value
    else:
        out = obj
    return out


def add_units(arr, unit_str, **kwargs):
    r"""Add units to an array or scalar.

    Args:
        arr (np.ndarray, float, int): Scalar or array of data to add units to.
        unit_str (str): Unit string.
        **kwargs: Additional keyword arguments are passed to the unit constructor.

    Returns:
        Quantity ro QuantityArray: Scalar or array with units.

    """
    if is_null_unit(unit_str):
        return arr
    if has_units(arr):
        out = convert_to(arr, unit_str)
    elif isinstance(arr, np.ndarray) and (arr.ndim > 0):
        out = QuantityArray(arr, unit_str, **kwargs)
    else:
        out = Quantity(arr, unit_str, **kwargs)
    return out


def are_compatible(units1, units2):
    r"""Check if two units are compatible.

    Args:
        units1 (str): First units string.
        units2 (str): Second units string.

    Returns:
        bool: True if the units are compatible, False otherwise.

    """
    # Empty units always compatible
    try:
        u1 = Units(units1)
        u2 = Units(units2)
    except UnitsError:
        return False
    if u1.is_dimensionless() or u2.is_dimensionless():
        return True
    return u1.is_compatible(u2)


def is_null_unit(ustr):
    r"""Determines if a string is a null unit.

    Args:
        ustr (str): String to test.

    Returns:
        bool: True if the string is '' or 'n/a', False otherwise.

    """
    return Units(ustr).is_dimensionless()


def as_unit(ustr):
    r"""Get unit object for the string.

    Args:
        ustr (str): Unit string.

    Returns:
        Units: Unit object.

    Raises:
        ValueError: If the string is not a recognized unit.

    """
    return Units(ustr)


def is_unit(ustr):
    r"""Determine if a string is a valid unit.

    Args:
        ustr (str): String representation to test.

    Returns:
        bool: True if the string is a valid unit. False otherwise.

    """
    try:
        as_unit(ustr)
        return True
    except UnitsError:
        return False


def convert_to(arr, new_units):
    r"""Convert quantity with units to new units. Objects without units
    will be returned with the new units.

    Args:
        arr (np.ndarray, float, int, Quantity, QuantityArray): Quantity with
            or without units.
        new_units (str): New units that should be applied.

    Returns:
        Quantity, QuantityArray: Scalar or array with new units.

    """
    if not has_units(arr):
        return add_units(arr, new_units)
    return arr.to(new_units)


def get_conversion_function(old_units, new_units):
    r"""Get a function that will convert a scalar/array from one unit
    to another.

    Args:
        old_units (str): Units to convert from.
        new_units (str): Units to convert to.

    Returns:
        function: Conversion function that takes scalar/array as input
            and returns converted scalar/array.

    """
    def fconvert(x):
        ux = add_units(x, old_units)
        return get_data(convert_to(ux, new_units))
    return fconvert
