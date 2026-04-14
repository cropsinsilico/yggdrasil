import os
import argparse
ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', '..', '..'))


def update_argparser(parser=None):
    r"""Update argument parser with language specific arguments.

    Args:
        parser (argparse.ArgumentParser, optional): Existing argument parser
            that should be updated. Default to None and a new argument parser
            will be created.

    Returns:
        argparse.ArgumentParser: Argument parser with language specific arguments.

    """
    if parser is None:
        parser = argparse.ArgumentParser("Run C installation script.")
    parser.add_argument('--rj-include-dir', '--rapidjson-include-dir',
                        nargs=1,
                        help='YggdrasilRapidJSON include directory.')
    return parser


def install(args=None, rj_include_dir=None):
    r"""Check that rapidjson is installed.

    Args:
        args (argparse.Namespace, optional): Arguments parsed from the
            command line. Default to None and is created from sys.argv.
        rj_include_dir (str, optional): Full path to the include directory for
            the rapidjson header-only package. Defaults to None and args
            is checked for '--rj-include-dir' or '--rapidjson-include-dir'.

    Returns:
        bool: True if the installation is valid, False otherwise.

    """
    if args is None:
        args = update_argparser().parse_args()
    if rj_include_dir is None:
        rj_include_dir = args.rj_include_dir
    if rj_include_dir is not None:
        if not os.path.isdir(rj_include_dir):
            raise RuntimeError(
                "YggdrasilRapidJSON sources do not exist at specified "
                "location \"{rj_include_dir}\"")
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


if __name__ == "__main__":
    out = install()
    if out:
        print("rapidjson installed.")
    else:
        raise Exception("Failed to located rapidjson.")
