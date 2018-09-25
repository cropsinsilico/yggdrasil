#!/usr/bin/python
import os
import sys
import traceback
from cis_interface import runner, schema, config
from cis_interface.drivers import GCCModelDriver


def cisrun():
    r"""Start a run."""
    prog = sys.argv[0].split(os.path.sep)[-1]
    # Print help
    if '-h' in sys.argv:
        print('Usage: cisrun [YAMLFILE1] [YAMLFILE2]...')
        return
    models = sys.argv[1:]
    cisRunner = runner.get_runner(models, cis_debug_prefix=prog)
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


if __name__ == '__main__':
    cisrun()
    sys.exit(0)
