import os
import copy
from yggdrasil import platform
from yggdrasil.config import ygg_cfg
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.schema import inherit_schema


_flag_keys = ['-']
if platform._is_win:  # pragma: windows
    _flag_keys.append('/')


class CompiledModelDriver(ModelDriver):
    r"""Base class for models written in compiled languages.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model on the command
            line and any arguments/flags that should be passed to the compiler/
            linker. The way arguments are sorted is controlled by the
            parse_arguments method. The default method used several attributes
            to determine which arguments are compiler/linker flags and which
            are model arguments.
        overwrite (bool, optional): If True, any existing object or executable
            files for the model are overwritten, otherwise they will only be
            compiled if they do not exist. Defaults to True. Setting this to
            False can be done to improve performance after debugging is complete,
            but this dosn't check if the source files should be changed, so
            users should make sure they recompile after any changes. The value
            of this keyword also determines whether or not any compilation
            products are cleaned up after a run.
        **kwargs: Additional keyword arguments are passed to parent class.

    Attributes:
        overwrite (bool): If True, any existing compilation products will be
            overwritten by compilation and cleaned up following the run.
            Otherwise, existing products will be used and will remain after
            the run.
        products (list): File created by the compilation.
        source_files (list): Source files.
        compiler_flags (list): Compiler flags.
        linker_flags (list): Linker flags.
        model_executable (str): Full path to the compiled model executable.
        model_args (list): Runtime arguments for running the model on the command
            line.

    """

    _linker_flags = []
    _compiler_flags = []
    _compiler_keys = _flag_keys
    _compiler_switch = []
    _linker_keys = ['l', 'L']
    _linker_switch = []
    _object_keys = []
    _object_switch = []
    _schema_properties = inherit_schema(
        ModelDriver._schema_properties,
        {'overwrite': {'type': 'boolean', 'default': True}})

    def __init__(self, name, args, **kwargs):
        super(CompiledModelDriver, self).__init__(name, args, **kwargs)
        # Parse arguments
        self.source_files = []
        self.compiler_flags = copy.deepcopy(self._compiler_flags)
        self.linker_flags = copy.deepcopy(self._linker_flags)
        self.model_executable = None
        self.model_args = []
        self.parse_arguments(self.args)
        # Compile
        self.compile()
        assert(len(self.products) > 0)
        self.model_executable = self.products[0]
        assert(os.path.isfile(self.model_executable))
        self.debug("Compiled %s", self.model_executable)
        # Compose arguments
        if platform._is_win:  # pragma: windows
            self.args = [os.path.splitext(self.model_executable)[0]]
        else:
            self.args = [os.path.join(".", self.model_executable)]
        self.args += self.model_args
        self.debug(self.args)
    
    @classmethod
    def compiler(cls):
        r"""Command required to compile a model written in this language from
        the command line.

        Returns:
            str: Name of (or path to) compiler executable.

        """
        out = ygg_cfg.get(cls._language, 'compiler',
                          getattr(cls, '_compiler', cls._language))
        if out is None:
            raise NotImplementedError("Compiler not set for language '%s'."
                                      % cls._language)

    @classmethod
    def language_executable(cls):
        r"""Command required to compile/run a model written in this language
        from the command line.

        Returns:
            str: Name of (or path to) compiler/interpreter executable required
                to run the compiler/interpreter from the command line.

        """
        return cls.compiler()

    @classmethod
    def configure(cls, cfg):
        r"""Add configuration options for this language."""
        cfg = super(CompiledModelDriver, cls).configure(cfg)
        # TODO: Required libraries
        return cfg

    def parse_arguments(self, args):
        r"""Sort arguments based on their syntax to determine if an argument
        is a source file, compilation flag, or runtime option/flag that should
        be passed to the model executable.

        Args:
            args (list): List of arguments provided.

        Raises:
            RuntimeError: If there is not a valid source file in the argument
                list.

        """
        is_compiler = True
        is_linker = False
        is_object = False
        ext = self._language_ext
        if not isinstance(ext, list):
            ext = [ext]
        self.compiler_flags.append('-DYGG_DEBUG=%d'
                                   % self.logger.getEffectiveLevel())
        if platform._is_win:  # pragma: windows
            args = [a.lower() for a in args]
        for a in args:
            if any([a.endswith(e) for e in ext]):
                self.source_files.append(a)
            # Handle objects
            elif a in self._object_switch:
                is_object = True
            elif is_object:
                # Previous argument indicated this is the executable
                self.model_executable = a
                is_object = False
            elif any([a.startswith(k) for k in self._object_keys]):
                for k in self._object_keys:
                    if a.startswith(k):
                        self.model_executable = a.split(k)[-1]
                        break
            # Handle linker/compiler
            elif a in self._linker_switch:
                is_linker = True
            elif is_compiler or any([a.startswith(k) for k in self._compiler_keys]):
                for k in self._compiler_keys:
                    if a.startswith(k):
                        kc = k
                        break
                if is_linker or any([a.startswith(kc + k) for k in self._linker_keys]):
                    if a not in self.linker_flags:
                        self.linker_flags.append(a)
                elif a not in self.compiler_flags:
                    self.compiler_flags.append(a)
            else:
                self.model_args.append(a)
        if len(self.source_files) == 0:
            raise RuntimeError("Could not locate a source file in the "
                               + "provided arguments.")

    def compile(self):
        r"""Compile model executable(s) and appends any products produced by
        the compilation that should be removed after the run is complete."""
        raise NotImplementedError("compile method not implemented for '%s'"
                                  % self._language)

    def cleanup(self):
        r"""Remove compile executable."""
        if self.overwrite:
            self.remove_products()
        super(CompiledModelDriver, self).cleanup()
        
    def remove_products(self):
        r"""Delete products produced during the compilation process."""
        for p in self.products:
            if os.path.isfile(p):
                T = self.start_timeout()
                while ((not T.is_out) and os.path.isfile(p)):
                    try:
                        os.remove(p)
                    except BaseException:  # pragma: debug
                        if os.path.isfile(p):
                            self.sleep()
                        if T.is_out:
                            raise
                self.stop_timeout()
                if os.path.isfile(p):  # pragma: debug
                    raise RuntimeError("Failed to remove product: %s" % p)
