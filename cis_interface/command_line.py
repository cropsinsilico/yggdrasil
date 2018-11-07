#!/usr/bin/python
import os
import sys
import traceback
from cis_interface import runner, schema, config, timing, yamlfile
from cis_interface.drivers import GCCModelDriver
import argparse


def cisrun():
    r"""Start a run."""
    parser = argparse.ArgumentParser(
        prog='cisrun',
        description="CLI for running model networks using cis_interface")
    parser.add_argument('yamlfile', nargs='+',
                        help="one or more yaml specification files to read "
                             + "run model and connection information from")
    parser.add_argument('--validate', action='store_true',
                        help="validate the provided specification files "
                             + "without running the integration")
    args = parser.parse_args()
    models = args.yamlfile
    if args.validate:
        try:
            yamlfile.parse_yaml(models)
            print("Provided YAML specification is valid")
        except BaseException:
            raise
    else:
        cisRunner = runner.get_runner(models)
        try:
            cisRunner.run()
            cisRunner.debug("runner returns, exiting")
        except Exception as ex:
            cisRunner.pprint("cisrun exception: %s" % type(ex))
            print(traceback.format_exc())
        print('')


def ciscc():
    r"""Compile C/C++ program."""
    # prog = sys.argv[0].split(os.path.sep)[-1]
    src = sys.argv[1:]
    out = GCCModelDriver.do_compile(src)
    print("executable: %s" % out)


def cc_flags():
    r"""Get the compiler flags necessary for including the interface
    library in a C or C++ program.

    Returns:
        list: The necessary compiler flags and preprocessor definitions.

    """
    return ' '.join(GCCModelDriver.get_flags()[0])


def ld_flags():
    r"""Get the linker flags necessary for calling functions/classes from
    the interface library in a C or C++ program.

    Returns:
        list: The necessary library linking flags.

    """
    return ' '.join(GCCModelDriver.get_flags()[1])


def regen_schema():
    r"""Regenerate the cis_interface schema."""
    if os.path.isfile(schema._schema_fname):
        os.remove(schema._schema_fname)
    schema.clear_schema()
    schema.init_schema()


def update_config():
    r"""Update the user config file for cis_interface."""
    config.update_config(config.usr_config_file, config.def_config_file)


def cistime():
    r"""Plot timing statistics."""
    parser = argparse.ArgumentParser(
        prog='cistime',
        description="Plot timing statistics for cis_interface.")
    parser.add_argument('--compare', choices=['comm_type', 'language',
                                              'platform', 'python_ver'],
                        help=("aspect that should be varied for comparison. "
                              + "If not provided, statistics for the default "
                              + "configuration on the current platform will be "
                              + "plotted."))
    args = parser.parse_args()
    if args.compare is None:
        timing.plot_scalings(compare='language', compare_values=['python'])
    else:
        timing.plot_scalings(compare=args.compare)


if __name__ == '__main__':
    cisrun()
    sys.exit(0)
