from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver


class RModelDriver(InterpretedModelDriver):  # pragma: R
    r"""Base class for running R models.

    Args:
        name (str): Driver name.
        args (str or list): Argument(s) for running the model in matlab.
            Generally, this should be the full path to a Matlab script.
        **kwargs: Additional keyword arguments are passed to parent class's
            __init__ method.

    """
    _schema_subtype_description = ('Model is written in R.')
    language = 'R'
    language_aliases = ['r']
    language_ext = '.R'
    base_languages = ['python']
    default_interpreter = 'Rscript'
    # Dynamically setting the interface library cause circular logic
    interface_library = 'yggdrasil.interface.YggInterface'
    # interface_library = PythonModelDriver.interface_library
    # The Batch version causes output to saved to a file rather than directed to
    # stdout
    # default_interpreter_flags = ['CMD', 'BATCH' '--vanilla', '--silent']
    function_param = {
        'interface': ['library(reticulate)',
                      'ygg <- import(\"{interface_library}\")'],
        'input': '{channel} <- ygg$YggInput(\"{channel_name}\")',
        'output': '{channel} <- ygg$YggOutput(\"{channel_name}\")',
        'recv': 'list[{flag_var}, {recv_var}] <- {channel}$recv()',
        'send': '{flag_var} <- {channel}$send({send_var})',
        'comment': '#',
        'indent': 2 * ' ',
        'quote': '\"',
        'print': 'print(\"{message}\")',
        'block_end': '}',
        'if_begin': 'if({cond}) {',
        'for_begin': 'for ({iter_var} in {iter_begin}:{iter_end}) {',
        'while_begin': 'while ({cond}) {',
        'try_begin': 'tryCatch({',
        'try_except': '}, error = function({error_var}) {',
        'try_end': '})'}
