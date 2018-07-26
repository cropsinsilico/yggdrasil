"""
This module imports the configuration for cis_interface.

.. todo::
   Remove reference to environment variables for accessing config options.

"""
import os
import shutil
import warnings
import logging
# import pprint
import subprocess
from cis_interface.backwards import configparser
from cis_interface import platform, backwards
config_file = '.cis_interface.cfg'
def_config_file = os.path.join(os.path.dirname(__file__), 'defaults.cfg')
usr_config_file = os.path.expanduser(os.path.join('~', config_file))
loc_config_file = os.path.join(os.getcwd(), config_file)


class CisConfigParser(configparser.ConfigParser):
    r"""Config parser that returns None if option not provided on get."""

    def get(self, section, option, default=None, **kwargs):
        r"""Return None if the section/option does not exist.

        Args:
            section (str): Name of section.
            option (str): Name of option in section.
            default (obj, optional): Value that should be returned if the
                section and/or option are not found or are an empty string.
                Defaults to None.
            **kwargs: Additional keyword arguments are passed to the parent
                class's get.

        Returns:
            obj: String entry if the section & option exist, otherwise default.

        """
        section = section.lower()
        option = option.lower()
        if self.has_section(section) and self.has_option(section, option):
            # Super does not work for ConfigParser as not inherited from object
            out = configparser.ConfigParser.get(self, section, option, **kwargs)
            # Count empty strings as not provided
            if not out:
                return default
            else:
                return out
        else:
            return default


def find_all(name, path):
    r"""Find all instances of a file with a given name within the directory
    tree starting at a given path.

    Args:
        name (str): Name of the file to be found (with the extension).
        path (str): Directory where search should start.

    Returns:
        list: All instances of the specified file.

    """
    result = []
    try:
        if platform._is_win:  # pragma: windows
            out = subprocess.check_output(["where", "/r", path, name],
                                          stderr=subprocess.STDOUT)
        else:
            try:
                out = subprocess.check_output(["find", path, "-type", "f",
                                               "-name", name],
                                              stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                if backwards.unicode2bytes('Permission denied') in e.output:
                    out = ''
                else:
                    raise e
    except subprocess.CalledProcessError:
        out = ''
    if not out.isspace():
        result = out.splitlines()
    result = [m.decode('utf-8') for m in result]
    return result


def locate_file(fname):
    r"""Locate a file on PATH.

    Args:
        fname (str): Name of the file that should be located.

    Returns:
        bool, str: Full path to the located file if it was located, False
            otherwise.

    """
    out = []
    for path in os.environ.get('PATH').split(os.pathsep):
        if path:
            # print('searching %s for %s' % (path, fname))
            out += find_all(fname, path)
    if not out:
        return False
    first = out[0]
    if len(out) > 1:
        # pprint.pprint(out)
        warnings.warn("More than one (%d) match to %s. Using first match (%s)" % (
            len(out), fname, first))
    return first


def update_config_windows(config):  # pragma: windows
    r"""Update config options specific to windows.

    Args:
        config (CisConfigParser): Config class that options should be set for.

    Returns:
        list: Section, option, description tuples for options that could not be
            set.

    """
    out = []
    if not config.has_section('windows'):
        config.add_section('windows')
    # Find paths
    clibs = [('libzmq_include', 'zmq.h', 'The full path to the zmq.h header file.'),
             ('libzmq_static', 'zmq.lib', 'The full path to the zmq.lib static library.'),
             ('czmq_include', 'czmq.h', 'The full path to the czmq.h header file.'),
             ('czmq_static', 'czmq.lib', 'The full path to the czmq.lib static library.')]
    for opt, fname, desc in clibs:
        if not config.has_option('windows', opt):
            fpath = locate_file(fname)
            if fpath:
                print('located %s: %s' % (fname, fpath))
                config.set('windows', opt, fpath)
            else:
                out.append(('windows', opt, desc))
    return out


def update_config(config_file, config_base=None):
    r"""Update config options for the current platform.

    Args:
        config_file (str): Full path to the config file that should be created
            and/or updated.
        config_base (str, optional): Full path to existing config file that should
            be used as a base for building the new one if it dosn't already exist.
            Defaults to 'defaults.cfg' if not provided.

    """
    if config_base is None:
        config_base = def_config_file
    assert(os.path.isfile(config_base))
    if not os.path.isfile(config_file):
        shutil.copy(config_base, config_file)
    cp = CisConfigParser()
    cp.read(config_file)
    miss = []
    if platform._is_win:  # pragma: windows
        miss += update_config_windows(cp)
    with open(config_file, 'w') as fd:
        cp.write(fd)
    for sect, opt, desc in miss:
        warnings.warn(("Could not locate option %s in section %s." +
                       "Please set this in %s to: %s")
                      % (opt, sect, config_file, desc))

        
# In order read: defaults, user, local files
if not os.path.isfile(usr_config_file):
    print('Creating user config file: "%s".' % usr_config_file)
    update_config(usr_config_file)
assert(os.path.isfile(usr_config_file))
assert(os.path.isfile(def_config_file))
files = [def_config_file, usr_config_file, loc_config_file]
cis_cfg = CisConfigParser()
cis_cfg.read(files)


# Aliases for old versions of config options
alias_map = [(('debug', 'psi'), ('debug', 'cis'))]
for old, new in alias_map:
    v = cis_cfg.get(*old)
    if v:  # pragma: debug
        cis_cfg.set(new[0], new[1], v)


# Set associated environment variables
env_map = [('debug', 'cis', 'CIS_DEBUG'),
           ('debug', 'rmq', 'RMQ_DEBUG'),
           ('debug', 'client', 'CIS_CLIENT_DEBUG'),
           ('rmq', 'namespace', 'CIS_NAMESPACE'),
           ('rmq', 'host', 'CIS_MSG_HOST'),
           ('rmq', 'vhost', 'CIS_MSG_VHOST'),
           ('rmq', 'user', 'CIS_MSG_USER'),
           ('rmq', 'password', 'CIS_MSG_PW'),
           ('parallel', 'cluster', 'CIS_CLUSTER'),
           ]


def cfg_logging(cfg=None):
    r"""Set logging levels from config options.

    Args:
        cfg (:class:`cis_interface.config.CisConfigParser`, optional):
            Config parser with options that should be used to update the
            environment. Defaults to :data:`cis_interface.config.cis_cfg`.

    """
    if cfg is None:
        cfg = cis_cfg
    _LOG_FORMAT = "%(levelname)s:%(module)s.%(funcName)s[%(lineno)d]:%(message)s"
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
    logLevelCIS = eval('logging.%s' % cfg.get('debug', 'cis', 'NOTSET'))
    logLevelRMQ = eval('logging.%s' % cfg.get('debug', 'rmq', 'INFO'))
    logging.getLogger("cis_interface").setLevel(level=logLevelCIS)
    logging.getLogger("pika").setLevel(level=logLevelRMQ)
        

def cfg_environment(env=None, cfg=None):
    r"""Set environment variables based on config options.

    Args:
        env (dict, optional): Dictionary of environment variables that should
            be updated. Defaults to `os.environ`.
        cfg (:class:`cis_interface.config.CisConfigParser`, optional):
            Config parser with options that should be used to update the
            environment. Defaults to :data:`cis_interface.config.cis_cfg`.

    """
    if env is None:
        env = os.environ
    if cfg is None:
        cfg = cis_cfg
    for s, o, e in env_map:
        v = cfg.get(s, o)
        if v:
            env[e] = v

            
# Do initial update of logging & environment (legacy)
cfg_logging()
cfg_environment()
