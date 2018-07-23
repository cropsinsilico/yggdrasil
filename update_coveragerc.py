import os
import sys
PY_MAJOR_VERSION = sys.version_info[0]
IS_WINDOWS = (sys.platform in ['win32', 'cygwin'])
# Import config parser
try:
    from ConfigParser import RawConfigParser as HandyConfigParser
except ImportError:
    try:
        from configparser import RawConfigParser as HandyConfigParser
    except ImportError:
        HandyConfigParser = None


def add_excl_rule(excl_list, new_rule):
    r"""Add an exclusion rule to the list if its not in there.

    Args:
        excl_list (list): List of exclusion rules to update.
        new_rule (str): New rule to add to the list if it already exists.

    Returns:
        list: Updated exclustion rules.

    """
    if new_rule not in excl_list:
        excl_list.append(new_rule)
    return excl_list


def rm_excl_rule(excl_list, new_rule):
    r"""Remove an exclusion rule from the list if its in there.

    Args:
        excl_list (list): List of exclusion rules to update.
        new_rule (str): New rule to remove from the list if it exists.

    Returns:
        list: Updated exclustion rules.

    """
    if new_rule in excl_list:
        excl_list.remove(new_rule)
    return excl_list


def update_coveragerc(matlab_installed=False, lpy_installed=False):
    r"""Update the coveragerc to reflect the OS, Python version, and availability
    of matlab.

    Args:
        matlab_installed (bool, optional): Truth of if matlab is installed or not.
            Defaults to False.
        lpy_installed (bool, optional): Truth of if lpy is installed or not.
            Defaults to False.

    Returns:
        bool: True if the file was updated successfully, False otherwise.

    """
    if HandyConfigParser is None:
        return False
    # Read options
    covrc = os.path.join(os.path.dirname(__file__), '.coveragerc')
    cp = HandyConfigParser("")
    cp.read(covrc)
    # Exclude rules for all files
    if not cp.has_section('report'):
        cp.add_section('report')
    if cp.has_option('report', 'exclude_lines'):
        excl_str = cp.get('report', 'exclude_lines')
        excl_list = excl_str.strip().split('\n')
    else:
        excl_list = []
    # Platform
    if IS_WINDOWS:
        excl_list = rm_excl_rule(excl_list, 'pragma: windows')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: windows')
    # Python version
    verlist = [2, 3]
    for v in verlist:
        vincl = 'pragma: Python %d' % v
        if PY_MAJOR_VERSION == v:
            excl_list = rm_excl_rule(excl_list, vincl)
        else:
            excl_list = add_excl_rule(excl_list, vincl)
    # Matlab
    if matlab_installed:
        excl_list = add_excl_rule(excl_list, 'pragma: no matlab')
        excl_list = rm_excl_rule(excl_list, 'pragma: matlab')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: matlab')
        excl_list = rm_excl_rule(excl_list, 'pragma: no matlab')
    # LPy
    if lpy_installed:
        excl_list = add_excl_rule(excl_list, 'pragma: no lpy')
        excl_list = rm_excl_rule(excl_list, 'pragma: lpy')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: lpy')
        excl_list = rm_excl_rule(excl_list, 'pragma: no lpy')
    # Add new rules
    cp.set('report', 'exclude_lines', '\n' + '\n'.join(excl_list))
    # Write
    with open(covrc, 'w') as fd:
        cp.write(fd)
    return True


if __name__ == "__main__":
    try:
        import matlab.engine
        matlab_installed = True
    except ImportError:
        matlab_installed = False
    try:
        from openalea import lpy
        lpy_installed = True
    except ImportError:
        lpy_installed = False
    flag = update_coveragerc(matlab_installed=matlab_installed,
                             lpy_installed=lpy_installed)
    if not flag:
        raise Exception("Failed to update converagerc file.")
