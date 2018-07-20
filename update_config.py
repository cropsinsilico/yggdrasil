import os
import sys
import pprint
import subprocess
import warnings
IS_WINDOWS = (sys.platform in ['win32', 'cygwin'])
# Import config parser
try:
    from ConfigParser import RawConfigParser as HandyConfigParser
except ImportError:
    try:
        from configparser import RawConfigParser as HandyConfigParser
    except ImportError:
        HandyConfigParser = None
usr_config_file = os.path.expanduser(os.path.join('~', '.cis_interface.cfg'))


def locate(fname, brute_force=False):
    r"""Locate a file.

    Args:
        fname (str): Name of the file that should be located.
        brute_force (bool, optional): If True, the entire file system will be
            searched for the file in question. Otherwise, the path will be
            searched first, then the entire system will be searched. Defaults
            to False.

    Returns:
        bool, str: Full path to the located file if it was located, False
            otherwise.

    """
    try:
        if brute_force:
            if os.environ.get('APPVEYOR_BUILD_FOLDER', False):
                warnings.warn("Brute force search disabled on appveyor.")
                return False
            warnings.warn("Running brute force search for %s" % fname)
            out = subprocess.check_output(["dir", fname, "/s/b"], shell=True,
                                          cwd=os.path.abspath(os.sep))
        else:
            out = subprocess.check_output(["where", fname])
    except subprocess.CalledProcessError:
        if not brute_force:
            return locate(fname, brute_force=True)
        return False
    if out.isspace():
        return False
    matches = out.splitlines()
    first = matches[0].decode('utf-8')
    if len(matches) > 1:
        pprint.pprint(matches)
        warnings.warn("More than one (%d) match to %s. Using first match (%s)" % (
            len(matches), fname, first))
    return first


def update_zmq(config, fname_config=None):
    r"""Update a cis_interface config file to reflect the locations of the
    relevant zmq and czmq headers and libraries.

    Args:
        config (ConfigParser): Config to update.

    Returns:
        bool: True if the config file was updated successfully, False otherwise.

    """
    if fname_config is None:
        fname_config = usr_config_file
    out = True
    if not IS_WINDOWS:
        return out
    config.read(fname_config)
    if not config.has_section('windows'):
        config.add_section('windows')
    # Find paths
    clibs = {'libzmq_include': 'zmq.h',
             'libzmq_static': 'zmq.lib',
             'czmq_include': 'czmq.h',
             'czmq_static': 'czmq.lib'}
    for opt, fname in clibs.items():
        if not config.has_option('windows', opt):
            fpath = locate(fname)
            if fpath:
                print('located %s: %s' % (fname, fpath))
                config.set('windows', opt, fpath)
            else:
                warnings.warn("Could not locate %s. " % fname +
                              "Please set %s option in %s to correct path."
                              % (opt, fname_config))
                out = False
    return out


def update_config(fname):
    r"""Update a cis_interface config file to reflect the current status of the
    machine.

    Args:
        fname (str): Full path to the config file that should be updated.

    Returns:
        bool: True if the config file was updated successfully, False otherwise.

    """
    if HandyConfigParser is None:
        warnings.warn("No config parser available.")
        return False
    if not IS_WINDOWS:
        return True
    cp = HandyConfigParser("")
    cp.read(fname)
    out = update_zmq(cp, fname_config=fname)
    with open(fname, 'w') as fd:
        cp.write(fd)
    return out


if __name__ == "__main__":
    flag = update_config(usr_config_file)
    if not flag:
        raise Exception("Failed to update config file.")
