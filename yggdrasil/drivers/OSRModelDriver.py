import os
import git
import subprocess
import tempfile
import logging
import xml.etree.ElementTree as ET
from yggdrasil import tools, platform
from yggdrasil.drivers.DSLModelDriver import ExecutableModelDriver


logger = logging.getLogger(__name__)


class OSRModelDriver(ExecutableModelDriver):
    r"""Class for running OpenSimRoot model.

    Args:
        sync_input_vars (list, optional): Variables that should be synchronized
            from other models. Defaults to [].
        sync_output_vars (list, optional): Variables that should be synchronized
            to other models. Defaults to [].

    """
    _schema_subtype_description = 'Model is an OSR model.'
    _schema_properties = {
        'sync_input_vars': {'type': 'array', 'items': {'type': 'string'},
                            'default': []},
        'sync_output_vars': {'type': 'array', 'items': {'type': 'string'},
                             'default': []}}
    language = 'osr'
    language_ext = '.xml'
    base_languages = ['cpp']
    repository_url = "https://gitlab.com/langmm/OpenSimRoot.git"
    _config_keys = ['repository']
    _config_attr_map = [{'attr': 'repository',
                         'key': 'repository'}]

    @staticmethod
    def after_registration(cls, **kwargs):
        r"""Operations that should be performed to modify class attributes after
        registration.
        """
        ExecutableModelDriver.after_registration(cls, **kwargs)
        cls.executable_path = None
        if cls.repository is not None:
            cls.executable_path = os.path.join(cls.repository, 'OpenSimRoot')
            if platform._is_win:  # pragma: windows
                cls.executable_path += '.exe'
        
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
        if not os.path.isfile(self.executable_path):
            self.compile_osr()
            assert(os.path.isfile(self.executable_path))

    def compile_osr(self):
        r"""Compile the OpenSimRoot executable with the yggdrasil flag set."""
        cwd = os.path.join(self.repository, 'OpenSimRoot')
        if platform._is_win:  # pragma: windows
            cwd = os.path.join(cwd, 'StaticBuild_win64')
            cmd = ['make']
        else:
            cwd = os.path.join(cwd, 'StaticBuild')
            cmd = ['make']
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
        tree = ET.parse(src)
        root = tree.getroot()
        timesync = self.timesync
        assert(timesync)
        if not isinstance(timesync, list):
            timesync = [timesync]
        for tname in reversed(timesync):
            ivars = ' '.join(self.sync_input_vars)
            ovars = ' '.join(self.sync_output_vars)
            cask = ET.Element('SimulaCask', attrib={'name': tname})
            icask = ET.Element('SimulaCaskInputs', text=ivars)
            ocask = ET.Element('SimulaCaskOutputs', text=ovars)
            cask.insert(0, icask)
            cask.insert(1, ocask)
            root.insert(0, cask)
        tree.write(dst)
        return dst

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
        out = super(OSRModelDriver, cls).configure_executable_type(cfg)
        opt = 'repository'
        desc = 'The full path to the OpenSimRoot repository.'
        if not cfg.has_option(cfg, cls.language, opt):
            fname = 'OpenSimRoot'
            fpath = tools.locate_file(fname)
            if fpath:
                logger.info('Located %s: %s' % (fname, fpath))
                cfg.set(cls.language, opt, fpath)
            else:
                logger.info('Could not locate %s, attempting to clone' % fname)
                try:
                    fpath = os.path.join(tempfile.gettempdir(), fname)
                    git.Repo.clone_from(cls.repository_url, fpath)
                    cfg.set(cls.language, opt, fpath)
                except BaseException as e:  # pragma: debug
                    logger.info('Failed to clone from %s. error = %s'
                                % (cls.repository_url, str(e)))
                    out.append((cls.language, opt, desc))
        return out
        
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
