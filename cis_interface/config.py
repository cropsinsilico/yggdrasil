"""
This module imports the configuration for cis_interface.

.. todo::
   Remove reference to environment variables for accessing config options.

"""
import os
from cis_interface.backwards import configparser


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
        
        
# In order read: defaults, user, local files
cis_cfg = CisConfigParser()
config_file = '.cis_interface.cfg'
def_config_file = os.path.join(os.path.dirname(__file__), 'defaults.cfg')
usr_config_file = os.path.expanduser(os.path.join('~', config_file))
loc_config_file = os.path.join(os.getcwd(), config_file)
assert(os.path.isfile(def_config_file))
files = [def_config_file, usr_config_file, loc_config_file]
cis_cfg.read(files)

# Set associated environment variables
env_map = [('debug', 'psi', 'PSI_DEBUG'),
           ('debug', 'rmq', 'RMQ_DEBUG'),
           ('debug', 'client', 'PSI_CLIENT_DEBUG'),
           ('rmq', 'namespace', 'PSI_NAMESPACE'),
           ('rmq', 'host', 'PSI_MSG_HOST'),
           ('rmq', 'vhost', 'PSI_MSG_VHOST'),
           ('rmq', 'user', 'PSI_MSG_USER'),
           ('rmq', 'password', 'PSI_MSG_PW'),
           ('parallel', 'cluster', 'PSI_CLUSTER'),
           ]


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
        v = cis_cfg.get(s, o)
        if v:
            env[e] = v

            
# Do initial update of environment (legacy)
cfg_environment()
