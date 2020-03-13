import re
import numpy as np
import unyt
from yggdrasil import tools
_ureg_unyt = unyt.UnitRegistry('mks')
_unit_quantity = unyt.array.unyt_quantity
_unit_array = unyt.array.unyt_array
_ureg_unyt.add("ac", 4046.86, dimensions=unyt.dimensions.area,
               tex_repr=r"\rm{ac}", offset=0.0, prefixable=False)
_ureg_unyt.add("a", 100.0, dimensions=unyt.dimensions.area,
               tex_repr=r"\rm{a}", offset=0.0, prefixable=True)
unyt._unit_lookup_table.inv_name_alternatives["acre"] = "ac"
unyt._unit_lookup_table.inv_name_alternatives["are"] = "a"
unyt._unit_lookup_table.inv_name_alternatives["hectare"] = "ha"


def convert_R_unit_string(r_str):
    r"""Convert R unit string to string that the Python package can
    understand.

    Args:
        r_str (str): R units string to convert.

    Returns:
        str: Converted string.

    """
    out = []
    regex_mu = tools.bytes2str(b'\xc2\xb5')
    regex = r'(?P<name>[A-Za-z%s]+)(?P<exp>-?[0-9]*)(?: |$)' % regex_mu
    for x in re.finditer(regex, r_str):
        xdict = x.groupdict()
        if xdict['exp']:
            out.append('({name}**{exp})'.format(**xdict))
        else:
            out.append(xdict['name'])
    return '*'.join(out)


def has_units(obj):
    r"""Determine if a Python object has associated units.

    Args:
        obj (object): Object to be tested for units.

    Returns:
        bool: True if the object has units, False otherwise.

    """
    out = hasattr(obj, 'units')
    if out and (obj.units == as_unit('dimensionless')):
        out = False
    return out


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
        out = obj.to_ndarray()
        if out.ndim == 0:
            out = out.reshape((1, ))[0]
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
    unit_str = tools.bytes2str(unit_str)
    if is_null_unit(unit_str):
        return arr
    if has_units(arr):
        return convert_to(arr, unit_str)
    if dtype is None:
        if isinstance(arr, np.ndarray):
            dtype = arr.dtype
        else:
            dtype = np.array([arr]).dtype
    if isinstance(arr, np.ndarray) and (arr.ndim > 0):
        out = unyt.unyt_array(arr, unit_str, dtype=dtype,
                              registry=_ureg_unyt)
    else:
        out = unyt.unyt_quantity(arr, unit_str, dtype=dtype,
                                 registry=_ureg_unyt)
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
        ustr (str): Unit string.

    Returns:
        unyt.Unit: Unit object.

    Raises:
        ValueError: If the string is not a recognized unit.

    """
    try:
        out = unyt.Unit(ustr, registry=_ureg_unyt)
    except unyt.exceptions.UnitParseError as e:
        raise ValueError(str(e))
    return out


def is_unit(ustr):
    r"""Determine if a string is a valid unit.

    Args:
        ustr (str): String representation to test.

    Returns:
        bool: True if the string is a valid unit. False otherwise.

    """
    ustr = tools.bytes2str(ustr)
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
    try:
        out = arr.to(new_units)
    except unyt.exceptions.UnitConversionError as e:
        raise ValueError(str(e))
    return out
