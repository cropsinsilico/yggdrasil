import re
import numpy as np
import pandas as pd
import unyt
from collections import OrderedDict
from yggdrasil import tools, constants
_unit_quantity = unyt.array.unyt_quantity
_unit_array = unyt.array.unyt_array
_ureg_unyt = None


PYTHON_SCALARS_WITH_UNITS = OrderedDict([
    (k, tuple(list(v) + [_unit_quantity]))
    for k, v in constants.PYTHON_SCALARS.items()])
ALL_PYTHON_ARRAYS_WITH_UNITS = tuple(
    list(constants.ALL_PYTHON_ARRAYS) + [_unit_array])
ALL_PYTHON_SCALARS_WITH_UNITS = tuple(
    list(constants.ALL_PYTHON_SCALARS) + [_unit_quantity])


def get_ureg():
    r"""Get the unit registry."""
    global _ureg_unyt
    if _ureg_unyt is None:
        _ureg_unyt = unyt.UnitRegistry('mks')
        _ureg_unyt.add("ac", 4046.86, dimensions=unyt.dimensions.area,
                       tex_repr=r"\rm{ac}", offset=0.0, prefixable=False)
        _ureg_unyt.add("a", 100.0, dimensions=unyt.dimensions.area,
                       tex_repr=r"\rm{a}", offset=0.0, prefixable=True)
        _ureg_unyt.add("j", 1.0, dimensions=unyt.dimensions.energy,
                       tex_repr=r"\rm{J}", offset=0.0, prefixable=True)
        # _ureg_unyt.add("cel", 1.0, dimensions=unyt.dimensions.temperature,
        #                tex_repr=r"^\circ\rm{C}", offset=-273.15, prefixable=True)
        # _ureg_unyt.add("j", 1.0, dimensions=unyt.dimensions.specific_flux,
        #                tex_repr=r"\rm{Jy}", prefixable=True)
        # _ureg_unyt.add("CH2O", 1.0, dimensions=unyt.dimensions.dimensionless,
        #                tex_repr=r"\rm{CH2O}", offset=0.0, prefixable=False)
        unyt._unit_lookup_table.inv_name_alternatives["acre"] = "ac"
        unyt._unit_lookup_table.inv_name_alternatives["are"] = "a"
        unyt._unit_lookup_table.inv_name_alternatives["hectare"] = "ha"
        unyt._unit_lookup_table.inv_name_alternatives["days"] = "day"
    return _ureg_unyt


def convert_to_pandas_timedelta(x):
    r"""Convert variable with time units to a pandas.Timedelta instance.

    Args:
        x (object): Scalar/array with units to convert to a pandas.Timedelta
            instance.

    Returns:
        pandas.Timedelta: Equivalent Timedelta variable.

    """
    assert(has_units(x))
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


def convert_R_unit_string(r_str):
    r"""Convert R unit string to string that the Python package can
    understand.

    Args:
        r_str (str): R units string to convert.

    Returns:
        str: Converted string.

    """
    return convert_unit_string(r_str)


def convert_unit_string(orig_str, replacements=None):
    r"""Convert unit string to string that the Python package can
    understand.

    Args:
        orig_str (str): Original units string to convert.
        replacements (dict, optional): Mapping from unit to another.
            Defaults to empty dict.

    Returns:
        str: Converted string.

    """
    if not orig_str.strip():
        return ''
    out = []
    if replacements is None:
        replacements = {'h': 'hr',
                        'hrs': 'hr',
                        'days': 'day',
                        '100%': 'percent'}
    regex_mu = [tools.bytes2str(b'\xc2\xb5'),
                tools.bytes2str(b'\xce\xbcs'),
                tools.bytes2str(b'\xc2\xb0'),
                r'(?:100\%)']
    regex = (r'(?P<paren>\()?(?P<name>[A-Za-z%s]+)'
             r'(?:(?:(?:\^)|(?:\*\*))?(?P<exp_paren>\()?(?P<exp>-?[0-9]+)'
             r'(?(exp_paren)\)))?'
             r'(?(paren)\)|)(?P<op> |(?:\*)|(?:\/))?' % ''.join(regex_mu))
    out = ''
    if re.fullmatch(r'(?:%s)+' % regex, orig_str.strip()):
        for x in re.finditer(regex, orig_str.strip()):
            xdict = x.groupdict()
            if xdict['name'] in replacements:
                xdict['name'] = replacements[xdict['name']]
            if xdict['exp']:
                out += '({name}**{exp})'.format(**xdict)
            else:
                out += xdict['name']
            if xdict['op']:
                if xdict['op'].isspace():
                    xdict['op'] = '*'
                out += xdict['op']
    else:  # pragma: debug
        print(repr(orig_str), type(orig_str))
        m = re.search(r'(?:%s)+' % regex, orig_str.strip())
        if m:
            print(repr(m.group(0)), m.groupdict())
        else:
            print('no match')
        for m in re.finditer(regex, orig_str.strip()):
            print(m.group(0), m.groupdict())
        raise Exception("Could not standardize units: %s" % repr(orig_str))
    return out


def has_units(obj, check_dimensionless=False):
    r"""Determine if a Python object has associated units.

    Args:
        obj (object): Object to be tested for units.
        check_dimensionless (bool, optional): If True, an object with
            dimensionless units will return True.

    Returns:
        bool: True if the object has units, False otherwise.

    """
    out = isinstance(obj, (_unit_quantity, _unit_array))
    # out = hasattr(obj, 'units')
    if ((out and (obj.units == as_unit('dimensionless'))
         and (not check_dimensionless))):
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
    if has_units(obj, check_dimensionless=True):
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
    ureg = get_ureg()
    unit_str = tools.bytes2str(unit_str)
    if is_null_unit(unit_str):
        return arr
    unit_str = convert_unit_string(unit_str)
    if has_units(arr):
        return convert_to(arr, unit_str)
    if dtype is None:
        if isinstance(arr, np.ndarray):
            dtype = arr.dtype
        else:
            dtype = np.array([arr]).dtype
    try:
        if isinstance(arr, np.ndarray) and (arr.ndim > 0):
            out = unyt.unyt_array(arr, unit_str, dtype=dtype,
                                  registry=ureg)
        else:
            out = unyt.unyt_quantity(arr, unit_str, dtype=dtype,
                                     registry=ureg)
    except BaseException:
        raise ValueError("Error parsing unit: %s, type(%s)."
                         % (repr(unit_str), type(unit_str)))
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
        out = unyt.Unit(ustr, registry=get_ureg())
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
    r"""Convert quantity with units to new units. Objects without units
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
    new_units = convert_unit_string(new_units)
    try:
        arr1 = get_data(arr)
        dtype = get_data(arr1).dtype
        out = arr.to(new_units)
        arr2 = get_data(out)
        equal = (arr2.dtype == dtype)
        if not equal:
            out = add_units(arr2, new_units, dtype=dtype)
    except unyt.exceptions.UnitConversionError as e:
        raise ValueError(str(e))
    return out


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
