"""
This module imports the configuration for cis_interface.

"""
import os
from cis_interface.backwards import configparser

cis_cfg = configparser.ConfigParser()

# In order read: defaults, user, local files
config_file = '.cis_interface.cfg'
def_config_file = os.path.join(os.path.dirname(__file__), 'defaults.cfg')
usr_config_file = os.path.expanduser(os.path.join('~', config_file))
loc_config_file = os.path.join(os.getcwd(), config_file)
assert(os.path.isfile(def_config_file))
files = [def_config_file, usr_config_file, loc_config_file]
cis_cfg.read(files)

# Set associated environment variables
# TODO: Remove dependence on environment variables
env_map = [('debug', 'psi', 'PSI_DEBUG'),
           ('debug', 'rmq', 'RMQ_DEBUG'),
           ('debug', 'client', 'PSI_CLIENT_DEBUG'),
           ('RMQ', 'namespace', 'PSI_NAMESPACE'),
           ('RMQ', 'host', 'PSI_MSG_HOST'),
           ('RMQ', 'vhost', 'PSI_MSG_VHOST'),
           ('RMQ', 'user', 'PSI_MSG_USER'),
           ('RMQ', 'password', 'PSI_MSG_PW'),
           ('parallel', 'cluster', 'PSI_CLUSTER'),
           ]
for s, v, env in env_map:
    val = cis_cfg.get(s, v)
    if val:
        os.environ[env] = val
    # os.environ[env] = cis_cfg.get(s, v)
