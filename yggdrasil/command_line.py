#!/usr/bin/python
import os
import sys
import copy
import logging
import subprocess
import argparse
import pprint
import shutil
import sysconfig
from yggdrasil import constants
LANGUAGES = getattr(constants, 'LANGUAGES', {})
LANGUAGES_WITH_ALIASES = getattr(constants, 'LANGUAGES_WITH_ALIASES', {})


logger = logging.getLogger(__name__)
package_dir = os.path.dirname(os.path.abspath(__file__))


def githook():
    r"""Git hook to determine if the Github workflow need to be
    re-generated."""
    # This check is not required when using pre-commit package
    # try:
    #     files = subprocess.check_output(
    #         ["git", "diff-index", "--cached", "--name-only",
    #          "--diff-filter=ACMRTUXB", "HEAD"],
    #         stderr=subprocess.PIPE).decode('utf-8').splitlines()
    # except subprocess.CalledProcessError:
    #     return 1
    # regen = (os.path.join('utils', 'test-install-base.yml') in files)
    regen = True
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


class ArgumentTuple(tuple):

    def __new__(self, args, kwargs):
        return tuple.__new__(ArgumentTuple, (args, kwargs))


class ConditionalArgumentTuple(ArgumentTuple):

    def __new__(cls, args, kwargs, conditions=None):
        out = ArgumentTuple.__new__(ConditionalArgumentTuple,
                                    args, kwargs)
        out.conditions = conditions
        if out.conditions is None:
            out.conditions = {}
        return out
            

class ArgumentBase(object):
    
    def __init__(self, arguments=None, conditions=None, **kwargs):
        self.arguments = arguments
        if self.arguments is None:
            self.arguments = []
        self.conditions = conditions
        if self.conditions is None:
            self.conditions = {}
        self.kwargs = kwargs


class ArgumentParser(ArgumentBase):
    pass


class ArgumentGroup(ArgumentBase):

    def __init__(self, exclusive=False, **kwargs):
        self.exclusive = exclusive
        super(ArgumentGroup, self).__init__(**kwargs)


class ArgumentSubparser(ArgumentBase):

    def __init__(self, parsers=None, **kwargs):
        self.parsers = parsers
        if self.parsers is None:
            self.parsers = []
        super(ArgumentSubparser, self).__init__(**kwargs)


class SubCommandMeta(type):
    r"""Meta class for subcommands."""

    def __call__(cls, *args, **kwargs):
        return cls.call(*args, **kwargs)


def ReplacementWarning(old, new):
    import warnings
    warnings.warn(("'%s' will soon be removed. Use '%s' instead.")
                  % (old, new), FutureWarning)


class SubCommand(metaclass=SubCommandMeta):
    r"""Class for handling subcommands so that they can be run
    as subcommands or individually."""

    name = None
    help = None
    arguments = []
    allow_unknown = False

    @classmethod
    def parse_args(cls, parser, args=None, allow_unknown=False,
                   namespace=None):
        # TODO: Check choices for positional arguments that can
        # have more than one element
        if isinstance(args, argparse.Namespace):
            return args
        kws = dict(args=args)
        if namespace is not None:
            kws['namespace'] = namespace
        if cls.allow_unknown or allow_unknown:
            args, extra = parser.parse_known_args(**kws)
            args._extra_commands = extra
        else:
            args = parser.parse_args(**kws)
        for k in ['language', 'languages']:
            v = getattr(args, k, None)
            if isinstance(v, list):
                v_flag = getattr(args, k + '_flag', None)
                if isinstance(v_flag, list):
                    v.extend(v_flag)
                if (len(v) == 0) or ('all' in v):
                    setattr(args, k, LANGUAGES.get('all', []))
                    args.all_languages = True
        return args

    @classmethod
    def func(cls, args):  # pragma: debug
        raise NotImplementedError

    @classmethod
    def call(cls, args=None, namespace=None, **kwargs):
        parser = cls.get_parser(args=args)
        args = cls.parse_args(parser, args=args, namespace=namespace)
        return cls.func(args, **kwargs)

    @classmethod
    def get_parser(cls, args=None):
        parser = argparse.ArgumentParser(cls.help)
        cls.add_arguments(parser, args=args)
        return parser

    @classmethod
    def add_argument_to_parser(cls, parser, x):
        if hasattr(x, 'conditions') and x.conditions:
            for k, v in x.conditions.items():
                if k == 'os':
                    from yggdrasil import platform
                    if platform._platform not in v:
                        return
                else:  # pragma: debug
                    raise NotImplementedError(k)
        if isinstance(x, list):
            for xx in x:
                cls.add_argument_to_parser(parser, xx)
        elif isinstance(x, (tuple, ArgumentTuple,
                            ConditionalArgumentTuple)):
            assert len(x) == 2
            args, kwargs = x[:]
            try:
                parser.add_argument(*args, **kwargs)
            except ValueError:
                if kwargs.get('action', None) == 'extend':
                    kwargs['action'] = 'append'
                    kwargs.pop('nargs', None)
                    parser.add_argument(*args, **kwargs)
                else:
                    raise
        elif isinstance(x, ArgumentGroup):
            if x.exclusive:
                group = parser.add_mutually_exclusive_group(**x.kwargs)
            else:
                group = parser.add_argument_group(**x.kwargs)
            cls.add_argument_to_parser(group, x.arguments)
        elif isinstance(x, ArgumentSubparser):
            subparsers = parser.add_subparsers(**x.kwargs)
            for xx in x.parsers:
                isubparser = subparsers.add_parser(**xx.kwargs)
                cls.add_argument_to_parser(isubparser, x.arguments)
                cls.add_argument_to_parser(isubparser, xx.arguments)
        else:
            raise NotImplementedError("type(x) = %s" % type(x))

    @classmethod
    def runtime_arguments(cls):
        return []

    @classmethod
    def add_arguments(cls, parser, args=None):
        args = copy.deepcopy(cls.arguments)
        for new_param in cls.runtime_arguments():
            for old_param in args:
                if new_param[0] == old_param[0]:
                    old_param[1].update(new_param[1])
        cls.add_argument_to_parser(parser, cls.arguments)

    @classmethod
    def add_subparser(cls, subparsers, args=None):
        parser = subparsers.add_parser(cls.name, help=cls.help)
        cls.add_arguments(parser, args=args)
        parser.set_defaults(func=cls.func)


class yggrun(SubCommand):
    r"""Start a run."""

    name = "run"
    help = "Run an integration."
    arguments = [
        (('yamlfile', ),
         {'nargs': '+',
          'help': "One or more yaml specification files."}),
        (('--with-mpi', '--mpi-nproc'),
         {'type': int, 'default': 1,
          'help': 'Number of MPI processes to run on.'}),
        (('--mpi-tag-start', ),
         {'type': int, 'default': 0,
          'help': 'Tag that MPI communications should start at.'}),
        (('--validate', ),
         {'action': 'store_true',
          'help': ('Validate the run via model validation commands on '
                   'completion.')}),
        (('--with-debugger', ),
         {'type': str,
          'help': ('Run all models with a specific debuggin tool. If '
                   'quoted, this can also include flags for the tool.')}),
        (('--disable-python-c-api', ),
         {'action': 'store_true',
          'help': 'Disable access to the Python C API from yggdrasil.'}),
        (('--with-asan', ),
         {'action': 'store_true',
          'help': 'Compile models with the address sanitizer enabled.'}),
        (('--as-service', ),
         {'action': 'store_true',
          'help': 'Run the provided YAMLs as a service.'}),
        (('--partial-commtype', ),
         {'type': str, 'default': 'rest',
          'help': ('Type of communicator to use for partial comms when '
                   '--as-service is passed')}),
        (('--client-id', ),
         {'type': str,
          'help': ('ID associated with the client requesting a service. '
                   '(This should only be passed when running with '
                   '--as-service)')}),
    ]

    @classmethod
    def add_arguments(cls, parser, **kwargs):
        from yggdrasil import config
        super(yggrun, cls).add_arguments(parser, **kwargs)
        config.get_config_parser(parser, skip_sections='testing')

    @classmethod
    def func(cls, args):
        if args.with_mpi > 1:
            new_args = ['mpiexec', '-n', str(args.with_mpi)]
            i = 0
            while i < len(sys.argv):
                x = sys.argv[i]
                if x.startswith(('--with-mpi', '--mpi-nproc')):
                    if '=' not in x:
                        i += 1
                else:
                    new_args.append(x)
                i += 1
            return subprocess.check_call(new_args)
        from yggdrasil import runner, config
        prog = sys.argv[0].split(os.path.sep)[-1]
        with config.parser_config(args):
            kwargs = dict(
                ygg_debug_prefix=prog,
                production_run=args.production_run,
                mpi_tag_start=args.mpi_tag_start,
                validate=args.validate,
                with_debugger=args.with_debugger,
                disable_python_c_api=args.disable_python_c_api,
                with_asan=args.with_asan,
                as_service=args.as_service)
            if args.as_service:
                kwargs['complete_partial'] = True
                if not args.partial_commtype:
                    args.partial_commtype = 'rest'
            if args.partial_commtype:
                kwargs['partial_commtype'] = {
                    'commtype': args.partial_commtype}
                if args.as_service and args.partial_commtype == 'rest':
                    assert args.client_id
                    kwargs['partial_commtype']['client_id'] = args.client_id
            runner.run(args.yamlfile, **kwargs)


class integration_service_manager(SubCommand):
    r"""Start or manage the yggdrasil service manager."""

    name = "integration-service-manager"
    help = "Start or manage a integration service manager."
    arguments = [
        (('--manager-name', ),
         {'help': "Name that will be used to identify the service manager."}),
        (('--service-type', ),
         {'choices': ['flask', 'rmq'],
          'help': ("Type of service that should be started. If not "
                   "provided, the default will be the (\'services\', "
                   "\'default_type\') configuration option, if set, and "
                   "will otherwise be \'flask\'.")}),
        (('--commtype', ),
         {'type': str,
          'help': ("Type of communicator that should be used for connections "
                   "to services. If not provided, the default will be "
                   "determined by the (\'services\', \'default_comm\') "
                   "configuration option, if set.")}),
        (('--address', ),
         {'type': str,
          'help': ('URL for requests to the service manager. '
                   'If not provided, the default will be determined by the '
                   '(\'services\', \'default_type\') configuration option, '
                   'if set, and based on the selected \'service-type\', if '
                   'not. For a service-type of \'flask\', this should be the '
                   'http address with the port that should be used '
                   'and the default will be \'http://localhost:{port}\'. '
                   'For a service-type of \'rmq\', this should be an '
                   'amqp broker address and the default will be '
                   '\'amqp://guest:guest@localhost:{port}/%%2f\'.')}),
        (('--port', ),
         {'type': int,
          'help': ('Port that should be used to access the app. '
                   'Defaults to 5000 for a flask service manager and '
                   '5672 for a RabbitMQ service manager if not set '
                   'via the PORT environment variable.')}),
        ArgumentSubparser(
            title='action', dest='action',
            description='Management action to take.',
            parsers=[
                ArgumentParser(
                    name='start',
                    help=('Start an integration service manager and/or '
                          'integration service.'),
                    arguments=[
                        (('--remote-url', ),
                         {'type': str,
                          'help': ('URL that will be used to access '
                                   'the service manager and running '
                                   'integrations by remote requests. '
                                   'If not provided, the environment '
                                   'variable YGGDRASIL_SERVICE_HOST_URL '
                                   'will be used if it is set. If it is '
                                   'not set, the local ``address`` will '
                                   'be used under the assumption that '
                                   'the service manager and integration '
                                   'services will only be connected to '
                                   'by local integrations.')}),
                        (('--integration-name', ),
                         {'default': None,
                          'help': ('Name of integration to start. If not '
                                   'provided, a service manager will be '
                                   'started.')}),
                        (('--integration-yamls', ),
                         {'nargs': '+',
                          'help': ('One or more YAML specification files '
                                   'defining the integration. This argument '
                                   'may be omitted if \'name\' refers to a '
                                   'registered integration.')}),
                        (('--with-coverage', ),
                         {'action': 'store_true',
                          'help': ('Enable coverage cleanup for testing.')}),
                        (('--model-repository', ),
                         {'type': str,
                          'help': ('URL for a directory in a Git repository '
                                   'containing models that should be loaded '
                                   'into the service manager registry.')}),
                        (('--track-memory', ),
                         {'action': 'store_true',
                          'help': ('Track the memory used by the '
                                   'service manager.')}),
                        (('--log-level', ),
                         {'type': int,
                          'help': ('Level of logging that should be '
                                   'performed for the service manager '
                                   'application.')})]),
                ArgumentParser(
                    name='stop',
                    help=('Stop an integration service manager or '
                          'an integration service.'),
                    arguments=[
                        (('--integration-name', ),
                         {'default': None,
                          'help': ('Name of integration to stop. If not '
                                   'provided, the service manager will be '
                                   'stopped as will all of the running '
                                   'services.')})]),
                ArgumentParser(
                    name='status',
                    help=('Get list of available services and the status '
                          'of any running services.')),
                ArgumentParser(
                    name='register',
                    help='Register an integration with the service manager.',
                    arguments=[
                        (('integration-name', ),
                         {'type': str,
                          'help': ('The name that the integration should be '
                                   'registered under or the path to a YAML '
                                   'file containing a list of one or more '
                                   'mappings between name and YAML '
                                   'specification files for integrations '
                                   'that should be registered.')}),
                        (('integration-yamls', ),
                         {'nargs': '*',
                          'help': ('One or more YAML specification files '
                                   'defining the integration.')})]),
                ArgumentParser(
                    name='unregister',
                    help='Unregister an integration with the service manager.',
                    arguments=[
                        (('integration-name', ),
                         {'type': str,
                          'help': ('The name of the integration to remove '
                                   'from the registry or the path to a YAML '
                                   'file containing a list of one or more '
                                   'mappings between integration name and '
                                   'YAML specification files for '
                                   'integrations that should be '
                                   'unregistered.')})]),
            ])]

    @classmethod
    def func(cls, args):
        from yggdrasil.services import IntegrationServiceManager
        integration_name = getattr(args, 'integration-name',
                                   getattr(args, 'integration_name', None))
        integration_yamls0 = getattr(args, 'integration-yamls',
                                     getattr(args, 'integration_yamls', None))
        integration_yamls = []
        if integration_yamls0:
            for yml in integration_yamls0:
                if not os.path.isabs(yml):
                    yml = os.path.abspath(yml)
                integration_yamls.append(yml)
        elif integration_name and os.path.isfile(integration_name):
            if not os.path.isabs(integration_name):
                integration_name = os.path.abspath(integration_name)
        for_request = (
            (args.action in ['status', 'register', 'unregister', 'stop'])
            or (integration_name is not None))
        x = IntegrationServiceManager(name=args.manager_name,
                                      service_type=args.service_type,
                                      commtype=args.commtype,
                                      address=args.address,
                                      port=args.port,
                                      for_request=for_request)
        if args.action in ['start', None]:
            if integration_name is None:
                if not x.is_running:
                    x.start_server(
                        remote_url=getattr(args, 'remote_url', None),
                        with_coverage=getattr(args, 'with_coverage', False),
                        model_repository=getattr(args, 'model_repository',
                                                 None),
                        log_level=getattr(args, 'log_level', None),
                        track_memory=getattr(args, 'track_memory', False))
            else:
                x.send_request(integration_name,
                               yamls=integration_yamls,
                               action='start')
        elif args.action == 'stop':
            if integration_name is None:
                x.stop_server()
            else:
                x.send_request(integration_name, action='stop')
        elif args.action == 'status':
            x.printStatus()
        elif args.action == 'register':
            x.registry.add(name=integration_name,
                           yamls=integration_yamls)
        elif args.action == 'unregister':
            x.registry.remove(name=integration_name)
        else:
            raise NotImplementedError(args.action)


class ygginfo(SubCommand):
    r"""Print information about yggdrasil installation."""

    name = 'info'
    help = ('Display information about the current yggdrasil '
            'installation.')
    arguments = [
        (('--no-languages', ),
         {'action': 'store_true', 'dest': 'no_languages',
          'help': ('Don\'t print information about individual '
                   'languages.')}),
        (('--no-comms', ),
         {'action': 'store_true', 'dest': 'no_comms',
          'help': ('Don\'t print information about individual '
                   'comms.')}),
        (('--verbose', '-v'),
         {'action': 'store_true',
          'help': ('Increase the verbosity of the printed '
                   'information.')}),
        ArgumentSubparser(
            title='tool', dest='tool',
            description='Compilation tool types to get info about.',
            arguments=[
                (('language', ),
                 {'choices': LANGUAGES_WITH_ALIASES.get('compiled', []),
                  'type': str.lower,
                  'help': 'Language to get tool information for.'}),
                (('--toolname', ),
                 {'default': None,
                  'help': ('Name of tool to get information for. '
                           'If not provided, information for the '
                           'default tool will be returned.')}),
                (('--flags', ),
                 {'action': 'store_true',
                  'help': ('Display the flags that yggdrasil will '
                           ' pass to the tool when it is called.')}),
                (('--fullpath', ),
                 {'action': 'store_true',
                  'help': 'Get the full path to the tool exectuable.'}),
                (('--disable-python-c-api', ),
                 {'action': 'store_true',
                  'help': 'Disable access to the Python C API from yggdrasil.'}),
                (('--with-asan', ),
                 {'action': 'store_true',
                  'help': "Compile with Clang ASAN if available."}),
            ],
            parsers=[
                ArgumentParser(
                    name='compiler',
                    help='Get information about a compiler.'),
                ArgumentParser(
                    name='linker',
                    help='Get information about a linker.',
                    arguments=[
                        (('--library', ),
                         {'action': 'store_true',
                          'help': 'Get flags for linking a library.'})]),
                ArgumentParser(
                    name='archiver',
                    help='Get information about a archiver.')])]

    @classmethod
    def func(cls, args, return_str=False):
        from yggdrasil import platform
        from yggdrasil.components import import_component
        if args.tool:
            drv = import_component('model', args.language)
            if args.flags:
                if args.tool == 'compiler':
                    flags = drv.get_compiler_flags(
                        for_model=True, toolname=args.toolname,
                        dry_run=True, dont_link=True,
                        disable_python_c_api=args.disable_python_c_api,
                        with_asan=args.with_asan)
                    if '/link' in flags:  # pragma: windows
                        flags = flags[:flags.index('/link')]
                    for k in ['-c']:
                        if k in flags:
                            flags.remove(k)
                else:
                    if args.tool == 'archiver':
                        libtype = 'static'
                    elif getattr(args, 'library', False):
                        libtype = 'shared'
                    else:
                        libtype = 'object'
                    flags = drv.get_linker_flags(
                        for_model=True, toolname=args.toolname,
                        dry_run=True, libtype=libtype,
                        disable_python_c_api=args.disable_python_c_api,
                        with_asan=args.with_asan)
                out = ' '.join(flags)
                if platform._is_win:  # pragma: windows:
                    out = out.replace('/', '-')
                    out = out.replace('\\', '/')
            elif args.fullpath:
                out = drv.get_tool(args.tool).get_executable(full_path=True)
            else:
                out = drv.get_tool(args.tool, return_prop='name')
            if return_str:
                return out
            print(out)
            return
        from yggdrasil import tools, config, __version__
        lang_list = tools.get_installed_lang()
        comm_list = tools.get_installed_comm()
        comm_lang_list = []
        prefix = '    '
        curr_prefix = ''
        vardict = [
            ('Location', os.path.dirname(__file__)),
            ('Version', __version__),
            ('Languages', ', '.join(lang_list)),
            ('Communication Mechanisms',
             ', '.join(tools.get_installed_comm())),
            ('Default Comm Mechanism', tools.get_default_comm()),
            ('Config File', config.usr_config_file)]
        try:
            # Add language information
            if not args.no_languages:
                # Install languages
                vardict.append(('Installed Languages:', ''))
                curr_prefix += prefix
                for lang in sorted(lang_list):
                    drv = import_component('model', lang)
                    vardict.append(
                        (curr_prefix + '%s:' % lang.upper(), ''))
                    if not drv.comms_implicit:
                        comm_lang_list.append(lang)
                    curr_prefix += prefix
                    exec_name = drv.language_executable()
                    if exec_name:
                        if not os.path.isabs(exec_name):
                            exec_name = shutil.which(exec_name)
                        vardict.append((curr_prefix + 'Location',
                                        exec_name))
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
                    vardict.append(
                        (curr_prefix + '%s:' % lang.upper(), ''))
                    curr_prefix += prefix
                    vardict.append(
                        (curr_prefix + "Language Installed",
                         drv.is_language_installed()))
                    if drv.executable_type == 'compiler':
                        curr_prefix += prefix
                        vardict += [
                            (curr_prefix
                             + ("%s Installed (%s)"
                                % (x.title(),
                                   getattr(drv, 'default_%s' % x, None))),
                             drv.is_tool_installed(x))
                            for x in ['compiler', 'linker', 'archiver']]
                        curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                    vardict.append(
                        (curr_prefix + "Base Languages Installed",
                         drv.are_base_languages_installed()))
                    missing = []
                    if not drv.are_base_languages_installed(
                            missing=missing):
                        vardict.append(
                            (curr_prefix
                             + "Base Languages Not Installed",
                             missing))
                    vardict.append(
                        (curr_prefix + "Dependencies Installed",
                         drv.are_dependencies_installed()))
                    if not drv.are_dependencies_installed():
                        vardict.append(
                            (curr_prefix
                             + "Dependencies Not Installed",
                             [b for b in drv.interface_dependencies if
                              (not drv.is_library_installed(b))]))
                    vardict.append(
                        (curr_prefix + "Interface Installed",
                         drv.is_interface_installed()))
                    vardict.append((curr_prefix + "Comm Installed",
                                    drv.is_comm_installed()))
                    vardict.append((curr_prefix + "Configured",
                                    drv.is_configured()))
                    if not vardict[-1][1]:
                        curr_prefix += prefix
                        for k, v in drv.configuration_steps().items():
                            vardict.append((curr_prefix + k, v))
                        curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                    curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            # Add comm information
            if not args.no_comms:
                # Fully installed comms
                vardict.append(
                    ('Comms Available for All Languages:', ''))
                curr_prefix += prefix
                for comm in sorted(comm_list):
                    cmm = import_component('comm', comm)
                    vardict.append(
                        (curr_prefix + '%s' % comm.upper(), ''))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                # Partially installed comms
                vardict.append(
                    ('Comms Available for Some/No Languages:', ''))
                curr_prefix += prefix
                for comm in tools.get_supported_comm():
                    if comm in comm_list:
                        continue
                    cmm = import_component('comm', comm)
                    vardict.append(
                        (curr_prefix + '%s:' % comm.upper(), ''))
                    curr_prefix += prefix
                    avail = [cmm.is_installed(language=lang)
                             for lang in comm_lang_list]
                    vardict.append(
                        (curr_prefix + "Available for ",
                         sorted([comm_lang_list[i].upper()
                                 for i in range(len(avail))
                                 if avail[i]])))
                    vardict.append(
                        (curr_prefix + "Not Available for ",
                         sorted([comm_lang_list[i].upper()
                                 for i in range(len(avail))
                                 if not avail[i]])))
                    curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
            # Add verbose information
            if args.verbose:
                # Path variables
                path_vars = ['PATH', 'C_INCLUDE_PATH', 'INCLUDE',
                             'LIBRARY_PATH', 'LD_LIBRARY_PATH', 'LIB']
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
                env_vars = ['CONDA_PREFIX', 'CONDA', 'SDKROOT', 'CC',
                            'CXX', 'FC', 'GFORTRAN', 'DISPLAY', 'CL',
                            '_CL_', 'LD', 'CFLAGS', 'CXXFLAGS',
                            'LDFLAGS', 'CONDA_JL_HOME',
                            'CONDA_JL_CONDA_EXE', 'JULIA_DEPOT_PATH',
                            'JULIA_LOAD_PATH', 'JULIA_PROJECT',
                            'JULIA_SSL_CA_ROOTS_PATH']
                if platform._is_win:  # pragma: windows
                    env_vars += ['VCPKG_ROOT']
                vardict.append(('Environment variables:', ''))
                curr_prefix += prefix
                for k in env_vars:
                    vardict.append(
                        (curr_prefix + k, os.environ.get(k, None)))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                # Locations of executables
                for x in ['git', 'mpiexec', 'mpicc']:
                    vardict.append((f'{x} Location:', shutil.which(x)))
                # Conda info
                if os.environ.get('CONDA_PREFIX', ''):
                    if platform._is_win:  # pragma: windows
                        out = tools.bytes2str(subprocess.check_output(
                            'conda info', shell=True)).strip()
                    else:
                        out = tools.bytes2str(subprocess.check_output(
                            ['conda', 'info'])).strip()
                    curr_prefix += prefix
                    vardict.append(
                        (curr_prefix + 'Conda Info:', "\n%s%s"
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
                    out = Rdrv.run_executable(
                        ["-e", "Cstack_info()"]).strip()
                    vardict.append(
                        (curr_prefix + "R Cstack_info:", "\n%s%s"
                         % (curr_prefix + prefix,
                            ("\n" + curr_prefix + prefix).join(
                                out.splitlines(False)))))
                    # Compilation tools
                    interp = 'R'.join(
                        Rdrv.get_interpreter().rsplit('Rscript', 1))
                    vardict.append(
                        (curr_prefix + "R C Compiler:", ""))
                    curr_prefix += prefix
                    for x in ['CC', 'CFLAGS', 'CXX', 'CXXFLAGS']:
                        try:
                            out = tools.bytes2str(
                                subprocess.check_output(
                                    [interp, 'CMD', 'config', x],
                                    stderr=subprocess.STDOUT)).strip()
                        except subprocess.CalledProcessError:
                            out = 'ERROR (missing Rtools?)'
                        vardict.append(
                            (curr_prefix + x, "%s"
                             % ("\n" + curr_prefix + prefix).join(
                                 out.splitlines(False))))
                    curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                    # Session info
                    out = Rdrv.run_executable(
                        ["-e", "sessionInfo()"]).strip()
                    vardict.append(
                        (curr_prefix + "R sessionInfo:", "\n%s%s"
                         % (curr_prefix + prefix,
                            ("\n" + curr_prefix + prefix).join(
                                out.splitlines(False)))))
                    # Reticulate conda_list
                    if os.environ.get('CONDA_PREFIX', ''):
                        if platform._is_win:  # pragma: windows
                            out = tools.bytes2str(subprocess.check_output(
                                'conda info --json', shell=True)).strip()
                        else:
                            out = tools.bytes2str(subprocess.check_output(
                                ['conda', 'info', '--json'])).strip()
                        vardict.append(
                            (curr_prefix
                             + "conda info --json",
                             "\n%s%s" % (
                                 curr_prefix + prefix,
                                 ("\n" + curr_prefix + prefix).join(
                                     out.splitlines(False)))))
                        try:
                            out = Rdrv.run_executable(
                                ["-e", ("library(reticulate); "
                                        "reticulate::conda_list()")],
                                env=env_reticulate).strip()
                        except BaseException:  # pragma: debug
                            out = 'ERROR'
                        vardict.append(
                            (curr_prefix
                             + "R reticulate::conda_list():",
                             "\n%s%s" % (
                                 curr_prefix + prefix,
                                 ("\n" + curr_prefix + prefix).join(
                                     out.splitlines(False)))))
                    # Windows python versions
                    if platform._is_win:  # pragma: windows
                        out = Rdrv.run_executable(
                            ["-e",
                             ("library(reticulate); "
                              "reticulate::py_versions_windows()")],
                            env=env_reticulate).strip()
                        vardict.append(
                            (curr_prefix
                             + "R reticulate::py_versions_windows():",
                             "\n%s%s" % (
                                 curr_prefix + prefix,
                                 ("\n" + curr_prefix + prefix).join(
                                     out.splitlines(False)))))
                    # conda_binary
                    if platform._is_win and shutil.which('conda'):  # pragma: windows
                        out = Rdrv.run_executable(
                            ["-e",
                             ("library(reticulate); "
                              "conda <- reticulate:::conda_binary(\"auto\"); "
                              "system(paste(conda, \"info --json\"))")],
                            env=env_reticulate).strip()
                        vardict.append(
                            (curr_prefix
                             + "R reticulate::py_versions_windows():",
                             "\n%s%s" % (
                                 curr_prefix + prefix,
                                 ("\n" + curr_prefix + prefix).join(
                                     out.splitlines(False)))))
                    # Reticulate py_config
                    out = Rdrv.run_executable(
                        ["-e", ("library(reticulate); "
                                "reticulate::py_config()")],
                        env=env_reticulate).strip()
                    vardict.append(
                        (curr_prefix + "R reticulate::py_config():",
                         "\n%s%s" % (
                             curr_prefix + prefix,
                             ("\n" + curr_prefix + prefix).join(
                                 out.splitlines(False)))))
                # System config vars
                vardict.append(('Sysconfig Vars:', ''))
                curr_prefix += prefix
                for k, v in sysconfig.get_config_vars().items():
                    vardict.append((curr_prefix + k, v))
                curr_prefix = curr_prefix.rsplit(prefix, 1)[0]
                # ASAN library
                asan_library = None
                Cdrv = import_component("model", "c")
                if Cdrv.is_installed():
                    asan_library = Cdrv.get_tool("compiler").asan_library()
                vardict.append(("Asan Library:", asan_library))
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

        
class validate_yaml(SubCommand):
    r"""Validate a set of or or more YAMLs defining an integration."""

    name = "validate"
    help = 'Validate a set of YAML specification files for an integration.'
    arguments = [
        (('yamlfile', ),
         {'nargs': '+',
          'help': 'One or more YAML specification files.'}),
        (('--model-only', ),
         {'action': 'store_true',
          'help': ('Validate a YAML containing an isolated model without '
                   'ensuring that it is part of a complete integration.')}),
        (('--model-submission', ),
         {'action': 'store_true',
          'help': ('Validate a YAML against the requirements for '
                   'submissions to the yggdrasil model repository.')})]

    @classmethod
    def func(cls, args):
        if args.model_submission:
            from yggdrasil.services import validate_model_submission
            validate_model_submission(args.yamlfile)
        else:
            from yggdrasil import yamlfile
            yamlfile.parse_yaml(args.yamlfile, model_only=args.model_only,
                                model_submission=args.model_submission)
        logger.info("Validation succesful.")


class yggcc(SubCommand):
    r"""Compile a program."""

    name = "compile-model"
    help = ("Compile a program from source files for use in an "
            "yggdrasil integration.")
    arguments = [
        (('source', ),
         {'nargs': '+',
          'help': ("One or more source files or the directory containing an "
                   "R package.")}),
        (('--language', ),
         {'default': None,
          'choices': ([None] + LANGUAGES_WITH_ALIASES.get('compiled', [])
                      + ['R', 'r']),
          'help': ("Language of the source code. If not provided, "
                   "the language will be determined from the "
                   "source extension.")}),
        (('--toolname', ),
         {'help': "Name of compilation tool that should be used"}),
        (('--flags', ),
         {'nargs': '*',
          'help': ("Additional flags that should be added to the compilation "
                   "command")}),
        (('--use-ccache', ),
         {'action': 'store_true', 'help': "Run compilation with ccache."}),
        (('--Rpkg-language', ),
         {'help': ("Language that R package is written in "
                   "(only used if the specified language is R).")}),
        (('--disable-python-c-api', ),
         {'action': 'store_true',
          'help': 'Disable access to the Python C API from yggdrasil.'}),
        (('--with-asan', ),
         {'action': 'store_true',
          'help': "Compile with Clang ASAN if available."})]

    @classmethod
    def func(cls, args):
        from yggdrasil.components import import_component
        from yggdrasil.constants import EXT2LANG
        if args.language is None:
            if (((len(args.source) == 1) and os.path.isdir(args.source[0])
                 and os.path.isdir(os.path.join(args.source[0], 'R')))):
                args.language = 'R'
            else:
                args.language = EXT2LANG[os.path.splitext(args.source[0])[-1]]
        drv = import_component('model', args.language)
        kws = {'toolname': args.toolname, 'flags': args.flags,
               'use_ccache': args.use_ccache,
               'disable_python_c_api': args.disable_python_c_api,
               'with_asan': args.with_asan}
        if (args.language in ['r', 'R']) and args.Rpkg_language:
            kws['language'] = args.Rpkg_language
        print("executable: %s" % drv.call_compiler(args.source, **kws))


class yggcompile(SubCommand):
    r"""Compile interface library/libraries."""

    name = "compile"
    help = ("Compile yggdrasil dependency libraries. Existing "
            "libraries are first deleted.")
    arguments = [
        (('language', ),
         {'nargs': '*', 'default': ['all'],
          # 'choices': (['all'] + LANGUAGES_WITH_ALIASES.get('compiled', [])
          #             + LANGUAGES_WITH_ALIASES.get('compiled_dsl', [])),
          'help': ("One or more languages to compile dependencies "
                   "for, source files to compile into an executable, "
                   "or the directory containing an R package.")}),
        (('--toolname', ),
         {'help': "Name of compilation tool that should be used"}),
        (('--disable-python-c-api', ),
         {'action': 'store_true',
          'help': 'Disable access to the Python C API from yggdrasil.'}),
        (('--with-asan', ),
         {'action': 'store_true',
          'help': "Compile with Clang ASAN if available."}),
        (('--force-source', ),
         {'action': 'store_true',
          'help': ("Force all arguments passed to the language parameter "
                   "to be treated as source files to be compiled.")}),
        (('--source-language', ),
         {'default': None,
          # 'choices': [None] + LANGUAGES_WITH_ALIASES['all'],
          'help': ("Language of the source code. If not provided, "
                   "the language will be determined from the "
                   "source extension.")}),
        (('--flags', ),
         {'nargs': '*',
          'help': ("Additional flags that should be added to the "
                   "compilation command if source files are provided.")}),
        (('--use-ccache', ),
         {'action': 'store_true',
          'help': "Run source compilation with ccache."}),
        (('--Rpkg-language', ),
         {'help': ("Language that R package is written in "
                   "(only used if the provided source language is R).")})]

    @classmethod
    def func(cls, args):
        from yggdrasil.components import import_component
        error_on_missing = (not getattr(args, 'all_languages', False))
        missing = []
        languages = []
        sources = []
        for x in args.language:
            if ((x in LANGUAGES_WITH_ALIASES['all']
                 and not args.force_source)):
                languages.append(x)
            else:
                sources.append(x)
        if languages:
            args.languages = languages
            yggclean.func(args, verbose=False)
        for lang in list(languages):
            drv = import_component('model', lang)
            drv.cleanup_dependencies(
                disable_python_c_api=args.disable_python_c_api,
                with_asan=args.with_asan)
            # Prevent language from being recompiled more than
            # once as a dependency
            for base_lang in drv.base_languages:
                if base_lang in languages:
                    languages.remove(base_lang)
        kwargs = {'toolname': args.toolname,
                  'disable_python_c_api': args.disable_python_c_api,
                  'with_asan': args.with_asan}
        for lang in languages:
            drv = import_component('model', lang)
            if ((hasattr(drv, 'compile_dependencies')
                 and (not getattr(drv, 'is_build_tool', False)))):
                if drv.is_installed():
                    drv.compile_dependencies(**kwargs)
                else:
                    missing.append(lang)
        if error_on_missing and missing:  # pragma: debug
            raise Exception(f"One or more of the requested languages "
                            f"are not fully installed for use with "
                            f"yggdrasil: {missing}")
        if sources:
            kwargs.update(
                use_ccache=args.use_ccache,
                flags=args.flags)
            if args.source_language is None:
                if ((len(sources) == 1 and os.path.isdir(sources[0])
                     and os.path.isdir(os.path.join(sources[0], 'R')))):
                    args.source_language = 'R'
                else:
                    args.source_language = constants.EXT2LANG[
                        os.path.splitext(sources[0])]
            drv = import_component('model', args.source_language)
            if (args.source_language in ['r', 'R']) and args.Rpkg_language:
                kwargs['language'] = args.Rpkg_language
            print(f"executable: {drv.call_compiler(sources, **kwargs)}")
            

class yggclean(SubCommand):
    r"""Cleanup dependency files."""

    name = "clean"
    help = "Remove dependency libraries compiled by yggdrasil."
    arguments = [
        (('language', ),
         {'nargs': '*', 'default': ['all'],
          # 'choices': ['all'] + LANGUAGES_WITH_ALIASES.get('all', []),
          'help': ("One or more languages to clean up dependencies "
                   "for.")})]

    @classmethod
    def func(cls, args, verbose=True):
        from yggdrasil.components import import_component
        for lang in args.language:
            if lang in ['ipc', 'ipcs']:
                from yggdrasil.communication.IPCComm import ipcrm_queues
                ipcrm_queues()
                ipcrm_queues(by_id=True)
            else:
                import_component('model', lang).cleanup_dependencies(
                    verbose=verbose)


class cc_toolname(SubCommand):
    r"""Output the name of the compiler used to compile C or C++ programs."""

    name = "compiler-tool"
    help = 'Get the compiler used for C/C++ programs.'
    arguments = [
        (('--cpp', ),
         {'action': 'store_true',
          'help': 'Get the compiler used for C++ programs.'}),
        (('--fullpath', ),
         {'action': 'store_true',
          'help': 'Get the full path to the tool exectuable.'})]

    @classmethod
    def parse_args(cls, *args, **kwargs):
        args = super(cc_toolname, cls).parse_args(*args, **kwargs)
        args.tool = 'compiler'
        args.toolname = None
        args.flags = False
        if args.cpp:
            args.language = 'cpp'
        else:
            args.language = 'c'
        return args

    @classmethod
    def func(cls, args, **kwargs):
        ygginfo.func(args, **kwargs)


class ld_toolname(cc_toolname):
    r"""Output the name of the linker used to compile C or C++ programs."""

    name = "linker-tool"
    help = 'Get the linker used for C/C++ programs.'
    arguments = [
        (('--cpp', ),
         {'action': 'store_true',
          'help': 'Get the linker used for C++ programs.'}),
        (('--fullpath', ),
         {'action': 'store_true',
          'help': 'Get the full path to the tool exectuable.'})]

    @classmethod
    def parse_args(cls, *args, **kwargs):
        args = super(ld_toolname, cls).parse_args(*args, **kwargs)
        args.tool = 'linker'
        return args


class cc_flags(cc_toolname):
    r"""Get the compiler flags necessary for including the interface
    library in a C or C++ program."""

    name = "compiler-flags"
    help = 'Get the compilation flags necessary for a C/C++ program.'
    arguments = [
        (('--cpp', ),
         {'action': 'store_true',
          'help': 'Get the compilation flags used for C++ programs.'}),
        (('--toolname', ),
         {'default': None,
          'help': 'Name of the tool that associated flags be returned for.'}),
        (('--disable-python-c-api', ),
         {'action': 'store_true',
          'help': 'Disable access to the Python C API from yggdrasil.'}),
        (('--with-asan', ),
         {'action': 'store_true',
          'help': "Compile with Clang ASAN if available."}),
    ]

    @classmethod
    def parse_args(cls, *args, **kwargs):
        args = super(cc_flags, cls).parse_args(*args, **kwargs)
        args.flags = True
        return args


class ld_flags(cc_toolname):
    r"""Get the linker flags necessary for including the interface
    library in a C or C++ program."""

    name = "linker-flags"
    help = 'Get the compilation flags necessary for a C/C++ program.'
    arguments = [
        (('--cpp', ),
         {'action': 'store_true',
          'help': 'Get the compilation flags used for C++ programs.'}),
        (('--toolname', ),
         {'default': None,
          'help': 'Name of the tool that associated flags be returned for.'}),
        (('--disable-python-c-api', ),
         {'action': 'store_true',
          'help': 'Disable access to the Python C API from yggdrasil.'}),
        (('--with-asan', ),
         {'action': 'store_true',
          'help': "Compile with Clang ASAN if available."}),
    ]

    @classmethod
    def parse_args(cls, *args, **kwargs):
        args = super(ld_flags, cls).parse_args(*args, **kwargs)
        args.tool = 'linker'
        args.flags = True
        return args


class ygginstall(SubCommand):
    r"""Call installation script."""

    name = "install"
    help = "Complete yggdrasil installation for one or more languages."
    arguments = (
        [(('languages', ),
          {'nargs': '*',
           # 'choices': ['all'] + LANGUAGES_WITH_ALIASES.get('all', []),
           'default': [],
           'help': 'One or more languages that should be installed.'}),
         (('--no-import', ),
          {'action': 'store_true',
           'help': ('Don\'t import the yggdrasil package in '
                    'calling the installation script.')}),
         (('--with-asan', ),
          {'action': 'store_true',
           'help': "Load ASAN library before running executables."}),
         ]
    )

    @classmethod
    def add_arguments(cls, parser, **kwargs):
        from yggdrasil.languages import install_languages
        super(ygginstall, cls).add_arguments(parser, **kwargs)
        install_languages.update_argparser(parser=parser)

    @classmethod
    def func(cls, args):
        from yggdrasil.languages import install_languages
        from yggdrasil import config
        languages = args.languages
        if (((isinstance(languages, str) and (languages == 'all'))
             or (isinstance(languages, list) and ('all' in languages)))):
            languages = [x.lower() for x in
                         install_languages.get_language_directories()]
        if args.with_asan:
            assert not args.no_import
            from yggdrasil.drivers.CModelDriver import CModelDriver
            CModelDriver.set_asan_env(os.environ)
        for x in languages:
            install_languages.install_language(x, args=args)
        if not os.path.isfile(config.usr_config_file):
            config.update_language_config(verbose=True)


class update_config(SubCommand):
    r"""Update the user config file for yggdrasil."""

    name = "config"
    help = 'Update the user config file.'
    arguments = (
        [(('languages', ),
          {'nargs': '*',
           # 'choices': ['all'] + LANGUAGES_WITH_ALIASES.get('all', []),
           'default': ['all'],
           'help': 'One or more languages that should be configured.'}),
         (('--languages', ),
          {'nargs': '+', 'dest': 'languages_flag',
           # 'choices': ['all'] + LANGUAGES_WITH_ALIASES.get('all', []),
           'default': ['all'],
           'help': 'One or more languages that should be configured.'}),
         (('--show-file', ),
          {'action': 'store_true',
           'help': 'Print the path to the config file without updating it.'}),
         (('--remove-file', ),
          {'action': 'store_true',
           'help': 'Remove the existing config file and return.'}),
         (('--overwrite', ),
          {'action': 'store_true',
           'help': 'Overwrite the existing file.'}),
         (('--disable-languages', ),
          {'nargs': '+', 'default': [],
           'choices': LANGUAGES_WITH_ALIASES.get('all', []),
           'help': 'One or more languages that should be disabled.'}),
         (('--enable-languages', ),
          {'nargs': '+', 'default': [],
           'choices': LANGUAGES_WITH_ALIASES.get('all', []),
           'help': 'One or more languages that should be enabled.'}),
         (('--quiet', '-q'),
          {'action': 'store_true',
           'help': 'Suppress output.'}),
         (('--allow-multiple-omp', ),
          {'action': 'store_true', 'default': None,
           'help': ('Have yggdrasil set the environment variable '
                    'KMP_DUPLICATE_LIB_OK to \'True\' during model runs '
                    'to disable errors resembling '
                    '"OMP: Error #15: Initializing libomp.dylib..." '
                    'that result from having multiple versions of OpenMP '
                    'loaded during runtime.')}),
         (('--dont-allow-multiple-omp', ),
          {'action': 'store_true', 'default': None,
           'help': ('Don\'t set the KMP_DUPLICATE_LIB_OK environment variable '
                    'when running models (see help for \'--allow-multiple-omp\' '
                    'for more information).')})]
        + [(('--%s-compiler' % k, ),
            {'help': ('Name or path to compiler that should be used to compile '
                      'models written in %s.' % k)})
           for k in LANGUAGES.get('compiled', [])]
        + [(('--%s-linker' % k, ),
            {'help': ('Name or path to linker that should be used to link '
                      'models written in %s.' % k)})
           for k in LANGUAGES.get('compiled', [])]
        + [(('--%s-archiver' % k, ),
            {'help': ('Name or path to archiver that should be used to create '
                      'static libraries for models written in %s.' % k)})
           for k in LANGUAGES.get('compiled', [])]
    )
    # TODO: Move these into the language directories?
    language_arguments = {
        'c': [
            ConditionalArgumentTuple(
                ('--vcpkg-dir', ),
                {'help': 'Directory containing the vcpkg installation.'},
                conditions={'os': ['Windows']}),
            ConditionalArgumentTuple(
                ('--macos-sdkroot', '--sdkroot'),
                {'help': ('The full path to the MacOS SDK that '
                          'should be used.')},
                conditions={'os': ['MacOS']})],
        'matlab': [
            (('--disable-matlab-engine-for-python', ),
             {'action': 'store_true', 'default': None,
              'dest': 'disable_engine',
              'help': 'Disable use of the Matlab engine for Python.'}),
            (('--enable-matlab-engine-for-python', ),
             {'action': 'store_true', 'default': None,
              'dest': 'enable_engine',
              'help': 'Enable use of the Matlab engine for Python.'}),
            (('--hide-matlab-libiomp', ),
             {'action': 'store_true', 'default': None,
              'help': ('Hide the version of libiomp installed by Matlab '
                       'by slightly changing the filename so that the '
                       'conda version of libomp is used instead. This '
                       'helps to solve the error "'
                       'OMP: Error #15: Initializing libomp.dylib..." '
                       'that can occur when using a conda environment. '
                       'The hidden file location will be set in the '
                       'configuration file and can be restored via the '
                       '\'--restore-matlab-libiomp\' option.')}),
            (('--restore-matlab-libiomp', ),
             {'action': 'store_true', 'default': None,
              'help': ('Restore the version of libiomp installed by Matlab. '
                       '(See help for \'--hide-matlab-libiomp\')')}),
        ],
        'osr': [
            (('--osr-repository-path', ),
             {'dest': 'repository',
              'help': 'The full path to the OpenSimRoot repository.'})]}
    opposite_arguments = [
        ('allow_multiple_omp', 'dont_allow_multiple_omp'),
        ('disable_engine', 'enable_engine'),
        ('hide_matlab_libiomp', 'restore_matlab_libiomp')]
        
    @classmethod
    def add_arguments(cls, parser, **kwargs):
        super(update_config, cls).add_arguments(parser, **kwargs)
        args = kwargs.get('args', None)
        if args is None:
            args = sys.argv[1:]
        if ('-h' in args) or ('--help' in args):
            args = [x for x in args if x not in ['-h', '--help']]
        preargs = parser.parse_known_args(args=args)[0]
        prelang = preargs.languages
        if preargs.languages_flag:
            prelang += preargs.languages_flag
        if (len(prelang) == 0) or ('all' in prelang):
            prelang = LANGUAGES.get('all', [])
        # TODO: The languages could be subparsers
        for k, v in cls.language_arguments.items():
            if k in prelang:
                cls.add_argument_to_parser(parser, v)

    @classmethod
    def func(cls, args):
        from yggdrasil import config
        if args.show_file:
            print('Config file located here: %s'
                  % config.usr_config_file)
        if args.remove_file and os.path.isfile(config.usr_config_file):
            os.remove(config.usr_config_file)
        if args.show_file or args.remove_file:
            return
        for x_true, x_false in cls.opposite_arguments:
            if getattr(args, x_false, None) is not None:
                assert getattr(args, x_true, None) is None
                setattr(args, x_true, not getattr(args, x_false))
            if hasattr(args, x_false):
                delattr(args, x_false)
        lang_kwargs = {}
        for k, v in cls.language_arguments.items():
            for v_args in v:
                name = v_args[1].get(
                    'dest',
                    v_args[0][0].lstrip('-').replace('-', '_'))
                if getattr(args, name, None) is not None:
                    lang_kwargs.setdefault(k, {})
                    lang_kwargs[k][name] = getattr(args, name)
        for x in ['compiler', 'linker', 'archiver']:
            for k in LANGUAGES.get('compiled', []):
                if getattr(args, '%s_%s' % (k, x), None):
                    lang_kwargs.setdefault(k, {})
                    lang_kwargs[k][x] = getattr(args, '%s_%s' % (k, x))
        config.update_language_config(
            args.languages, overwrite=args.overwrite,
            verbose=(not args.quiet),
            disable_languages=args.disable_languages,
            enable_languages=args.enable_languages,
            allow_multiple_omp=args.allow_multiple_omp,
            lang_kwargs=lang_kwargs)


class regen_schema(SubCommand):
    r"""Regenerate the yggdrasil schema."""

    name = "schema"
    help = "Regenerate the yggdrasil schema."
    arguments = [
        (('--only-constants', ),
         {'action': 'store_true',
          'help': ('Only update the constants.py file without updating '
                   'the schema.')}),
        (('--filename', ),
         {'type': str,
          'help': 'Name where schema should be saved.'})]

    @classmethod
    def func(cls, args):
        from yggdrasil import schema
        if not args.only_constants:
            if args.filename is None:
                args.filename = schema._schema_fname
            if os.path.isfile(args.filename):
                os.remove(args.filename)
            schema.clear_schema()
            schema.init_schema(fname=args.filename)
        else:
            schema.update_constants()


class yggmodelform(SubCommand):
    r"""Save/print a JSON schema that can be used for generating a
    form for composing a model specification files."""

    name = "model-form-schema"
    help = ('Save/print the JSON schema for generating the model '
            'specification form.')
    arguments = [
        (('--file', ),
         {'help': 'Path to file where the schema should be saved.'})]

    @classmethod
    def func(cls, args):
        from yggdrasil.schema import get_model_form_schema
        out = get_model_form_schema(fname_dst=args.file, indent='    ')
        if not args.file:
            pprint.pprint(out)


class yggdevup(SubCommand):
    r"""Cleanup old libraries, re-install languages, and re-compile
    interface libraries following an update to the code (when doing
    development)."""

    name = "dev-update"
    help = ('Perform cleanup and reinitialization following an '
            'update to the code during development.')

    @classmethod
    def func(cls, args):
        yggclean(args=['all'])
        ygginstall(args=['all'])
        yggcompile(args=['all'])
        ygginfo(args=[])


class timing_plots(SubCommand):
    r"""Create performance plots using timing results."""

    name = "timing"
    help = "Create performance plots using timing results."
    arguments = [
        ArgumentSubparser(
            title='comparison', dest='comparison',
            description='Comparison plot that should be created.',
            parsers=[
                ArgumentParser(
                    name='commtype',
                    help='Compare different communication avenues.'),
                ArgumentParser(
                    name='language',
                    help='Compare different programming languages.'),
                ArgumentParser(
                    name='os',
                    help='Compare different operating systems.'),
                ArgumentParser(
                    name='python',
                    help='Compare different versions of Python.'),
                ArgumentParser(
                    name='lang2019',
                    help='Create plots from Lang (2019) paper.')])]

    @classmethod
    def func(cls, args):
        from yggdrasil import timing
        if args.comparison == 'lang2019':
            _lang_list = timing._lang_list
            _lang_list_nomatlab = copy.deepcopy(_lang_list)
            _lang_list_nomatlab.remove('matlab')
            timing.plot_scalings(compare='platform', python_ver='2.7')
            # All plots on Linux, no matlab
            timing.plot_scalings(compare='comm_type',
                                 platform='Linux',
                                 python_ver='2.7')
            timing.plot_scalings(compare='python_ver',
                                 platform='Linux')
            timing.plot_scalings(compare='language',
                                 platform='Linux',
                                 python_ver='2.7',
                                 compare_values=_lang_list_nomatlab)
            # Language comparision on MacOS, with matlab
            timing.plot_scalings(compare='language',
                                 platform='MacOS',
                                 python_ver='2.7',
                                 compare_values=_lang_list)
        else:
            if args.comparison == 'commtype':
                args.comparison = 'comm_type'
            elif args.comparison == 'os':
                args.comparison = 'platform'
            timing.plot_scalings(compare=args.comparison)


class coveragerc(SubCommand):
    r"""Create a .coveragerc file."""

    name = "coveragerc"
    help = (
        "Generate a coveragerc file that covers/ignores lines based on "
        "installed languages or options.")
    arguments = [
        (('--method', ),
         {'choices': ['installed', 'env', None],
          'default': None,
          'help': ("Method that should be used to select languages that "
                   "should be covered. 'env' covers languages based on "
                   "the value of environment variables of the form "
                   "'INSTALL{language}'. 'installed' covers languages "
                   "that yggdrasil considers installed.")}),
        (('--cover-languages', '--cover-language', '--cover'),
         {'nargs': '*',
          'choices': LANGUAGES.get('all', []),
          'help': "Language(s) to cover."}),
        (('--dont-cover-languages', '--dont-cover-language',
          '--dont-cover'),
         {'nargs': '*',
          'choices': LANGUAGES.get('all', []),
          'help': "Language(s) to ignore in coverage."}),
        (('--filename', ),
         {'type': str, 'default': None,
          'help': "File to save coveragerc to"}),
        (('--setup-cfg', ),
         {'type': str, 'default': None,
          'help': "setup.cfg file containing coverage options"}),
    ]

    @classmethod
    def func(cls, args):
        from yggdrasil.tools import is_lang_installed
        from yggdrasil.config import create_coveragerc
        covered_languages = {}
        if args.method == 'env':
            for k in LANGUAGES['all']:
                v = os.environ.get(f"INSTALL{k.upper()}", None)
                if v is not None:
                    covered_languages[k] = (v == '1')
        elif args.method == 'installed':
            for k in LANGUAGES['all']:
                covered_languages[k] = is_lang_installed(k)
        if args.cover_languages:
            for k in args.cover_languages:
                covered_languages[k] = True
        if args.dont_cover_languages:
            for k in args.dont_cover_languages:
                covered_languages[k] = False
        for k in LANGUAGES['all']:
            covered_languages.setdefault(k, True)
        create_coveragerc(covered_languages, filename=args.filename,
                          setup_cfg=args.setup_cfg)


class file_converter(SubCommand):
    r"""Convert between compatible file types."""

    name = "fconvert"
    help = (
        "Convert a file of one type into another compatible type.")
    arguments = [
        (('src', ),
         {'help': "Name of file to convert"}),
        (('dst', ),
         {'help': "Name of destination file"}),
        (('--from', '--src-type'),
         {'dest': 'src_type',
          'default': None,
          'help': "Source file type"}),
        (('--to', '--dst-type'),
         {'dest': 'dst_type',
          'default': None,
          'help': "Destination file type"}),
        (('--src-kwargs', ),
         {'dest': 'src_kwargs',
          'type': str,
          'help': ("Keyword arguments for source file communicator "
                   "in JSON format")}),
        (('--dst-kwargs', ),
         {'dest': 'dst_kwargs',
          'type': str,
          'help': ("Keyword arguments for destination file communicator "
                   "in JSON format")}),
        (('--transform', ),
         {'type': str,
          'help': ("Transform keyword arguments for transforming "
                   "messages between source and destination in JSON "
                   "format")}),
    ]

    @classmethod
    def runtime_arguments(cls):
        return [
            (('--from', '--src-type'),
             {'choices': [None] + list(constants.COMPONENT_REGISTRY[
                 'file']['subtypes'].keys())}),
            (('--to', '--dst-type'),
             {'choices': [None] + list(constants.COMPONENT_REGISTRY[
                 'file']['subtypes'].keys())}),
        ]
    
    @classmethod
    def func(cls, args):
        from yggdrasil.communication.FileComm import convert_file
        from yggdrasil import rapidjson
        if args.src_kwargs is not None:
            args.src_kwargs = rapidjson.loads(args.src_kwargs)
        if args.dst_kwargs is not None:
            args.dst_kwargs = rapidjson.loads(args.dst_kwargs)
        if args.transform is not None:
            args.transform = rapidjson.loads(args.transform)
        convert_file(args.src, args.dst,
                     src_type=args.src_type, src_kwargs=args.src_kwargs,
                     dst_type=args.dst_type, dst_kwargs=args.dst_kwargs,
                     transform=args.transform)


class generate_gha_workflow(SubCommand):
    r"""Re-generate the Github actions workflow yaml."""

    name = "gha"
    help = (
        "Generate a Github Actions (GHA) workflow yaml file from "
        "a version of the file that uses anchors (not supported by "
        "GHA as of 2021-01-14).")
    arguments = [
        (('--base', '--base-file'),
         {'help': (
             "Version of GHA workflow yaml that contains anchors.")}),
        (('--dest', ),
         {'help': (
             "Name of target GHA workflow yaml file.")}),
        (('--verbose', ),
         {'action': 'store_true', 'help': "Print yaml contents."})]

    @classmethod
    def func(cls, args, gitdir=None):
        import yaml
        from yggdrasil.serialize.YAMLSerialize import decode_yaml, encode_yaml
        from collections import OrderedDict

        class NoAliasDumper(yaml.SafeDumper):
            def ignore_aliases(self, data):
                return True
        if (args.base is None or args.dest is None) and (gitdir is None):
            try:
                gitdir = subprocess.check_output(
                    ["git", "rev-parse", "--git-dir"],
                    stderr=subprocess.PIPE).decode('utf-8').strip()
            except subprocess.CalledProcessError:
                return 1
        if args.base is None:
            args.base = os.path.join(gitdir, '..', 'utils',
                                     'test-install-base.yml')
        if args.dest is None:
            args.dest = os.path.join(gitdir, '..', '.github', 'workflows',
                                     'test-install.yml')
        with open(args.base, 'r') as fd:
            contents = decode_yaml(fd.read(), sorted_dict_type=OrderedDict)
            # contents = yaml.load(fd, Loader=yaml.SafeLoader)
        if args.verbose:
            pprint.pprint(contents)
        with open(args.dest, 'w') as fd:
            fd.write(('# DO NOT MODIFY THIS FILE, IT IS GENERATED.\n'
                      '# To make changes, modify \'%s\'\n'
                      '# and run \'ygggha\'\n')
                     % args.base)
            fd.write(encode_yaml(contents, sorted_dict_type=OrderedDict,
                                 Dumper=NoAliasDumper))
            # yaml.dump(contents, fd, Dumper=NoAliasDumper)


def rebuild_c_api():
    r"""Rebuild the C/C++ API."""
    ReplacementWarning('yggbuildapi_c', 'yggdrasil compile-deps c cpp')
    yggcompile(args=['c', 'cpp'] + sys.argv[1:])


def yggtime_comm():
    r"""Plot timing statistics comparing the different communication mechanisms."""
    ReplacementWarning('yggtime_comm', 'yggdrasil timing commtype')
    timing_plots(args=['commtype'] + sys.argv[1:])


def yggtime_lang():
    r"""Plot timing statistics comparing the different languages."""
    ReplacementWarning('yggtime_lang', 'yggdrasil timing language')
    timing_plots(args=['language'] + sys.argv[1:])


def yggtime_os():
    r"""Plot timing statistics comparing the different operating systems."""
    ReplacementWarning('yggtime_os', 'yggdrasil timing os')
    timing_plots(args=['os'] + sys.argv[1:])


def yggtime_py():
    r"""Plot timing statistics comparing the different versions of Python."""
    ReplacementWarning('yggtime_py', 'yggdrasil timing python')
    timing_plots(args=['python'] + sys.argv[1:])


def yggtime_paper():
    r"""Create plots for timing."""
    ReplacementWarning('yggtime_paper', 'yggdrasil timing lang2019')
    timing_plots(args=['lang2019'] + sys.argv[1:])


class main(SubCommand):
    r"""Runner for yggdrasil CLI."""

    name = "yggdrasil"
    help = (
        "Command line interface for the yggdrasil package.")
    arguments = []
    subcommands = [yggrun, ygginfo, validate_yaml,
                   yggcc, yggcompile, yggclean,
                   ygginstall, update_config, regen_schema,
                   yggmodelform, yggdevup,
                   timing_plots, generate_gha_workflow,
                   integration_service_manager, coveragerc,
                   file_converter]

    @classmethod
    def get_parser(cls, **kwargs):
        from yggdrasil import __version__ as ver
        parser = super(main, cls).get_parser(**kwargs)
        parser.add_argument('--version', action='version',
                            version=('yggdrasil %s' % ver))
        subparsers = parser.add_subparsers(title='subcommands',
                                           dest='subcommand')
        parser._ygg_subparsers = {}
        for x in cls.subcommands:
            x.add_subparser(subparsers, args=kwargs.get('args', None))
            parser._ygg_subparsers[x.name] = x
        return parser

    @classmethod
    def parse_args(cls, parser, args=None, **kwargs):
        if args is None:
            args = sys.argv[1:]
        if isinstance(args, list) and ('test' in args):
            kwargs['allow_unknown'] = True
        args = super(main, cls).parse_args(parser, args=args, **kwargs)
        if args.subcommand:
            args = parser._ygg_subparsers[args.subcommand].parse_args(
                parser, args=args, **kwargs)
        return args

    @classmethod
    def func(cls, args):
        args.func(args)


if __name__ == '__main__':
    yggrun()
    sys.exit(0)
