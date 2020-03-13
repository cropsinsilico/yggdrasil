#!/usr/bin/python
import os
import sys
import copy
import logging
import subprocess
import argparse
import pprint


logger = logging.getLogger(__name__)


def ygginfo():
    r"""Print information about yggdrasil installation."""
    from yggdrasil import __version__, tools, config, platform
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
    parser = argparse.ArgumentParser(
        description='Display information about the current yggdrasil installation.')
    parser.add_argument('--no-languages', action='store_true',
                        dest='no_languages',
                        help='Don\'t print information about individual languages.')
    parser.add_argument('--verbose', action='store_true',
                        help='Increase the verbosity of the printed information.')
    args = parser.parse_args()
    try:
        # Add language information
        if not args.no_languages:
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
                vardict.append((curr_prefix + 'Version',
                                drv.language_version()))
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
                vardict.append((curr_prefix + "Base Languages Installed",
                                drv.are_base_languages_installed()))
                if not drv.are_base_languages_installed():
                    vardict.append(
                        (curr_prefix + "Base Languages Not Installed",
                         [b for b in drv.base_languages if
                          (not import_component('model', b).is_installed())]))
                vardict.append((curr_prefix + "Dependencies Installed",
                                drv.are_dependencies_installed()))
                vardict.append((curr_prefix + "Interface Installed",
                                drv.is_interface_installed()))
                vardict.append((curr_prefix + "Comm Installed",
                                drv.is_comm_installed()))
                vardict.append((curr_prefix + "Configured",
                                drv.is_configured()))
                vardict.append((curr_prefix + "Disabled",
                                drv.is_disabled()))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
        # Add verbose information
        if args.verbose:
            # Conda info
            if os.environ.get('CONDA_PREFIX', ''):
                out = tools.bytes2str(subprocess.check_output(
                    ['conda', 'info'])).strip()
                curr_prefix += prefix
                vardict.append((curr_prefix + 'Conda Info:', "\n%s%s"
                                % (curr_prefix + prefix,
                                   ("\n" + curr_prefix + prefix).join(
                                       out.splitlines(False)))))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            # R and reticulate info
            Rdrv = import_component("model", "R")
            if Rdrv.is_installed():
                env_reticulate = copy.deepcopy(os.environ)
                env_reticulate['RETICULATE_PYTHON'] = sys.executable
                # Stack size
                out = Rdrv.run_executable(["-e", "Cstack_info()"]).strip()
                vardict.append((curr_prefix + "R Cstack_info:", "\n%s%s"
                                % (curr_prefix + prefix,
                                   ("\n" + curr_prefix + prefix).join(
                                       out.splitlines(False)))))
                # Compilation tools
                interp = 'R'.join(Rdrv.get_interpreter().rsplit('Rscript', 1))
                vardict.append((curr_prefix + "R C Compiler:", ""))
                curr_prefix += prefix
                for x in ['CC', 'CFLAGS', 'CXX', 'CXXFLAGS']:
                    out = tools.bytes2str(subprocess.check_output(
                        [interp, 'CMD', 'config', x])).strip()
                    vardict.append((curr_prefix + x, "%s"
                                    % ("\n" + curr_prefix + prefix).join(
                                        out.splitlines(False))))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                # Session info
                out = Rdrv.run_executable(["-e", "sessionInfo()"]).strip()
                vardict.append((curr_prefix + "R sessionInfo:", "\n%s%s"
                                % (curr_prefix + prefix,
                                   ("\n" + curr_prefix + prefix).join(
                                       out.splitlines(False)))))
                # Reticulate conda_list
                if os.environ.get('CONDA_PREFIX', ''):
                    out = Rdrv.run_executable(
                        ["-e", ("library(reticulate); "
                                "reticulate::conda_list()")],
                        env=env_reticulate).strip()
                    vardict.append((curr_prefix + "R reticulate::conda_list():",
                                    "\n%s%s" % (curr_prefix + prefix,
                                                ("\n" + curr_prefix + prefix).join(
                                                    out.splitlines(False)))))
                # Windows python versions
                if platform._is_win:  # pragma: windows
                    out = Rdrv.run_executable(
                        ["-e", ("library(reticulate); "
                                "reticulate::py_versions_windows()")],
                        env=env_reticulate).strip()
                    vardict.append((curr_prefix
                                    + "R reticulate::py_versions_windows():",
                                    "\n%s%s" % (curr_prefix + prefix,
                                                ("\n" + curr_prefix + prefix).join(
                                                    out.splitlines(False)))))
                # conda_binary
                if platform._is_win:  # pragma: windows
                    out = Rdrv.run_executable(
                        ["-e", ("library(reticulate); "
                                "conda <- reticulate:::conda_binary(\"auto\"); "
                                "system(paste(conda, \"info --json\"))")],
                        env=env_reticulate).strip()
                    vardict.append((curr_prefix
                                    + "R reticulate::py_versions_windows():",
                                    "\n%s%s" % (curr_prefix + prefix,
                                                ("\n" + curr_prefix + prefix).join(
                                                    out.splitlines(False)))))
                # Reticulate py_config
                out = Rdrv.run_executable(["-e", ("library(reticulate); "
                                                  "reticulate::py_config()")],
                                          env=env_reticulate).strip()
                vardict.append((curr_prefix + "R reticulate::py_config():",
                                "\n%s%s" % (curr_prefix + prefix,
                                            ("\n" + curr_prefix + prefix).join(
                                                out.splitlines(False)))))
    finally:
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
    parser = argparse.ArgumentParser(description='Run an integration.')
    parser.add_argument('yamlfile', nargs='+',
                        help='One or more yaml specification files.')
    args = parser.parse_args()
    prog = sys.argv[0].split(os.path.sep)[-1]
    runner.run(args.yamlfile, ygg_debug_prefix=prog)


def yggclean():
    r"""Cleanup dependency files."""
    from yggdrasil.tools import get_supported_lang
    from yggdrasil.components import import_component
    parser = argparse.ArgumentParser(
        description='Remove dependency libraries compiled by yggdrasil.')
    parser.add_argument('language', nargs='*', default=[],
                        help=('One or more languages to clean up '
                              'dependencies for.'))
    args = parser.parse_args()
    if (len(args.language) == 0) or ('all' in args.language):
        args.language = get_supported_lang()
    for l in args.language:
        import_component('model', l).cleanup_dependencies()


def yggcc():
    r"""Compile C/C++ program."""
    from yggdrasil.drivers import CModelDriver
    parser = argparse.ArgumentParser(description='Compile a C/C++ program.')
    parser.add_argument('source', nargs='+',
                        help='One or more source files.')
    args = parser.parse_args()
    out = CModelDriver.CModelDriver.call_compile(args.source)
    print("executable: %s" % out)


def cc_flags():
    r"""Get the compiler flags necessary for including the interface
    library in a C or C++ program.

    Returns:
        list: The necessary compiler flags and preprocessor definitions.

    """
    from yggdrasil.drivers import CModelDriver
    print(' '.join(CModelDriver.CModelDriver.get_compiler_flags(for_model=True)))


def ld_flags():
    r"""Get the linker flags necessary for calling functions/classes from
    the interface library in a C or C++ program.

    Returns:
        list: The necessary library linking flags.

    """
    from yggdrasil.drivers import CModelDriver
    print(' '.join(CModelDriver.CModelDriver.get_linker_flags(for_model=True)))


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
    parser = argparse.ArgumentParser(
        description='Validate a set of YAML specification files for an integration.')
    parser.add_argument('yamlfile', nargs='+',
                        help='One or more YAML specification files.')
    args = parser.parse_args()
    yamlfile.parse_yaml(args.yamlfile)
    logger.info("Validation succesful.")


def update_config():
    r"""Update the user config file for yggdrasil."""
    from yggdrasil import config, tools, platform
    parser = argparse.ArgumentParser(
        description='Update the user config file.')
    parser.add_argument('--show-file', action='store_true',
                        help='Print the path to the config file without updating it.')
    parser.add_argument('--remove-file', action='store_true',
                        help='Remove the existing config file and return.')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite the existing file.')
    parser.add_argument('--languages', nargs='+',
                        default=tools.get_supported_lang(),
                        help=('One or more languages that should be'
                              'configured.'))
    parser.add_argument('--disable-languages', nargs='+',
                        default=[], dest='disable_languages',
                        help='One or more languages that should be disabled.')
    parser.add_argument('--enable-languages', nargs='+', default=[],
                        help='One or more languages that should be enabled.')
    if ('-h' in sys.argv) or ('--help' in sys.argv):
        prelang = tools.get_supported_lang()
    else:
        prelang = parser.parse_known_args()[0].languages
    lang_args = {}
    lang_args2kwargs = {}
    if platform._is_mac:
        lang_args.setdefault('c', [])
        lang_args['c'].append(
            (('--macos-sdkroot', '--sdkroot'),
             {'help': (
                 'The full path to the MacOS SDK '
                 'that should be used.')}))
    for l in prelang:
        if l in lang_args:
            lang_args2kwargs[l] = []
            for args, kwargs in lang_args.get(l, []):
                parser.add_argument(*args, **kwargs)
                lang_args2kwargs[l].append(parser._actions[-1].dest)
    args = parser.parse_args()
    lang_kwargs = {l: {k: getattr(args, k) for k in alist}
                   for l, alist in lang_args2kwargs.items()}
    if args.show_file:
        print('Config file located here: %s' % config.usr_config_file)
    if args.remove_file and os.path.isfile(config.usr_config_file):
        os.remove(config.usr_config_file)
    if args.show_file or args.remove_file:
        return
    config.update_language_config(args.languages, overwrite=args.overwrite,
                                  verbose=True,
                                  disable_languages=args.disable_languages,
                                  enable_languages=args.enable_languages,
                                  lang_kwargs=lang_kwargs)


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
    parser = install_languages.update_argparser()
    args = parser.parse_args()
    if (len(args.language) == 0) or ('all' in args.language):
        install_languages.install_all_languages(args=args)
    else:
        for x in args.language:
            install_languages.install_language(x, args=args)


def yggmodelform():
    r"""Save/print a JSON schema that can be used for generating a
    form for composing a model specification files."""
    from yggdrasil.schema import get_model_form_schema
    parser = argparse.ArgumentParser(
        description=('Save/print the JSON schema for generating the '
                     'model specification form.'))
    parser.add_argument('--file',
                        help='Path to file where the schema should be saved.')
    args = parser.parse_args()
    out = get_model_form_schema(fname_dst=args.file)
    if not args.file:
        pprint.pprint(out)


if __name__ == '__main__':
    yggrun()
    sys.exit(0)
