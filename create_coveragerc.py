import os
import sys
import site
import argparse
PY_MAJOR_VERSION = sys.version_info[0]
IS_WINDOWS = (sys.platform in ['win32', 'cygwin'])
_on_gha = bool(os.environ.get('GITHUB_ACTIONS', False))
_on_travis = bool(os.environ.get('TRAVIS_OS_NAME', False))
_on_appveyor = bool(os.environ.get('APPVEYOR_BUILD_FOLDER', False))
# _on_ci = (_on_gha or _on_travis or _on_appveyor)
# Import config parser
try:
    from ConfigParser import RawConfigParser as HandyConfigParser
except ImportError:
    try:
        from configparser import RawConfigParser as HandyConfigParser
    except ImportError:
        HandyConfigParser = None
_package_dir = os.path.join(site.getsitepackages()[0], 'yggdrasil')
if os.path.isdir(_package_dir):
    ADD_PATH = _package_dir
else:
    ADD_PATH = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'yggdrasil')
try:
    from yggdrasil import constants
except ImportError:
    sys.path.insert(0, ADD_PATH)
    try:
        import constants
    finally:
        sys.path.pop(0)
_install_languages = None


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


def import_install_languages():
    r"""Import install_languages from yggdrasil."""
    global _install_languages
    if _install_languages is None:
        if os.path.isdir(_package_dir):
            from yggdrasil.languages import install_languages
        else:
            LANG_PATH = os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                'yggdrasil', 'languages')
            sys.path.insert(0, LANG_PATH)
            try:
                import install_languages
            finally:
                sys.path.pop(0)
        _install_languages = install_languages
    return _install_languages


def get_covered_languages(from_env=False, args=None, **kwargs):
    r"""Get a dictionary of languages that should be covered.

    Args:
        from_env (bool, optional): If True, the environment is checked for
            variables of the form "INSTALL{LANGUAGE}" and the language is
            covered if the value is '1'. If False, only installed languages
            are covered.
        **kwargs: Additional keyword arguments are checked for arguments
            of the form "cover_{LANGUAGE}" and the language is covered if
            the value is True. Passed arguments override values set from
            checking the environment and the installed languages.

    """
    out = {}
    if from_env:
        for k in constants.LANGUAGES['all']:
            v = os.environ.get(f"INSTALL{k.upper()}", None)
            if v is not None:
                out[k] = (v == '1')
    else:
        out = import_install_languages().install_all_languages(args=args)
    # Override with passed arguments or set default to False
    for k, v in constants.ALIASED_LANGUAGES.items():
        for kalias in v:
            if f"cover_{kalias}" in kwargs:
                kwargs[f"cover_{k}"] = kwargs.pop(f"cover_{kalias}")
    for k in constants.LANGUAGES['all']:
        if f"cover_{k}" in kwargs:
            out[k] = kwargs.pop(f"cover_{k}")
        else:
            out.setdefault(k, False)
    if kwargs:
        import pprint
        raise AssertionError(f"kwargs contains unused arguments: "
                             f"{pprint.pformat(kwargs)}")
    return out


def create_coveragerc(installed_languages):
    r"""Create the coveragerc to reflect the OS, Python version, and availability
    of matlab. Parameters from the setup.cfg file will be added. If the
    .coveragerc file already exists, it will be read first before adding setup.cfg
    options.
    

    Args:
        installed_languages (dict): Dictionary of language/boolean key/value
            pairs indicating optional languages and their state of installation.

    Returns:
        bool: True if the file was created/updated successfully, False otherwise.

    """
    if HandyConfigParser is None:
        return False
    debug_msg = 'cwd = %s, os.path.dirname(__file__) = %s' % (
        os.getcwd(), os.path.dirname(__file__))
    print(debug_msg)
    # covdir = os.path.dirname(__file__)
    covdir = os.getcwd()
    covrc = os.path.join(covdir, '.coveragerc')
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
                    val_old = [line.strip() for line in
                               cp.get(sect_cp, opt).split('\n')]
                    val_new = [line.strip() for line in
                               cp_cfg.get(x, opt).split('\n')]
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
    # Operating system
    if IS_WINDOWS:
        excl_list = rm_excl_rule(excl_list, 'pragma: windows')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: windows')
    # CI Platform
    if _on_gha:
        excl_list = rm_excl_rule(excl_list, 'pragma: gha')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: gha')
    if _on_travis:
        excl_list = rm_excl_rule(excl_list, 'pragma: travis')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: travis')
    if _on_appveyor:
        excl_list = rm_excl_rule(excl_list, 'pragma: appveyor')
    else:
        excl_list = add_excl_rule(excl_list, 'pragma: appveyor')
    # Python version
    verlist = [2, 3]
    for v in verlist:
        vincl = 'pragma: Python %d' % v
        if PY_MAJOR_VERSION == v:
            excl_list = rm_excl_rule(excl_list, vincl)
        else:
            excl_list = add_excl_rule(excl_list, vincl)
    # Language specific
    for k, v in installed_languages.items():
        if v:
            excl_list = add_excl_rule(excl_list, 'pragma: no %s' % k)
            excl_list = rm_excl_rule(excl_list, 'pragma: %s' % k)
        else:
            excl_list = add_excl_rule(excl_list, 'pragma: %s' % k)
            excl_list = rm_excl_rule(excl_list, 'pragma: no %s' % k)
    # Add new rules
    cp.set('report', 'exclude_lines', '\n' + '\n'.join(excl_list))
    # Set include path so that filenames in the report are absolute
    if os.path.isdir(_package_dir):
        PACKAGE_DIR = _package_dir
    else:
        PACKAGE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                   'yggdrasil')
    section = 'source'
    if section == 'include':
        section_path = os.path.join(PACKAGE_DIR, '*')
    else:
        section_path = PACKAGE_DIR
    if not cp.has_section('run'):
        cp.add_section('run')
    incl_list = []
    if cp.has_option('run', section):
        incl_list = cp.get('run', section).strip().split('\n')
    incl_list.append(section_path)
    cp.set('run', section, '\n' + '\n'.join(incl_list))
    # Write
    with open(covrc, 'w') as fd:
        cp.write(fd)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Create a coverage file based on the installed languages.")
    parser.add_argument(
        '--from-env', action='store_true',
        help='Determine covered languages from environment variables')
    for k in constants.LANGUAGES['all']:
        parser.add_argument(
            f'--cover-{k}', action='store_true',
            help=f"Enable coverage of {k} language")
    for k in constants.LANGUAGES['all']:
        parser.add_argument(
            f'--dont-cover-{k}', action='store_true',
            help=(f"Disable coverage of {k} language (this overrides "
                  f"--cover-{k}"))
    arglist = sys.argv[1:]
    add_args = (('-h' in arglist) or ('--help' in arglist)
                or not parser.parse_known_args(args=arglist)[0].from_env)
    if add_args:
        install_languages = import_install_languages()
        for x in install_languages.get_language_directories():
            with install_languages.import_language_install(
                    x.lower()) as install:
                if hasattr(install, 'update_argparser'):
                    parser = install.update_argparser(parser)
    args = parser.parse_args(args=arglist)
    kwargs = {
        f'cover_{k}': True for k in constants.LANGUAGES['all']
        if getattr(args, f'cover_{k}', False)}
    kwargs.update({
        f'cover_{k}': False for k in constants.LANGUAGES['all']
        if getattr(args, f'dont_cover_{k}', False)})
    covered_languages = get_covered_languages(args.from_env,
                                              args=args, **kwargs)
    flag = create_coveragerc(covered_languages)
    if not flag:
        raise Exception("Failed to create/update converagerc file.")
