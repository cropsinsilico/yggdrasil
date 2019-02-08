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
from yggdrasil import platform, backwards
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


def locate_file(fname):
    r"""Locate a file on PATH.

    Args:
        fname (str): Name of the file that should be located.

    Returns:
        bool, str: Full path to the located file if it was located, False
            otherwise.

    """
    out = []
    if platform._is_win:  # pragma: windows
        out += find_all(fname, None)
    else:
        for path in os.environ.get('PATH').split(os.pathsep):
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


def update_config_matlab(config):
    r"""Update config options specific to matlab.

    Args:
        config (YggConfigParser): Config class that options should be set for.

    Returns:
        list: Section, option, description tuples for options that could not be
            set.

    """
    out = []
    # This should be uncommented if the matlab section is removed from the
    # default config file
    if not config.has_section('matlab'):  # pragma: debug
        config.add_section('matlab')
    opts = {
        'startup_waittime_s': [('The time allowed for a Matlab engine to start'
                               + 'before timing out and reporting an error.'),
                               '10'],
        'release': ['The version (release number) of matlab that is installed.',
                    ''],
        'matlabroot': ['The path to the default installation of matlab.', '']}
    if config.get('matlab', 'disable', 'False').lower() != 'true':
        mtl_id = '=MATLABROOT='
        cmd = ("fprintf('" + mtl_id + "%s" + mtl_id + "R%s" + mtl_id + "'"
               + ",matlabroot,version('-release')); exit();")
        mtl_cmd = ['matlab', '-nodisplay', '-nosplash', '-nodesktop', '-nojvm',
                   '-r', '%s' % cmd]
        try:  # pragma: matlab
            mtl_proc = subprocess.check_output(mtl_cmd)
            mtl_id = backwards.match_stype(mtl_proc, mtl_id)
            if mtl_id not in mtl_proc:  # pragma: debug
                raise RuntimeError(("Could not locate matlab root id (%s) in "
                                    "output (%s).") % (mtl_id, mtl_proc))
            opts['matlabroot'][1] = backwards.as_str(mtl_proc.split(mtl_id)[-3])
            opts['release'][1] = backwards.as_str(mtl_proc.split(mtl_id)[-2])
        except (subprocess.CalledProcessError, OSError):  # pragma: no matlab
            pass
    for k in opts.keys():
        if not config.has_option('matlab', k):
            if opts[k][1]:  # pragma: matlab
                config.set('matlab', k, opts[k][1])
            else:
                out.append(('matlab', k, opts[k][0]))
    return out


def update_config_windows(config):  # pragma: windows
    r"""Update config options specific to windows.

    Args:
        config (YggConfigParser): Config class that options should be set for.

    Returns:
        list: Section, option, description tuples for options that could not be
            set.

    """
    out = []
    if not config.has_section('windows'):
        config.add_section('windows')
    # Find paths
    clibs = [('libzmq_include', 'zmq.h',
              'The full path to the zmq.h header file.'),
             ('libzmq_static', 'zmq.lib',
              'The full path to the zmq.lib static library.'),
             ('czmq_include', 'czmq.h',
              'The full path to the czmq.h header file.'),
             ('czmq_static', 'czmq.lib',
              'The full path to the czmq.lib static library.')]
    for opt, fname, desc in clibs:
        if not config.has_option('windows', opt):
            fpath = locate_file(fname)
            if fpath:
                logging.info('Located %s: %s' % (fname, fpath))
                config.set('windows', opt, fpath)
            else:
                out.append(('windows', opt, desc))
    return out


def update_config_c(config):
    r"""Update config options specific to C/C++.

    Args:
        config (CisConfigParser): Config class that options should be set for.

    Returns:
        list: Section, option, description tuples for options that could not be
            set.

    """
    out = []
    if not config.has_section('c'):
        config.add_section('c')
    # Find paths
    clibs = [('rapidjson_include', 'rapidjson.h',
              'The full path to the directory containing rapidjson headers.')]
    for opt, fname, desc in clibs:
        if not config.has_option('c', opt):
            fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rapidjson',
                                 'include', 'rapidjson', fname)
            if not os.path.isfile(fpath):  # pragma: debug
                fpath = locate_file(fname)
            if fpath:
                if opt == 'rapidjson_include':
                    fpath = os.path.dirname(os.path.dirname(fpath))
                logging.info('Located %s: %s' % (fname, fpath))
                config.set('c', opt, fpath)
            else:  # pragma: debug
                out.append(('c', opt, desc))
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
    cp = YggConfigParser()
    cp.read(config_file)
    miss = []
    if platform._is_win:  # pragma: windows
        miss += update_config_windows(cp)
    miss += update_config_c(cp)
    miss += update_config_matlab(cp)
    with open(config_file, 'w') as fd:
        cp.write(fd)
    for sect, opt, desc in miss:  # pragma: windows
        warnings.warn(("Could not set option %s in section %s. "
                       + "Please set this in %s to: %s")
                      % (opt, sect, config_file, desc), RuntimeWarning)
        

# In order read: defaults, user, local files
if not os.path.isfile(usr_config_file):
    logging.info('Creating user config file: "%s".' % usr_config_file)
    update_config(usr_config_file)
assert(os.path.isfile(usr_config_file))
assert(os.path.isfile(def_config_file))
files = [def_config_file, usr_config_file, loc_config_file]
ygg_cfg = YggConfigParser()
ygg_cfg.read(files)


# Aliases for old versions of config options
alias_map = [(('debug', 'psi'), ('debug', 'ygg')),
             (('debug', 'cis'), ('debug', 'ygg'))]
for old, new in alias_map:
    v = ygg_cfg.get(*old)
    if v:  # pragma: debug
        ygg_cfg.set(new[0], new[1], v)


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
