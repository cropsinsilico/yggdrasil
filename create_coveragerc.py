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


def create_coveragerc(matlab_installed=False, lpy_installed=False):
    r"""Create the coveragerc to reflect the OS, Python version, and availability
    of matlab. Parameters from the setup.cfg file will be added. If the
    .coveragerc file already exists, it will be read first before adding setup.cfg
    options.
    

    Args:
        matlab_installed (bool, optional): Truth of if matlab is installed or not.
            Defaults to False.
        lpy_installed (bool, optional): Truth of if lpy is installed or not.
            Defaults to False.

    Returns:
        bool: True if the file was created/updated successfully, False otherwise.

    """
    if HandyConfigParser is None:
        return False
    covrc = os.path.join(os.path.dirname(__file__), '.coveragerc')
    cp = HandyConfigParser("")
    # Read from existing .coveragerc
    if os.path.isfile(covrc):
        cp.read(covrc)
    # Read options from setup.cfg
    setup_cfg = os.path.join(os.path.dirname(__file__), 'setup.cfg')
    cp_cfg = HandyConfigParser("")
    cp_cfg.read(setup_cfg)
    # Transfer options
    for x in cp_cfg.sections():
        if x.startswith('coverage:'):
            sect_cp = x.split('coverage:')[-1]
            if not cp.has_section(sect_cp):
                cp.add_section(sect_cp)
            for opt in cp_cfg.options(x):
                if cp.has_option(sect_cp, opt):
                    val_old = [l.strip() for l in cp.get(sect_cp, opt).split('\n')]
                    val_new = [l.strip() for l in cp_cfg.get(x, opt).split('\n')]
                    for v in val_new:
                        if v not in val_old:
                            val_old.append(v)
                    opt_new = '\n'.join(val_old)
                else:
                    opt_new = cp_cfg.get(x, opt)
                cp.set(sect_cp, opt, opt_new)
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
    flag = create_coveragerc(matlab_installed=matlab_installed,
                             lpy_installed=lpy_installed)
    if not flag:
        raise Exception("Failed to create/update converagerc file.")
