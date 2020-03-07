"""
This module imports the configuration for yggdrasil.

.. todo::
   Remove reference to environment variables for accessing config options.

"""
import os
import sys
import json
import shutil
import logging
import warnings
import configparser
from collections import OrderedDict
from yggdrasil import tools
conda_prefix = os.environ.get('CONDA_PREFIX', '')
config_file = '.yggdrasil.cfg'
def_config_file = os.path.join(os.path.dirname(__file__), 'defaults.cfg')
if conda_prefix:
    usr_dir = conda_prefix
else:
    usr_dir = os.path.expanduser('~')
usr_config_file = os.path.join(usr_dir, config_file)
loc_config_file = os.path.join(os.getcwd(), config_file)
logger = logging.getLogger(__name__)


class YggConfigParser(configparser.ConfigParser, object):
    r"""Config parser that returns None if option not provided on get."""

    def __init__(self, files=None):
        self.files = files
        super(YggConfigParser, self).__init__()

    def reload(self):
        r"""Reload parameters from the original files."""
        self._sections = self._dict()
        if self.files is not None:
            self.read(self.files)

    @property
    def file_to_update(self):
        r"""str: Full path to file that should be updated if update_file is
        called without an explicit file path."""
        out = None
        if self.files is not None:
            out = self.files[-1]
        return out

    def update_file(self, fname=None):
        r"""Write out updated contents to a file.

        Args:
            fname (str, optional): Full path to file where contents should be
               saved. If None, file_to_update is used. Defaults to None.

        Raises:
            RuntimeError: If fname is None and file_to_update is None.

        """
        if fname is None:
            fname = self.file_to_update
        if fname is None:
            raise RuntimeError("No file provided or set at creation.")
        with open(fname, 'w') as fd:
            self.write(fd)

    def read(self, *args, **kwargs):
        out = super(YggConfigParser, self).read(*args, **kwargs)
        alias_map = [(('debug', 'psi'), ('debug', 'ygg')),
                     (('debug', 'cis'), ('debug', 'ygg'))]
        for old, new in alias_map:
            v = self.get(*old)
            if v:  # pragma: debug
                self.set(new[0], new[1], v)
        return out

    @classmethod
    def from_files(cls, files, **kwargs):
        r"""Construct a config parser from a set of files.

        Args:
            files (list): One or more files that options should be read from in
                the order they should be loaded.
            **kwargs: Additional keyword arguments are passed to the class
                constructor.

        Returns:
           YggConfigParser: Config parser with information loaded from the
               provided files.

        """
        out = cls(files=files, **kwargs)
        out.reload()
        return out

    def set(self, section, option, value=None):
        """Set an option."""
        if not isinstance(value, str):
            value = json.dumps(value)
        super(YggConfigParser, self).set(section, option, value=value)

    def backwards_str2val(self, val):  # pragma: no cover
        try:
            out = json.loads(val)
        except ValueError:
            if val.startswith('[') and val.endswith(']'):
                if val[1:-1]:
                    out = [self.backwards_str2val(x.strip())
                           for x in val[1:-1].split(',')]
                else:
                    out = []
            elif val.startswith("'") and val.endswith("'"):
                out = val.strip("'")
            else:
                out = val
        return out

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
                return self.backwards_str2val(out)
        else:
            return default


def get_language_order(drivers):
    r"""Get the correct language order, including any base languages.

    Args:
        drivers (dict): Drivers in order.

    Returns:
        dict: Drivers in sorted order.

    """
    from yggdrasil.components import import_component
    out = OrderedDict()
    for d, drv in drivers.items():
        if d == 'cpp':
            d = 'c++'
        new_deps = OrderedDict()
        sub_deps = OrderedDict()
        for sub_d in drv.base_languages:
            if sub_d in drivers:
                sub_deps[sub_d] = drivers[sub_d]
            else:
                sub_deps[sub_d] = import_component('model', sub_d)
        sub_deps = get_language_order(sub_deps)
        min_dep = -1
        for sub_d, sub_drv in sub_deps.items():
            if sub_d in out:
                min_dep = max(min_dep, list(out.keys()).index(sub_d))
            else:
                new_deps[sub_d] = sub_drv
        if d in out.keys():
            dpos = list(out.keys()).index(d)
            assert(dpos > min_dep)
            min_dep = dpos
        else:
            new_deps[d] = drv
        new_out = OrderedDict()
        for k in list(out.keys())[:(min_dep + 1)]:
            new_out[k] = out[k]
        new_out.update(new_deps)
        for k in list(out.keys())[(min_dep + 1):]:
            new_out[k] = out[k]
        out = new_out
    return out


def update_language_config(languages=None, skip_warnings=False,
                           disable_languages=None, enable_languages=None,
                           lang_kwargs=None, overwrite=False, verbose=False):
    r"""Update configuration options for a language driver.

    Args:
        languages (list, optional): List of languages to configure.
            Defaults to None and all supported languages will be
            configured.
        skip_warnings (bool, optional): If True, warnings about missing options
            will not be raised. Defaults to False.
        disable_languages (list, optional): List of languages that should be
            disabled. Defaults to an empty list.
        enable_languages (list, optional): List of languages that should be
            enabled. Defaults to an empty list.
        overwrite (bool, optional): If True, the existing file will be overwritten.
            Defaults to False.
        verbose (bool, optional): If True, information about the config file
            will be displayed. Defaults to False.
        lang_kwargs (dict, optional): Dictionary containing language
            specific keyword arguments. Defaults to {}.

    """
    from yggdrasil.components import import_component
    if verbose:
        logger.info("Updating user configuration file for yggdrasil at:\n\t%s"
                    % usr_config_file)
    miss = []
    if languages is None:
        all_languages = tools.get_supported_lang()
        languages = ['c', 'c++', 'make', 'cmake', 'python', 'lpy', 'r', 'matlab']
        for l in all_languages:
            if l.lower() not in languages:
                languages.append(l)
    elif not isinstance(languages, list):
        languages = [languages]
    drivers = OrderedDict([(l, import_component('model', l))
                           for l in languages])
    drv = list(get_language_order(drivers).values())
    if disable_languages is None:
        disable_languages = []
    if enable_languages is None:
        enable_languages = []
    if lang_kwargs is None:
        lang_kwargs = {}
    if overwrite:
        shutil.copy(def_config_file, usr_config_file)
        ygg_cfg_usr.reload()
    for idrv in drv:
        if (((idrv.language in disable_languages)
             and (idrv.language in enable_languages))):
            logger.info(("%s language both enabled and disabled. "
                         "No action will be taken.") % idrv.language)
        elif idrv.language in disable_languages:
            ygg_cfg_usr.set(idrv.language, 'disable', 'True')
        elif idrv.language in enable_languages:
            ygg_cfg_usr.set(idrv.language, 'disable', 'False')
        if ygg_cfg_usr.get(idrv.language, 'disable', 'False').lower() == 'true':
            continue  # pragma: no cover
        miss += idrv.configure(ygg_cfg_usr,
                               **lang_kwargs.get(idrv.language, {}))
    ygg_cfg_usr.update_file()
    ygg_cfg.reload()
    if not skip_warnings:
        for sect, opt, desc in miss:  # pragma: windows
            warnings.warn(("Could not set option %s in section %s. "
                           + "Please set this in %s to: %s")
                          % (opt, sect, ygg_cfg_usr.file_to_update, desc),
                          RuntimeWarning)
    

# Set associated environment variables
env_map = [('debug', 'ygg', 'YGG_DEBUG'),
           ('debug', 'rmq', 'RMQ_DEBUG'),
           ('debug', 'client', 'YGG_CLIENT_DEBUG'),
           ('jsonschema', 'validate_components', 'YGG_SKIP_COMPONENT_VALIDATION'),
           ('jsonschema', 'validate_all_messages', 'YGG_VALIDATE_ALL_MESSAGES'),
           ('rmq', 'namespace', 'YGG_NAMESPACE'),
           ('rmq', 'host', 'YGG_MSG_HOST'),
           ('rmq', 'vhost', 'YGG_MSG_VHOST'),
           ('rmq', 'user', 'YGG_MSG_USER'),
           ('rmq', 'password', 'YGG_MSG_PW'),
           ('parallel', 'cluster', 'YGG_CLUSTER'),
           ]


def get_ygg_loglevel(cfg=None, default='DEBUG'):
    r"""Get the current log level.

    Args:
        cfg (:class:`yggdrasil.config.YggConfigParser`, optional):
            Config parser with options that should be used to determine the
            log level. Defaults to :data:`yggdrasil.config.ygg_cfg`.
        default (str, optional): Log level that should be returned if the log
            level option is not set in cfg. Defaults to 'DEBUG'.

    Returns:
        str: Log level string.

    """
    is_model = tools.is_subprocess()
    if cfg is None:
        cfg = ygg_cfg
    if is_model:
        opt = 'client'
    else:
        opt = 'ygg'
    return cfg.get('debug', opt, default)


def set_ygg_loglevel(level, cfg=None):
    r"""Set the current log level.

    Args:
        level (str): Level that the log should be set to.
        cfg (:class:`yggdrasil.config.YggConfigParser`, optional):
            Config parser with options that should be used to update the
            environment. Defaults to :data:`yggdrasil.config.ygg_cfg`.
    
    """
    is_model = tools.is_subprocess()
    if cfg is None:
        cfg = ygg_cfg
    if is_model:
        opt = 'client'
    else:
        opt = 'ygg'
    cfg.set('debug', opt, level)
    logLevelYGG = eval('logging.%s' % level)
    ygg_logger = logging.getLogger("yggdrasil")
    ygg_logger.setLevel(level=logLevelYGG)
        
    
def cfg_logging(cfg=None):
    r"""Set logging levels from config options.

    Args:
        cfg (:class:`yggdrasil.config.YggConfigParser`, optional):
            Config parser with options that should be used to update the
            environment. Defaults to :data:`yggdrasil.config.ygg_cfg`.

    """
    is_model = tools.is_subprocess()
    if cfg is None:
        cfg = ygg_cfg
    _LOG_FORMAT = "%(levelname)s:%(module)s.%(funcName)s[%(lineno)d]:%(message)s"
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
    logLevelYGG = eval('logging.%s' % cfg.get('debug', 'ygg', 'NOTSET'))
    logLevelRMQ = eval('logging.%s' % cfg.get('debug', 'rmq', 'INFO'))
    logLevelCLI = eval('logging.%s' % cfg.get('debug', 'client', 'INFO'))
    ygg_logger = logging.getLogger("yggdrasil")
    rmq_logger = logging.getLogger("pika")
    if is_model:
        ygg_logger.setLevel(level=logLevelCLI)
    else:
        ygg_logger.setLevel(level=logLevelYGG)
    rmq_logger.setLevel(level=logLevelRMQ)
    # For models, route the loggs to stdout so that they are displayed by the
    # model driver.
    if is_model:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logLevelCLI)
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

            
# Initialize config
ygg_cfg_usr = YggConfigParser.from_files([usr_config_file])
ygg_cfg = YggConfigParser.from_files([def_config_file, usr_config_file,
                                      loc_config_file])


# Do initial update of logging & environment (legacy)
cfg_logging()
cfg_environment()
