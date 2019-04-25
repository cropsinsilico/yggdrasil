"""
This module imports the configuration for yggdrasil.

.. todo::
   Remove reference to environment variables for accessing config options.

"""
import os
import sys
import shutil
import logging
import warnings
import subprocess
from yggdrasil.backwards import configparser
from yggdrasil import platform, tools
from yggdrasil.components import import_component
config_file = '.yggdrasil.cfg'
def_config_file = os.path.join(os.path.dirname(__file__), 'defaults.cfg')
usr_config_file = os.path.expanduser(os.path.join('~', config_file))
loc_config_file = os.path.join(os.getcwd(), config_file)


class YggConfigParser(configparser.ConfigParser):
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
        

def load_config_files(cfg):
    r"""Load the config files and set the module level object."""
    files = [def_config_file, usr_config_file, loc_config_file]
    cfg.read(files)
    # Aliases for old versions of config options
    alias_map = [(('debug', 'psi'), ('debug', 'ygg')),
                 (('debug', 'cis'), ('debug', 'ygg'))]
    for old, new in alias_map:
        v = cfg.get(*old)
        if v:  # pragma: debug
            cfg.set(new[0], new[1], v)


# Initialize config
ygg_cfg = YggConfigParser()
load_config_files(ygg_cfg)
    

def find_all(name, path):
    r"""Find all instances of a file with a given name within the directory
    tree starting at a given path.

    Args:
        name (str): Name of the file to be found (with the extension).
        path (str, None): Directory where search should start. If set to
            None on Windows, the current directory and PATH variable are
            searched.

    Returns:
        list: All instances of the specified file.

    """
    result = []
    try:
        if platform._is_win:  # pragma: windows
            if path is None:
                out = subprocess.check_output(["where", name],
                                              env=os.environ,
                                              stderr=subprocess.STDOUT)
            else:
                out = subprocess.check_output(["where", "/r", path, name],
                                              env=os.environ,
                                              stderr=subprocess.STDOUT)
        else:
            args = ["find", path, "-type", "f", "-name", name]
            pfind = subprocess.Popen(args, env=os.environ,
                                     stderr=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
            (stdoutdata, stderrdata) = pfind.communicate()
            out = stdoutdata
            for l in stderrdata.splitlines():
                if b'Permission denied' not in l:
                    raise subprocess.CalledProcessError(pfind.returncode,
                                                        ' '.join(args),
                                                        output=stderrdata)
    except subprocess.CalledProcessError:
        out = ''
    if not out.isspace():
        result = sorted(out.splitlines())
    result = [os.path.normcase(os.path.normpath(m.decode('utf-8'))) for m in result]
    return result


def locate_file(fname, environment_variable='PATH', directory_list=None):
    r"""Locate a file within a set of paths defined by a list or environment
    variable.

    Args:
        fname (str): Name of the file that should be located.
        environment_variable (str): Environment variable containing the set of
            paths that should be searched. Defaults to 'PATH'. If None, this
            keyword argument will be ignored. If a list is provided, it is
            assumed to be a list of environment variables that should be
            searched in the specified order.
        directory_list (list): List of paths that should be searched in addition
            to those specified by environment_variable. Defaults to None and is
            ignored. These directories will be searched be for those in the
            specified environment variables.

    Returns:
        bool, str: Full path to the located file if it was located, False
            otherwise.

    """
    out = []
    if ((platform._is_win and (environment_variable == 'PATH')
         and (directory_list is None))):  # pragma: windows
        out += find_all(fname, None)
    else:
        if directory_list is None:
            directory_list = []
        if environment_variable is not None:
            if not isinstance(environment_variable, list):
                environment_variable = [environment_variable]
            for x in environment_variable:
                directory_list += os.environ.get(x, '').split(os.pathsep)
        for path in directory_list:
            if path:
                out += find_all(fname, path)
    if not out:
        return False
    first = out[0]
    if len(out) > 1:
        warnings.warn(("More than one (%d) match to %s. "
                       + "Using first match (%s)") %
                      (len(out), fname, first), RuntimeWarning)
    return first


def update_config(config_file, config_base=None, skip_warnings=False):
    r"""Update config options for the current platform.

    Args:
        config_file (str): Full path to the config file that should be created
            and/or updated.
        config_base (str, optional): Full path to existing config file that should
            be used as a base for building the new one if it dosn't already exist.
            Defaults to 'defaults.cfg' if not provided.
        skip_warnings (bool, optional): If True, warnings about missing options
            will not be raised. Defaults to False.

    """
    if config_base is None:
        config_base = def_config_file
    assert(os.path.isfile(config_base))
    created = False
    if not os.path.isfile(config_file):
        created = True
        shutil.copy(config_base, config_file)
    try:
        cp = YggConfigParser()
        cp.read(config_file)
        miss = []
        # if platform._is_win:  # pragma: windows
        #     miss += update_config_windows(cp)
        for l in tools.get_supported_lang():
            drv = import_component('model', l)
            miss += drv.configure(cp)
        # miss += update_config_c(cp)
        # miss += update_config_matlab(cp)
        with open(config_file, 'w') as fd:
            cp.write(fd)
        if not skip_warnings:
            for sect, opt, desc in miss:  # pragma: windows
                warnings.warn(("Could not set option %s in section %s. "
                               + "Please set this in %s to: %s")
                              % (opt, sect, config_file, desc), RuntimeWarning)
    except BaseException:  # pragma: debug
        if created:
            os.remove(config_file)
            

# In order read: defaults, user, local files
if not os.path.isfile(usr_config_file):
    logging.info('Creating user config file: "%s".' % usr_config_file)
    update_config(usr_config_file)
    load_config_files(ygg_cfg)
assert(os.path.isfile(usr_config_file))
assert(os.path.isfile(def_config_file))


# Set associated environment variables
env_map = [('debug', 'ygg', 'YGG_DEBUG'),
           ('debug', 'rmq', 'RMQ_DEBUG'),
           ('debug', 'client', 'YGG_CLIENT_DEBUG'),
           ('rmq', 'namespace', 'YGG_NAMESPACE'),
           ('rmq', 'host', 'YGG_MSG_HOST'),
           ('rmq', 'vhost', 'YGG_MSG_VHOST'),
           ('rmq', 'user', 'YGG_MSG_USER'),
           ('rmq', 'password', 'YGG_MSG_PW'),
           ('parallel', 'cluster', 'YGG_CLUSTER'),
           ]


def cfg_logging(cfg=None):
    r"""Set logging levels from config options.

    Args:
        cfg (:class:`yggdrasil.config.YggConfigParser`, optional):
            Config parser with options that should be used to update the
            environment. Defaults to :data:`yggdrasil.config.ygg_cfg`.

    """
    is_model = (os.environ.get('YGG_SUBPROCESS', "False") == "True")
    if cfg is None:
        cfg = ygg_cfg
    _LOG_FORMAT = "%(levelname)s:%(module)s.%(funcName)s[%(lineno)d]:%(message)s"
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
    logLevelYGG = eval('logging.%s' % cfg.get('debug', 'ygg', 'NOTSET'))
    logLevelRMQ = eval('logging.%s' % cfg.get('debug', 'rmq', 'INFO'))
    ygg_logger = logging.getLogger("yggdrasil")
    rmq_logger = logging.getLogger("pika")
    ygg_logger.setLevel(level=logLevelYGG)
    rmq_logger.setLevel(level=logLevelRMQ)
    # For models, route the loggs to stdout so that they are displayed by the
    # model driver.
    if is_model:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logLevelYGG)
        ygg_logger.addHandler(handler)
        rmq_logger.addHandler(handler)


def cfg_environment(env=None, cfg=None):
    r"""Set environment variables based on config options.

    Args:
        env (dict, optional): Dictionary of environment variables that should
            be updated. Defaults to `os.environ`.
        cfg (:class:`yggdrasil.config.YggConfigParser`, optional):
            Config parser with options that should be used to update the
            environment. Defaults to :data:`yggdrasil.config.ygg_cfg`.

    """
    if env is None:
        env = os.environ
    if cfg is None:
        cfg = ygg_cfg
    for s, o, e in env_map:
        v = cfg.get(s, o)
        if v:
            env[e] = v

            
# Do initial update of logging & environment (legacy)
cfg_logging()
cfg_environment()
