#!/usr/bin/python
import os
import sys
import copy
import logging
import subprocess
import argparse
import pprint
import shutil


logger = logging.getLogger(__name__)


def githook():
    r"""Git hook to determine if the Github workflow need to be
    re-generated."""
    try:
        files = subprocess.check_output(
            ["git", "diff-index", "--cached", "--name-only",
             "--diff-filter=ACMRTUXB", "HEAD"],
            stderr=subprocess.PIPE).decode('utf-8').splitlines()
    except subprocess.CalledProcessError:
        return 1
    regen = (os.path.join('utils', 'test-install-base.yml') in files)
    if regen:
        try:
            gitdir = subprocess.check_output(
                ["git", "rev-parse", "--git-dir"],
                stderr=subprocess.PIPE).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            return 1
        workflow_dir = os.path.join(gitdir, '..', '.github', 'workflows')
        generate_gha_workflow(args=[], gitdir=gitdir)
        try:
            subprocess.run(
                ['git', 'add',
                 os.path.join(workflow_dir, 'test-install.yml')],
                check=True,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return 1
    return 0


def generate_gha_workflow(args=None, gitdir=None):
    r"""Re-generate the Github actions workflow yaml."""
    import yaml
    from yggdrasil.metaschema.encoder import decode_yaml, encode_yaml
    from collections import OrderedDict

    class NoAliasDumper(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True
    if gitdir is None:
        try:
            gitdir = subprocess.check_output(
                ["git", "rev-parse", "--git-dir"],
                stderr=subprocess.PIPE).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            return 1
    parser = argparse.ArgumentParser(
        "Generate a Github Actions (GHA) workflow yaml file from "
        "a version of the file that uses anchors (not supported by "
        "GHA as of 2021-01-14).")
    parser.add_argument(
        '--base', '--base-file',
        default=os.path.join(gitdir, '..', 'utils',
                             'test-install-base.yml'),
        help="Version of GHA workflow yaml that contains anchors.")
    parser.add_argument(
        '--dest',
        default=os.path.join(gitdir, '..', '.github', 'workflows',
                             'test-install.yml'),
        help="Name of target GHA workflow yaml file.")
    parser.add_argument(
        '--verbose', action='store_true',
        help="Print yaml contents.")
    args = parser.parse_args(args=args)
    base = args.base
    dest = args.dest
    with open(base, 'r') as fd:
        contents = decode_yaml(fd.read(), sorted_dict_type=OrderedDict)
        # contents = yaml.load(fd, Loader=yaml.SafeLoader)
    if args.verbose:
        pprint.pprint(contents)
    with open(dest, 'w') as fd:
        fd.write(('# DO NOT MODIFY THIS FILE, IT IS GENERATED.\n'
                  '# To make changes, modify \'%s\'\n'
                  '# and run \'ygggha\'\n')
                 % args.base)
        fd.write(encode_yaml(contents, sorted_dict_type=OrderedDict,
                             Dumper=NoAliasDumper))
        # yaml.dump(contents, fd, Dumper=NoAliasDumper)


def ygginfo(args=None, return_str=False):
    r"""Print information about yggdrasil installation."""
    from yggdrasil import __version__, tools, config, platform
    from yggdrasil.components import import_component
    lang_list = tools.get_installed_lang()
    comm_list = tools.get_installed_comm()
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
    parser.add_argument('--no-comms', action='store_true', dest='no_comms',
                        help='Don\'t print information about individual comms.')
    parser.add_argument('--verbose', action='store_true',
                        help='Increase the verbosity of the printed information.')
    args = parser.parse_args(args=args)
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
                        exec_name = shutil.which(exec_name)
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
                if not drv.are_dependencies_installed():
                    vardict.append(
                        (curr_prefix + "Dependencies Not Installed",
                         [b for b in drv.interface_dependencies if
                          (not drv.is_library_installed(b))]))
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
        # Add comm information
        if not args.no_comms:
            # Fully installed comms
            vardict.append(('Comms Available for All Languages:', ''))
            curr_prefix += prefix
            for comm in sorted(comm_list):
                cmm = import_component('comm', comm)
                vardict.append((curr_prefix + '%s' % comm.upper(), ''))
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            # Partially installed comms
            vardict.append(('Comms Available for Some/No Languages:', ''))
            curr_prefix += prefix
            for comm in tools.get_supported_comm():
                if comm in comm_list:
                    continue
                cmm = import_component('comm', comm)
                vardict.append((curr_prefix + '%s:' % comm.upper(), ''))
                curr_prefix += prefix
                avail = [cmm.is_installed(language=lang) for lang in lang_list]
                vardict.append(
                    (curr_prefix + "Available for ",
                     sorted([lang_list[i].upper() for i in range(len(avail))
                             if avail[i]])))
                vardict.append(
                    (curr_prefix + "Not Available for ",
                     sorted([lang_list[i].upper() for i in range(len(avail))
                             if not avail[i]])))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
        # Add verbose information
        if args.verbose:
            # Path variables
            path_vars = ['PATH', 'C_INCLUDE_PATH', 'INCLUDE', 'LIBRARY_PATH',
                         'LD_LIBRARY_PATH', 'LIB']
            vardict.append(('Environment paths:', ''))
            curr_prefix += prefix
            for k in path_vars:
                if os.environ.get(k, ''):
                    vardict.append(
                        (curr_prefix + k, '\n%s%s'
                         % (curr_prefix + prefix,
                            ("\n" + curr_prefix + prefix).join(
                                os.environ[k].split(os.pathsep)))))
                else:
                    vardict.append((curr_prefix + k, ''))
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            # Environment variabless
            env_vars = ['CONDA_PREFIX', 'CONDA', 'SDKROOT', 'CC', 'CXX',
                        'FC', 'GFORTRAN', 'DISPLAY', 'CL', '_CL_']
            if platform._is_win:  # pragma: windows
                env_vars += ['VCPKG_ROOT']
            vardict.append(('Environment variables:', ''))
            curr_prefix += prefix
            for k in env_vars:
                vardict.append(
                    (curr_prefix + k, os.environ.get(k, None)))
            curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            # Conda info
            if os.environ.get('CONDA_PREFIX', ''):
                if platform._is_win:  # pragma: windows
                    out = tools.bytes2str(subprocess.check_output(
                        'conda info', shell=True)).strip()
                else:
                    out = tools.bytes2str(subprocess.check_output(
                        ['conda', 'info'])).strip()
                curr_prefix += prefix
                vardict.append((curr_prefix + 'Conda Info:', "\n%s%s"
                                % (curr_prefix + prefix,
                                   ("\n" + curr_prefix + prefix).join(
                                       out.splitlines(False)))))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            # Configuration
            with open(config.usr_config_file, 'r') as fd:
                contents = fd.read()
            vardict.append(
                ('Configuration file:', '%s\n\t%s' % (
                    config.usr_config_file,
                    '\n\t'.join(contents.splitlines()))))
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
                    try:
                        out = tools.bytes2str(subprocess.check_output(
                            [interp, 'CMD', 'config', x],
                            stderr=subprocess.STDOUT)).strip()
                    except subprocess.CalledProcessError:
                        out = 'ERROR (missing Rtools?)'
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
                if platform._is_win and shutil.which('conda'):  # pragma: windows
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
        msg = "yggdrasil info:\n%s" % '\n'.join(lines)
        if return_str:
            return msg
        logger.info(msg)


def yggrun():
    r"""Start a run."""
    from yggdrasil import runner, config
    parser = argparse.ArgumentParser(description='Run an integration.')
    parser.add_argument('yamlfile', nargs='+',
                        help='One or more yaml specification files.')
    config.get_config_parser(parser, skip_sections='testing')
    args = parser.parse_args()
    prog = sys.argv[0].split(os.path.sep)[-1]
    with config.parser_config(args):
        runner.run(args.yamlfile, ygg_debug_prefix=prog,
                   production_run=args.production_run)


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
    for lang in args.language:
        import_component('model', lang).cleanup_dependencies()


def yggcompile():
    r"""Compile interface library/libraries."""
    from yggdrasil.tools import get_supported_lang
    from yggdrasil.components import import_component
    yggclean()
    parser = argparse.ArgumentParser(
        description='Compile yggdrasil dependency libraries')
    parser.add_argument('language', nargs='*', default=[],
                        help=('One or more languages to compile the '
                              'interface libraries for.'))
    parser.add_argument('--toolname',
                        help=('Name of compilation tool that should be '
                              'used.'))
    args = parser.parse_args()
    if (len(args.language) == 0) or ('all' in args.language):
        args.language = get_supported_lang()
    for lang in args.language:
        drv = import_component('model', lang)
        if ((hasattr(drv, 'compile_dependencies')
             and drv.is_installed()
             and (not getattr(drv, 'is_build_tool', False)))):
            drv.compile_dependencies(toolname=args.toolname)


def yggcc():
    r"""Compile C/C++ program."""
    from yggdrasil.drivers import CModelDriver
    parser = argparse.ArgumentParser(description='Compile a C/C++ program.')
    parser.add_argument('source', nargs='+',
                        help='One or more source files.')
    args = parser.parse_args()
    out = CModelDriver.CModelDriver.call_compile(args.source)
    print("executable: %s" % out)


def cc_toolname():
    r"""Output the name of the compiler used to compile C or C++ programs."""
    parser = argparse.ArgumentParser(
        description='Get the compiler used for C/C++ programs.')
    parser.add_argument('--cpp', action='store_true',
                        help='Get the compiler used for C++ programs.')
    args = parser.parse_args()
    if args.cpp:
        from yggdrasil.drivers.CPPModelDriver import CPPModelDriver as driver
    else:
        from yggdrasil.drivers.CModelDriver import CModelDriver as driver
    out = driver.get_tool('compiler', return_prop='name')
    print(out)


def ld_toolname():
    r"""Output the name of the linker used to compile C or C++ programs."""
    parser = argparse.ArgumentParser(
        description='Get the linker used for C/C++ programs.')
    parser.add_argument('--cpp', action='store_true',
                        help='Get the linker used for C++ programs.')
    args = parser.parse_args()
    if args.cpp:
        from yggdrasil.drivers.CPPModelDriver import CPPModelDriver as driver
    else:
        from yggdrasil.drivers.CModelDriver import CModelDriver as driver
    out = driver.get_tool('linker', return_prop='name')
    print(out)


def cc_flags():
    r"""Get the compiler flags necessary for including the interface
    library in a C or C++ program.

    Returns:
        list: The necessary compiler flags and preprocessor definitions.

    """
    from yggdrasil import platform
    parser = argparse.ArgumentParser(
        description='Get the compilation flags necessary for a C/C++ program.')
    parser.add_argument('--cpp', action='store_true',
                        help='Get compilation flags for a C++ program.')
    parser.add_argument('--toolname', default=None,
                        help=('Name of the tool that associated flags should '
                              'be returned for.'))
    args = parser.parse_args()
    if args.cpp:
        from yggdrasil.drivers.CPPModelDriver import CPPModelDriver as driver
    else:
        from yggdrasil.drivers.CModelDriver import CModelDriver as driver
    out = ' '.join(driver.get_compiler_flags(for_model=True,
                                             toolname=args.toolname,
                                             dry_run=True))
    if platform._is_win:  # pragma: windows:
        if out.endswith(' /link'):
            out = out[:-(len(' /link'))]
        out = out.replace('/', '-')
        out = out.replace('\\', '/')
        # out = out.encode('unicode_escape').decode('utf-8')
    print(out)


def ld_flags():
    r"""Get the linker flags necessary for calling functions/classes from
    the interface library in a C or C++ program.

    Returns:
        list: The necessary library linking flags.

    """
    from yggdrasil import platform
    parser = argparse.ArgumentParser(
        description='Get the linker flags necessary for a C/C++ program.')
    parser.add_argument('--cpp', action='store_true',
                        help='Get linker flags for a C++ program.')
    parser.add_argument('--toolname', default=None,
                        help=('Name of the tool that associated flags should '
                              'be returned for.'))
    args = parser.parse_args()
    if args.cpp:
        from yggdrasil.drivers.CPPModelDriver import CPPModelDriver as driver
    else:
        from yggdrasil.drivers.CModelDriver import CModelDriver as driver
    out = ' '.join(driver.get_linker_flags(for_model=True,
                                           toolname=args.toolname,
                                           dry_run=True))
    if platform._is_win:  # pragma: windows:
        out = out.replace('/', '-')
        out = out.replace('\\', '/')
        # out = out.encode('unicode_escape').decode('utf-8')
    print(out)


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
    lang_args.setdefault('c', [])
    lang_args['c'].append(
        (('--vcpkg-dir', ),
         {'help': 'Directory containing the vcpkg installation.'}))
    if platform._is_mac:
        lang_args.setdefault('c', [])
        lang_args['c'].append(
            (('--macos-sdkroot', '--sdkroot'),
             {'help': (
                 'The full path to the MacOS SDK '
                 'that should be used.')}))
    for lang in prelang:
        if lang in lang_args:
            lang_args2kwargs[lang] = []
            for args, kwargs in lang_args.get(lang, []):
                parser.add_argument(*args, **kwargs)
                lang_args2kwargs[lang].append(parser._actions[-1].dest)
    args = parser.parse_args()
    lang_kwargs = {lang: {k: getattr(args, k) for k in alist}
                   for lang, alist in lang_args2kwargs.items()}
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


def yggdevup():
    r"""Cleanup old libraries, re-install languages, and re-compile interface
    libraries following an update to the code (when doing development)."""
    parser = argparse.ArgumentParser(
        description=('Perform cleanup and reinitialization following an '
                     'update to the code during development.'))
    parser.parse_args()
    yggclean()
    ygginstall()
    yggcompile()
    ygginfo()


if __name__ == '__main__':
    yggrun()
    sys.exit(0)
