import numpy as np
from yggdrasil import backwards
if backwards.PY2:  # pragma: Python 2
    import pint
    unyt = None
    _use_unyt = False
    _ureg_unyt = None
    _ureg_pint = pint.UnitRegistry()
    # _ureg_pint.define('micro_mole = 1e-6 * mole = uMol = umol')
    _ureg_pint.define('day = 24 * hour = d')
else:  # pragma: Python 3
    import unyt
    pint = None
    _use_unyt = True
    _ureg_unyt = unyt.UnitRegistry()
    _ureg_pint = None
if _use_unyt:
    _unit_quantity = unyt.array.unyt_quantity
    _unit_array = unyt.array.unyt_array
else:
    _unit_quantity = _ureg_pint.Quantity
    _unit_array = _ureg_pint.Quantity


def has_units(obj):
    r"""Determine if a Python object has associated units.

    Args:
        obj (object): Object to be tested for units.

    Returns:
        bool: True if the object has units, False otherwise.

    """
    return hasattr(obj, 'units')


def get_units(obj):
    r"""Get the string representation of the units.

    Args:
        obj (object): Object to get units for.

    Returns:
        str: Units, empty if input object has none.
        
    """
    if has_units(obj):
        out = str(obj.units)
    else:
        out = ''
    return out


def get_data(obj):
    r"""Get the array/scalar assocaited with the object.

    Args:
        obj (object): Object to get data for.

    Returns:
        np.ndarray: Numpy array representation of the underlying data.

    """
    if has_units(obj):
        if _use_unyt:
            out = obj.to_ndarray()
            if out.ndim == 0:
                out = out.reshape((1, ))[0]
        else:
            out = obj.magnitude
    else:
        out = obj
    return out


def add_units(arr, unit_str, dtype=None):
    r"""Add units to an array or scalar.

    Args:
        arr (np.ndarray, float, int): Scalar or array of data to add units to.
        unit_str (str): Unit string.
        dtype (np.dtype, optional): Numpy data type that should be maintained for
            array/qunatity with units. If not provided, this is determined from the
            array.

    Returns:
        unyt.unyt_array: Array with units.

    """
    if isinstance(unit_str, backwards.bytes_type):
        unit_str = backwards.as_str(unit_str)
    if is_null_unit(unit_str):
        return arr
    if dtype is None:
        if isinstance(arr, np.ndarray):
            dtype = arr.dtype
        else:
            dtype = np.array([arr]).dtype
    if _use_unyt:
        if isinstance(arr, np.ndarray) and (arr.ndim > 0):
            out = unyt.unyt_array(arr, unit_str, dtype=dtype)
        else:
            out = unyt.unyt_quantity(arr, unit_str, dtype=dtype)
    else:
        out = _ureg_pint.Quantity(arr, unit_str)
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
    if is_null_unit(units1) or is_null_unit(units2):
        return True
    if (not is_unit(units1)) or (not is_unit(units2)):
        return False
    x = add_units(1, units1)
    try:
        convert_to(x, units2)
    except ValueError:
        return False
    return True


def is_null_unit(ustr):
    r"""Determines if a string is a null unit.

    Args:
        ustr (str): String to test.

    Returns:
        bool: True if the string is '' or 'n/a', False otherwise.

    """
    if (len(ustr) == 0) or (ustr == 'n/a'):
        return True
    return False


def as_unit(ustr):
    r"""Get unit object for the string.

    Args:

    Returns:

    Raises:
        ValueError: If the string is not a recognized unit.

    """
    if _use_unyt:
        try:
            out = unyt.Unit(ustr)
        except unyt.exceptions.UnitParseError as e:
            raise ValueError(str(e))
    else:
        try:
            out = _ureg_pint(ustr)
        except pint.errors.UndefinedUnitError as e:
            raise ValueError(str(e))
    return out


def is_unit(ustr):
    r"""Determine if a string is a valid unit.

    Args:
        ustr (str): String representation to test.

    Returns:
        bool: True if the string is a valid unit. False otherwise.

    """
    ustr = backwards.as_str(ustr)
    if is_null_unit(ustr):
        return True
    try:
        as_unit(ustr)
    except ValueError:
        return False
    return True


def convert_to(arr, new_units):
    r"""Convert qunatity with units to new units. Objects without units
    will be returned with the new units.

    Args:
        arr (np.ndarray, float, int, unyt.unyt_array): Quantity with or
            without units.
        new_units (str): New units that should be applied.

    Returns:
        unyt.unyt_array: Array with new units.

    """
    if is_null_unit(new_units):
        return arr
    if not has_units(arr):
        return add_units(arr, new_units)
    if _use_unyt:
        try:
            out = arr.to(new_units)
        except unyt.exceptions.UnitConversionError as e:
            raise ValueError(str(e))
    else:
        out = arr.to(new_units)
    return out
