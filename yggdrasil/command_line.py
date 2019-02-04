#!/usr/bin/python
import os
import sys
import copy
import logging
import traceback
from yggdrasil import runner, schema, config, timing, yamlfile
from yggdrasil.drivers import GCCModelDriver


def yggrun():
    r"""Start a run."""
    prog = sys.argv[0].split(os.path.sep)[-1]
    # Print help
    if '-h' in sys.argv:
        print('Usage: yggrun [YAMLFILE1] [YAMLFILE2]...')
        return
    models = sys.argv[1:]
    yggRunner = runner.get_runner(models, ygg_debug_prefix=prog)
    try:
        yggRunner.run()
        yggRunner.debug("runner returns, exiting")
    except Exception as ex:
        yggRunner.pprint("yggrun exception: %s" % type(ex))
        print(traceback.format_exc())
    print('')


def yggcc():
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
    print(' '.join(GCCModelDriver.get_flags()[0]))


def ld_flags():
    r"""Get the linker flags necessary for calling functions/classes from
    the interface library in a C or C++ program.

    Returns:
        list: The necessary library linking flags.

    """
    print(' '.join(GCCModelDriver.get_flags()[1]))


def rebuild_c_api():
    r"""Rebuild the C/C++ API."""
    if GCCModelDriver._c_installed:
        GCCModelDriver.build_api(cpp=False, overwrite=True)
        GCCModelDriver.build_api(cpp=True, overwrite=True)
    else:
        raise Exception("The libraries necessary for running models written in "
                        "C/C++ could not be located.")


def regen_schema():
    r"""Regenerate the yggdrasil schema."""
    if os.path.isfile(schema._schema_fname):
        os.remove(schema._schema_fname)
    schema.clear_schema()
    schema.init_schema()


def validate_yaml():
    r"""Validate a set of or or more YAMLs defining an integration."""
    files = sys.argv[1:]
    yamlfile.parse_yaml(files)
    logging.info("Validation succesful.")


def update_config():
    r"""Update the user config file for yggdrasil."""
    config.update_config(config.usr_config_file, config.def_config_file)


def yggtime_comm():
    r"""Plot timing statistics comparing the different communication mechanisms."""
    timing.plot_scalings(compare='commtype')


def yggtime_lang():
    r"""Plot timing statistics comparing the different languages."""
    timing.plot_scalings(compare='language')


def yggtime_os():
    r"""Plot timing statistics comparing the different operating systems."""
    timing.plot_scalings(compare='platform')


def yggtime_py():
    r"""Plot timing statistics comparing the different versions of Python."""
    timing.plot_scalings(compare='python')


def yggtime_paper():
    r"""Create plots for timing."""
    _lang_list = timing._lang_list
    _lang_list_nomatlab = copy.deepcopy(_lang_list)
    _lang_list_nomatlab.remove('matlab')
    timing.plot_scalings(compare='platform', python_ver='2.7')
    # All plots on Linux, no matlab
    timing.plot_scalings(compare='comm_type', platform='Linux', python_ver='2.7')
    timing.plot_scalings(compare='python_ver', platform='Linux')
    timing.plot_scalings(compare='language', platform='Linux', python_ver='2.7',
                         compare_values=_lang_list_nomatlab)
    # Language comparision on MacOS, with matlab
    timing.plot_scalings(compare='language', platform='MacOS', python_ver='2.7',
                         compare_values=_lang_list)


if __name__ == '__main__':
    yggrun()
    sys.exit(0)
