#!/usr/bin/python
import os
import sys
import copy
import logging
import traceback


logger = logging.getLogger(__name__)


def yggrun():
    r"""Start a run."""
    from yggdrasil import runner
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
    from yggdrasil.drivers import CModelDriver
    # prog = sys.argv[0].split(os.path.sep)[-1]
    src = sys.argv[1:]
    out = CModelDriver.CModelDriver.call_compile(src)
    print("executable: %s" % out)


def cc_flags():
    r"""Get the compiler flags necessary for including the interface
    library in a C or C++ program.

    Returns:
        list: The necessary compiler flags and preprocessor definitions.

    """
    from yggdrasil.drivers import CModelDriver
    print(' '.join(CModelDriver.CModelDriver.get_compiler_flags()))


def ld_flags():
    r"""Get the linker flags necessary for calling functions/classes from
    the interface library in a C or C++ program.

    Returns:
        list: The necessary library linking flags.

    """
    from yggdrasil.drivers import CModelDriver
    print(' '.join(CModelDriver.CModelDriver.get_linker_flags()))


def rebuild_c_api():
    r"""Rebuild the C/C++ API."""
    from yggdrasil.drivers import CModelDriver, CPPModelDriver
    if CModelDriver.CModelDriver.is_installed():
        CModelDriver.CModelDriver.compile_dependencies(overwrite=True)
        # TODO: Check that this compiles library correctly
        CPPModelDriver.CPPModelDriver.compile_dependencies(overwrite=True)
    else:
        raise Exception("The libraries necessary for running models written in "
                        "C/C++ could not be located.")

    
def regen_metaschema():
    r"""Regenerate the yggdrasil metaschema."""
    from yggdrasil import metaschema
    if os.path.isfile(metaschema._metaschema_fname):
        os.remove(metaschema._metaschema_fname)
    metaschema._metaschema = None
    metaschema._validator = None
    metaschema.get_metaschema()
    

def regen_schema():
    r"""Regenerate the yggdrasil schema."""
    from yggdrasil import schema
    if os.path.isfile(schema._schema_fname):
        os.remove(schema._schema_fname)
    schema.clear_schema()
    schema.init_schema()


def validate_yaml():
    r"""Validate a set of or or more YAMLs defining an integration."""
    from yggdrasil import yamlfile
    files = sys.argv[1:]
    yamlfile.parse_yaml(files)
    logger.info("Validation succesful.")


def update_config():
    r"""Update the user config file for yggdrasil."""
    from yggdrasil import config, tools
    from yggdrasil.components import import_component
    overwrite = ('--overwrite' in sys.argv)
    drv = [import_component('model', l) for l in tools.get_supported_lang()]
    config.update_language_config(drv, overwrite=overwrite,
                                  verbose=True)


def yggtime_comm():
    r"""Plot timing statistics comparing the different communication mechanisms."""
    from yggdrasil import timing
    timing.plot_scalings(compare='commtype')


def yggtime_lang():
    r"""Plot timing statistics comparing the different languages."""
    from yggdrasil import timing
    timing.plot_scalings(compare='language')


def yggtime_os():
    r"""Plot timing statistics comparing the different operating systems."""
    from yggdrasil import timing
    timing.plot_scalings(compare='platform')


def yggtime_py():
    r"""Plot timing statistics comparing the different versions of Python."""
    from yggdrasil import timing
    timing.plot_scalings(compare='python')


def yggtime_paper():
    r"""Create plots for timing."""
    from yggdrasil import timing
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
