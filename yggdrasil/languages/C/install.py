import os
import sys
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', '..', '..'))


def install(rj_include_dir=None):
    r"""Check that rapidjson is installed.

    Args:
        rj_include_dir (str, optional): Full path to the include directory for
            the rapidjson header-only package. Defaults to None and sys.argv
            is checked for '--rj-include-dir=' or '--rapidjson-include-dir='.

    Returns:
        bool: True if the installation is valid, False otherwise.

    """
    if rj_include_dir is None:
        rj_include_dir0 = os.path.join(ROOT_PATH, 'yggdrasil', 'rapidjson', 'include')
        for idx, arg in enumerate(sys.argv[:]):
            if ((arg.startswith('--rj-include-dir=')
                 or arg.startswith('--rapidjson-include-dir='))):
                sys.argv.pop(idx)
                rj_include_dir = os.path.abspath(arg.split('=', 1)[1])
                break
        else:
            rj_include_dir = rj_include_dir0
    if not os.path.isdir(rj_include_dir):
        raise RuntimeError("RapidJSON sources could not be located. If you "
                           "cloned the git repository, initialize the rapidjson "
                           "git submodule by calling "
                           "'git submodule update --init --recursive' "
                           "from inside the repository.")
    if rj_include_dir != rj_include_dir0:
        def_config_file = os.path.join(ROOT_PATH, 'yggdrasil', 'defaults.cfg')
        try:
            import ConfigParser as configparser
        except ImportError:
            import configparser
        cfg = configparser.ConfigParser()
        cfg.read(def_config_file)
        if not cfg.has_section('c'):
            cfg.add_section('c')
        cfg.set('c', 'rapidjson_include', rj_include_dir)
        with open(def_config_file, 'w') as fd:
            cfg.write(fd)
    return True
