import os
import git
import subprocess
import tempfile
import logging
import pystache
import io as sio
import xml.etree.ElementTree as ET
from yggdrasil import tools, platform
from yggdrasil.components import import_component
from yggdrasil.drivers.ExecutableModelDriver import ExecutableModelDriver


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
    language = 'osr'
    language_ext = '.xml'
    base_languages = ['cpp']
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
        if self.copy_xml_to_osr:
            self.model_file = os.path.join(
                self.repository, 'OpenSimRoot', 'InputFiles',
                os.path.basename(self.model_file))
        # if not (isinstance(self.executable_path, str)
        #         and os.path.isfile(self.executable_path)):
        self.compile_osr()
        assert(os.path.isfile(self.executable_path))

    @classmethod
    def compile_osr(cls):
        r"""Compile the OpenSimRoot executable with the yggdrasil flag set."""
        for x in cls.base_languages:
            base_cls = import_component('model', x)
            base_cls.compile_dependencies()
        cwd = os.path.join(cls.repository, 'OpenSimRoot')
        if platform._is_win:  # pragma: windows
            cwd = os.path.join(cwd, 'StaticBuild_win64')
        else:
            cwd = os.path.join(cwd, 'StaticBuild')
        cmd = ['make', 'OpenSimRootYgg', '-j4']
        subprocess.check_call(cmd, cwd=cwd)

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

    def wrap_xml(self, src, dst=None):
        r"""Wrap the input XML, adding tags for the inputs/outputs specified for
        this model.

        Args:
            src (str): Full path to the XML file that should be wrapped.
            dst (str, optional): Full path to the location where the updated XML
                should be saved. Defaults to None and will be set based on src.

        Returns:
            str: Full path to XML file produced.

        """
        if dst is None:
            dst = '_copy'.join(os.path.splitext(src))
        with open(src, 'r') as fd:
            src_contents = fd.read()
        src_contents = pystache.render(
            sio.StringIO(src_contents).getvalue(), self.set_env())
        root = ET.fromstring(src_contents)
        timesync = self.timesync
        assert(timesync)
        if not isinstance(timesync, list):
            timesync = [timesync]
        for tsync in reversed(timesync):
            ivars = tsync.get('inputs', [])
            ovars = tsync.get('outputs', [])
            if not isinstance(ivars, list):
                ivars = [ivars]
            if not isinstance(ovars, list):
                ovars = [ovars]
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
            root.append(cask)
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
        if not cfg.has_option(cls.language, opt):
            fname = 'OpenSimRoot'
            fpath = tools.locate_file(fname)
            if fpath:
                logger.info('Located %s: %s' % (fname, fpath))
                cfg.set(cls.language, opt, fpath)
            else:
                logger.info('Could not locate %s, attempting to clone' % fname)
                try:
                    fpath = os.path.join(tempfile.gettempdir(), fname)
                    if not os.path.isdir(fpath):
                        git.Repo.clone_from(cls.repository_url, fpath,
                                            branch=cls.repository_branch)
                    cfg.set(cls.language, opt, fpath)
                except BaseException as e:  # pragma: debug
                    logger.info('Failed to clone from %s. error = %s'
                                % (cls.repository_url, str(e)))
                    out.append((cls.language, opt, desc))
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
        out['OSR_REPOSITORY'] = cls.repository
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
        args = [cls.executable_path] + args
        return super(OSRModelDriver, cls).executable_command(args, **kwargs)
