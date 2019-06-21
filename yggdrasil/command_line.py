#!/usr/bin/python
import os
import sys
import copy
import logging
import traceback
import subprocess


logger = logging.getLogger(__name__)


def ygginfo():
    r"""Print information about yggdrasil installation."""
    from yggdrasil import __version__, tools, config, backwards
    from yggdrasil.components import import_component
    lang_list = tools.get_installed_lang()
    prefix = '    '
    curr_prefix = ''
    vardict = [
        ('Location', os.path.dirname(__file__)),
        ('Version', __version__),
        ('Languages', ', '.join(lang_list)),
        ('Communication Mechanisms', ', '.join(tools.get_installed_comm())),
        ('Default Comm Mechanism', tools.get_default_comm()),
        ('Config File', config.usr_config_file)]
    # Add language information
    if '--no-languages' not in sys.argv:
        # Install languages
        vardict.append(('Installed Languages:', ''))
        curr_prefix += prefix
        for lang in sorted(lang_list):
            drv = import_component('model', lang)
            vardict.append((curr_prefix + '%s:' % lang.upper(), ''))
            curr_prefix += prefix
            if lang == 'executable':
                vardict.append((curr_prefix + 'Location', ''))
            else:
                exec_name = drv.language_executable()
                if not os.path.isabs(exec_name):
                    exec_name = tools.which(exec_name)
                vardict.append((curr_prefix + 'Location', exec_name))
            vardict.append((curr_prefix + 'Version', drv.language_version()))
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
        curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
        # Not installed languages
        vardict.append(("Languages Not Installed:", ''))
        curr_prefix += prefix
        for lang in tools.get_supported_lang():
            if lang in lang_list:
                continue
            drv = import_component('model', lang)
            vardict.append((curr_prefix + '%s:' % lang.upper(), ''))
            curr_prefix += prefix
            vardict.append((curr_prefix + "Language Installed",
                            drv.is_language_installed()))
            vardict.append((curr_prefix + "Dependencies Installed",
                            drv.are_dependencies_installed()))
            vardict.append((curr_prefix + "Interface Installed",
                            drv.is_interface_installed()))
            vardict.append((curr_prefix + "Comm Installed",
                            drv.is_comm_installed()))
            vardict.append((curr_prefix + "Configured", drv.is_configured()))
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
        curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
    # Add verbose information
    if '--verbose' in sys.argv:
        # Conda info
        if os.environ.get('CONDA_PREFIX', ''):
            out = backwards.as_str(subprocess.check_output(['conda', 'info'])).strip()
            curr_prefix += prefix
            vardict.append((curr_prefix + 'Conda Info:', "\n%s%s"
                            % (curr_prefix + prefix,
                               ("\n" + curr_prefix + prefix).join(
                                   out.splitlines(False)))))
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
        # R and reticulate info
        Rdrv = import_component("model", "R")
        if Rdrv.is_installed():
            out = Rdrv.run_executable(["-e", "sessionInfo()"]).strip()
            vardict.append((curr_prefix + "R sessionInfo:", "\n%s%s"
                            % (curr_prefix + prefix,
                               ("\n" + curr_prefix + prefix).join(
                                   out.splitlines(False)))))
            out = Rdrv.run_executable(["-e", "reticulate::py_config()"]).strip()
            vardict.append((curr_prefix + "R reticulate::py_config():", "\n%s%s"
                            % (curr_prefix + prefix,
                               ("\n" + curr_prefix + prefix).join(
                                   out.splitlines(False)))))
    # Print things
    max_len = max(len(x[0]) for x in vardict)
    lines = []
    line_format = '%-' + str(max_len) + 's' + prefix + '%s'
    for k, v in vardict:
        lines.append(line_format % (k, v))
    logger.info("yggdrasil info:\n%s" % '\n'.join(lines))


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


def ygginstall():
    r"""Call installation script."""
    from yggdrasil.languages import install_languages
    languages = []
    for x in sys.argv[1:]:
        if not x.startswith('-'):
            languages.append(x)
    if len(languages) == 0:
        install_languages.install_all_languages()
    else:
        for x in languages:
            install_languages.install_language(x)


if __name__ == '__main__':
    yggrun()
    sys.exit(0)
