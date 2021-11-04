import os
import git
import copy
import shutil
import subprocess
import tempfile
import logging
import chevron
import io as sio
import warnings
import xml.etree.ElementTree as ET
from yggdrasil import tools, platform
from yggdrasil.components import import_component
from yggdrasil.drivers.ExecutableModelDriver import ExecutableModelDriver
from yggdrasil.drivers.CPPModelDriver import CPPModelDriver


logger = logging.getLogger(__name__)


class OSRModelDriver(ExecutableModelDriver):
    r"""Class for running OpenSimRoot model.

    Args:
        sync_vars_in (list, optional): Variables that should be synchronized
            from other models. Defaults to [].
        sync_vars_out (list, optional): Variables that should be synchronized
            to other models. Defaults to [].
        copy_xml_to_osr (bool, optional): If True, the XML file(s) will
            be copied to the OSR repository InputFiles direcitory before
            running. This is necessary if the XML file(s) use any of the
            files located there since OSR always assumes the included
            file paths are relative. Defaults to False.
        update_interval (float, optional): Max simulation interval at which
            synchronization should occur (in days). Defaults to 1.0 if not
            provided. If the XML input file loads additional export modules
            that output at a shorter rate, the existing table of values will
            be extrapolated.

    """
    _schema_subtype_description = 'Model is an OSR model.'
    _schema_properties = {
        'sync_vars_in': {'type': 'array', 'items': {'type': 'string'},
                         'default': []},
        'sync_vars_out': {'type': 'array', 'items': {'type': 'string'},
                          'default': []},
        'copy_xml_to_osr': {'type': 'boolean', 'default': False},
        'update_interval': {'type': 'object',
                            'additionalProperties': {'type': 'float'},
                            'default': {'timesync': 1.0}}}
    executable_type = 'dsl'
    language = 'osr'
    language_ext = '.xml'
    base_languages = ['cpp']
    interface_dependencies = ['make']
    repository = None
    executable_path = None
    repository_url = "https://gitlab.com/langmm/OpenSimRoot.git"
    repository_branch = "volatile_active"
    _config_keys = ['repository']
    _config_attr_map = [{'attr': 'repository',
                         'key': 'repository'}]

    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration.
        """
        ExecutableModelDriver.after_registration(cls, **kwargs)
        if cls.repository is not None:
            if platform._is_win:  # pragma: windows
                cls.executable_path = os.path.join(
                    cls.repository, 'OpenSimRoot',
                    'StaticBuild_win64', 'OpenSimRootYgg') + '.exe'
            else:
                cls.executable_path = os.path.join(
                    cls.repository, 'OpenSimRoot',
                    'StaticBuild', 'OpenSimRootYgg')
        
    def parse_arguments(self, *args, **kwargs):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            *args: Additional arguments are passed to the parent class's method.
            **kwargs: Additional keyword arguments are passed to the parent
                class's method.

        """
        super(OSRModelDriver, self).parse_arguments(*args, **kwargs)
        self.model_file_orig = self.model_file
        self.model_file = '_copy'.join(os.path.splitext(self.model_file_orig))
        if self.copy_xml_to_osr and (self.repository is not None):
            self.model_file = os.path.join(
                self.repository, 'OpenSimRoot', 'InputFiles',
                os.path.basename(self.model_file))
        # if not (isinstance(self.executable_path, str)
        #         and os.path.isfile(self.executable_path)):
        self.compile_dependencies()
        assert(os.path.isfile(self.executable_path))

    @classmethod
    def is_library_installed(cls, lib, **kwargs):
        r"""Determine if a dependency is installed.

        Args:
            lib (str): Name of the library that should be checked.
            **kwargs: Additional keyword arguments are ignored.

        Returns:
            bool: True if the library is installed, False otherwise.

        """
        # Need to treat gnu make as dependency since OSR Makefile is not
        # compatible with nmake
        if lib == 'make':
            return bool(shutil.which('make'))
        return super(OSRModelDriver, cls).is_library_installed(
            lib, **kwargs)  # pragma: debug

    @classmethod
    def compile_dependencies(cls, target='OpenSimRootYgg', toolname=None):
        r"""Compile the OpenSimRoot executable with the yggdrasil flag set.

        Args:
            target (str, optional): Make target that should be build. Defaults to
                'OpenSimRootYgg' (the yggdrasil-instrumented version of the
                OSR executable).
            toolname (str, optional): C++ compiler that should be used. Forced
                to be 'cl.exe' on windows. Otherwise the default C++ compiler will
                be used.

        """
        if (cls.repository is not None) and CPPModelDriver.is_installed():
            if not os.path.isdir(cls.repository):  # pragma: debug
                # This will only need to be called if the tempdir was cleaned up
                cls.clone_repository(cls.repository)
            # toolname = CPPModelDriver.get_tool('compiler',
            #                                    return_prop='name',
            #                                    default=None)
            cwd = os.path.join(cls.repository, 'OpenSimRoot')
            flags = ['-j4']
            env = copy.deepcopy(os.environ)
            if platform._is_win:  # pragma: windows
                toolname = 'cl'
                env['YGG_OSR_TOOL'] = toolname
                if toolname == 'cl':
                    cl_path = shutil.which(toolname + '.exe')
                    if cl_path:
                        msvc_bin = os.path.dirname(cl_path)
                        env['YGG_OSR_CXX'] = cl_path
                        env['YGG_OSR_LINK'] = os.path.join(msvc_bin, 'link.exe')
                        for k in ['CL', '_CL_']:
                            v = os.environ.get(k, None)
                            if v is not None:  # pragma: appveyor
                                env[k] = v.replace('/', '-').replace('\\', '/')
                    else:  # pragma: debug
                        env.pop('YGG_OSR_TOOL')
                        warnings.warn(
                            "The MSVC compiler is not installed. Be aware "
                            "that the GNU compiler takes a *very* long time "
                            "to compile OpenSimRoot against yggdrasil on "
                            "Windows (> 1 hr).")
                cwd = os.path.join(cwd, 'StaticBuild_win64')
            else:
                cwd = os.path.join(cwd, 'StaticBuild')
            if target != 'cleanygg':
                for x in cls.base_languages:
                    base_cls = import_component('model', x)
                    base_cls.compile_dependencies(toolname=toolname)
            elif not os.path.isfile(cls.executable_path):
                return
            cmd = ['make', target] + flags
            subprocess.check_call(cmd, cwd=cwd, env=env)

    def write_wrappers(self, **kwargs):
        r"""Write any wrappers needed to compile and/or run a model.

        Args:
            **kwargs: Keyword arguments are passed to the parent class's
                method.

        Returns:
            list: Full paths to any created wrappers.

        """
        out = super(OSRModelDriver, self).write_wrappers(**kwargs)
        out.append(self.wrap_xml(self.model_file_orig, self.model_file))
        return out

    def wrap_xml(self, src, dst):
        r"""Wrap the input XML, adding tags for the inputs/outputs specified for
        this model.

        Args:
            src (str): Full path to the XML file that should be wrapped.
            dst (str): Full path to the location where the updated XML should
                be saved.

        Returns:
            str: Full path to XML file produced.

        """
        with open(src, 'r') as fd:
            src_contents = fd.read()
        src_contents = chevron.render(
            sio.StringIO(src_contents).getvalue(), self.set_env())
        root = ET.fromstring(src_contents)
        timesync = self.timesync
        assert(timesync)
        if not isinstance(timesync, list):
            timesync = [timesync]
        for tsync in reversed(timesync):
            ivars = tsync.get('inputs', [])
            ovars = tsync.get('outputs', [])
            assert(isinstance(ivars, list))
            assert(isinstance(ovars, list))
            ivars = ' '.join(ivars)
            ovars = ' '.join(ovars)
            tupdate = self.update_interval.get(tsync['name'], 1.0)
            cask = ET.Element('SimulaCask',
                              attrib={'name': tsync['name'],
                                      'interval': str(tupdate)})
            if ivars:
                icask = ET.Element('SimulaCaskInputs')
                icask.text = ivars
                cask.insert(-1, icask)
            if ovars:
                ocask = ET.Element('SimulaCaskOutputs')
                ocask.text = ovars
                cask.insert(-1, ocask)
            probe = ET.Element("SimulaBase", name="probeCaskObjects")
            probe_vals = [ET.Element("SimulaConstant",
                                     name="run", type="bool"),
                          ET.Element("SimulaConstant",
                                     name="timeInterval", type="time"),
                          ET.Element("SimulaConstant",
                                     name="requestedVariables",
                                     type="string")]
            probe_vals[0].text = '1'
            probe_vals[1].text = str(tupdate)
            probe_vals[2].text = ', '.join(ivars.split())
            probe.extend(probe_vals)
            probe_directive = ET.Element(
                'SimulaDirective',
                attrib={'path': "/simulationControls/outputParameters"})
            probe_directive.append(probe)
            root.extend([cask, probe_directive])
        tree = ET.ElementTree(root)
        tree.write(dst)
        return dst

    @classmethod
    def is_language_installed(cls):
        r"""Determine if the interpreter/compiler for the associated programming
        language is installed.

        Returns:
            bool: True if the language interpreter/compiler is installed.

        """
        return (cls.repository is not None)

    @classmethod
    def clone_repository(cls, dest=None):
        r"""Clone the OpenSimRoot repository.

        Args:
            dest (str, optional): Full path to location where the repository should
                be cloned. Defaults to '$TEMP/OpenSimRoot'.

        Returns:
            str: Full path to location where the repository was cloned.

        """
        if dest is None:
            dest = os.path.join(tempfile.gettempdir(), 'OpenSimRoot')
        if not os.path.isdir(dest):  # pragma: config
            repo = git.Repo.clone_from(cls.repository_url, dest,
                                       branch=cls.repository_branch)
            repo.close()
        return dest
        
    @classmethod
    def configure_executable_type(cls, cfg):
        r"""Add configuration options specific in the executable type
        before the libraries are configured.

        Args:
            cfg (CisConfigParser): Config class that options should be set for.
        
        Returns:
            list: Section, option, description tuples for options that could not
                be set.

        """
        # TODO: Move clone + compile to install
        out = super(OSRModelDriver, cls).configure_executable_type(cfg)
        opt = 'repository'
        desc = 'The full path to the OpenSimRoot repository.'
        # if platform._is_win:  # pragma: windows
        #     out.append((cls.language, opt, desc))
        #     return out
        if (((not cfg.has_option(cls.language, opt))
             or (not os.path.isdir(cfg.get(cls.language, opt))))):
            fname = 'OpenSimRoot'
            fpath = tools.locate_file(fname)
            if not fpath:
                logger.info('Could not locate %s, attempting to clone' % fname)
                try:
                    fpath = cls.clone_repository()
                except BaseException as e:  # pragma: debug
                    logger.info('Failed to clone from %s. error = %s'
                                % (cls.repository_url, str(e)))
                    out.append((cls.language, opt, desc))
            if fpath:
                logger.info('Located %s: %s' % (fname, fpath))
                cfg.set(cls.language, opt, fpath)
        return out
        
    @classmethod
    def set_env_class(cls, **kwargs):
        r"""Set environment variables that are instance independent.

        Args:
            **kwargs: Additional keyword arguments are passed to the
                parent class's method.

        Returns:
            dict: Environment variables for the model process.

        """
        out = super(OSRModelDriver, cls).set_env_class(**kwargs)
        if cls.repository is not None:
            out['OSR_REPOSITORY'] = cls.repository
        kwargs['existing'] = out
        out = CPPModelDriver.set_env_class(**kwargs)
        return out
        
    @classmethod
    def language_executable(cls, **kwargs):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        return cls.executable_path
        
    @classmethod
    def executable_command(cls, args, **kwargs):
        r"""Compose a command for running a program using the exectuable for
        this language (compiler/interpreter) with the provided arguments.

        Args:
            args (list): The program that returned command should run and any
                arguments that should be provided to it.
            unused_kwargs (dict, optional): Existing dictionary that unused
                keyword arguments should be added to. Defaults to None and is
                ignored.
            **kwargs: Additional keyword arguments are passed to the parent
                class.

        Returns:
            list: Arguments composing the command required to run the program
                from the command line using the executable for this language.

        """
        args = [cls.language_executable()] + args
        return super(OSRModelDriver, cls).executable_command(args, **kwargs)

    @classmethod
    def cleanup_dependencies(cls, *args, **kwargs):
        r"""Cleanup dependencies."""
        cls.compile_dependencies(target='cleanygg')
        super(OSRModelDriver, cls).cleanup_dependencies(*args, **kwargs)

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for driver instance.
                deps (list): Dependencies to install.

        """
        out = super(OSRModelDriver, cls).get_testing_options()
        out['kwargs'].update(
            timesync={'name': 'timesync',
                      'inputs': ['carbonAllocation2Roots'],
                      'outputs': ['carbonAllocation2Roots']},
            copy_xml_to_osr=True)
        out['requires_partner'] = True
        return out
