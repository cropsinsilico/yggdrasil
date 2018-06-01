import os
import copy
import pprint
import pystache
import yaml
import importlib
from cis_interface import backwards
from cis_interface.drivers import import_all_drivers
from cis_interface.communication import import_all_comms


_schema_fname = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '.cis_schema.yml'))
_registered_languages = []
_registered_models = {}
_registered_io = {}
_registered_filetypes = []
_registered_files = {}
_registered_connections = {}


class CoerceClass(yaml.YAMLObject):
    r"""Class for coercing strings to types in schema."""

    yaml_loader = yaml.SafeLoader

    def __init__(self, *args):
        pass

    def __call__(self, s):
        return s

    def __repr__(self):
        return "%s()" % self.__class__.__name__

    def __reduce__(self):
        """Return state information for pickling"""
        return self.__class__, tuple()

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class str_to_int_class(CoerceClass):
    r"""Convert a string to an integer.

    Args:
        s (str): String to convert to an int.

    Returns:
        int: Integer conversion of the string.

    """
    yaml_tag = '!str_to_int'

    def __call__(self, s):
        return int(s)


class str_to_bool_class(CoerceClass):
    r"""Convert a string to a boolean.

    Args:
        s (str): String to convert to a bool.

    Returns:
        bool: Evaluation of if the string is True or False.

    """
    yaml_tag = '!str_to_bool'

    def __call__(self, s):
        return (s.lower() == 'true')


class str_to_list_class(CoerceClass):
    r"""Convert a comma separated string of values into a list.

    Args:
        s (str): String of comma separated values.

    Returns:
        list: List of values from string.

    """
    yaml_tag = '!str_to_list'

    def __call__(self, s):
        return s.split(',')


class str_to_function_class(CoerceClass):
    r"""Convert a string to a function.

    Args:
        s (str): String specifying function. The format should be
            "<package.module>:<function>" so that <function> can be imported
            from <package>.

    Returns:
        func: Callable function.

    """
    yaml_tag = '!str_to_function'

    def __call__(self, s):
        pkg_mod = s.split(':')
        if len(pkg_mod) == 2:
            mod, fun = pkg_mod[:]
        else:
            raise ValueError("Could not parse function string: %s" % s)
        modobj = importlib.import_module(mod)
        if not hasattr(modobj, fun):
            raise AttributeError("Module %s has no funciton %s" % (
                modobj, fun))
        out = getattr(modobj, fun)
        return out


class validate_function_class(CoerceClass):
    r"""Validate a value that should be a function."""
    yaml_tag = '!validate_function'

    def __call__(self, field, value, error):
        if not hasattr(value, '__call__'):
            error(field, "Functions must be callable.")


str_to_int = str_to_int_class()
str_to_bool = str_to_bool_class()
str_to_list = str_to_list_class()
str_to_function = str_to_function_class()
validate_function = validate_function_class()


def register_component(component_class):
    r"""Decorator for registering a class as a yaml component."""
    global _registered_languages, _registered_models, _registered_io
    global _registered_filetypes, _registered_files
    global _registered_connections
    yaml_typ = component_class._schema_type
    yaml_opt = component_class._schema
    name = component_class.__class__
    if yaml_typ == 'model':
        if isinstance(component_class._language, list):
            ilang = component_class._language
        else:
            ilang = [component_class._language]
        _registered_languages += ilang
        _registered_models[name] = yaml_opt
    elif yaml_typ == 'io':
        _registered_io[name] = yaml_opt
    elif yaml_typ == 'file':
        if isinstance(component_class._filetype, list):
            ifile = component_class._filetype
        else:
            ifile = [component_class._filetype]
        _registered_filetypes += ifile
        _registered_files[name] = yaml_opt
    elif yaml_typ == 'connection':
        _registered_connections[name] = yaml_opt
    return component_class


def load_schema(fname):
    r"""Load a schema of all the yaml options from a file.

    Args:
        fname (str): Full path to the file the schema should be loaded from.

    Returns:
        dict: cis_interface YAML options.

    """
    with open(fname, 'r') as f:
        contents = f.read()
        schema = yaml.safe_load(contents)
    return schema


def save_schema(fname, schema):
    r"""Save a schema of all the yaml options to a file.

    Args:
        fname (str): Full path to the file the schema should be saved to.
        schema (dict): cis_interface YAML options.

    """
    with open(fname, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False)


def merge_schemas(schema_dict):
    r"""Merge a set of schemas.

    Args:
        schema_dict (dict): Schemas to merge.

    Returns:
        dict: Merged schema.

    """
    out = {}
    for x in schema_dict.values():
        for k, v in x.items():
            if k not in out:
                out[k] = v
            else:
                diff = [ik for ik in set(v) - set(out[k])]
                if (len(diff) == 0):
                    pass
                elif (len(diff) == 1) and (diff[0] == 'dependencies'):
                    alldeps = {}
                    deps = [out[k]['dependencies'], v['dependencies']]
                    for idep in deps:
                        for ik, iv in idep:
                            if ik not in alldeps:
                                alldeps[ik] = []
                            if isinstance(iv, list):
                                alldeps[ik] += iv
                            else:
                                alldeps[ik].append(iv)
                    for ik in alldeps.keys():
                        alldeps[ik] = list(set(alldeps[ik]))
                    vcopy = copy.deecopy(v)
                    vcopy['dependencies'] = alldeps
                    out[k].update(**vcopy)
                else:  # pragma: debug
                    print('Existing:')
                    pprint.pprint(out[k])
                    print('New:')
                    pprint.pprint(v)
                    raise ValueError("Cannot merge schemas.")
    return out


def inherit_schema(orig, key, value, **kwargs):
    r"""Create an inherited schema, adding new value to accepted ones for
    dependencies.
    
    Args:
        orig (dict): Schema that will be inherited.
        key (str): Field that other fields are dependent on.
        value (str): New value for key that dependent fields should accept.
        **kwargs: Additional keyword arguments will be added to the schema
            with dependency on the provided key/value pair.

    Returns:
        dict: New schema.

    """
    if isinstance(value, list):
        value_list = value
    else:
        value_list = [value]
    out = copy.deepcopy(orig)
    for k in out.keys():
        if ('dependencies' in out[k]) and (key in out[k]['dependencies']):
            if not isinstance(out[k]['dependencies'][key], list):
                out[k]['dependencies'][key] = [out[k]['dependencies'][key]]
            out[k]['dependencies'][key] += value_list
    for k, v in kwargs.items():
        out[k] = v
        out[k].setdefault('dependencies', {})
        out[k]['dependencies'].setdefault(key, [])
        out[k]['dependencies'][key] += value_list
    out.update(**kwargs)
    return out


def create_schema():
    r"""Create a schema of all of the yaml options."""
    schema = {}
    # Import all necessary classes to complete registry
    import_all_drivers()
    import_all_comms()
    # IO
    io_schema = merge_schemas(_registered_io)
    # File
    file_schema = merge_schemas(_registered_files)
    file_schema['filetype']['allowed'] = _registered_filetypes
    # Models
    model_schema = merge_schemas(_registered_models)
    model_schema['language']['allowed'] = _registered_languages
    model_schema['inputs'] = {'type': 'list', 'required': False,
                              'schema': io_schema}
    model_schema['outputs'] = {'type': 'list', 'required': False,
                               'schema': io_schema}
    schema['models'] = {'type': 'list', 'schema': model_schema}
    # Connections
    conn_schema = {'input': {'type': 'string', 'required': True,
                             'excludes': 'input_file'},
                   'input_file': {'schema': file_schema, 'required': True,
                                  'excludes': 'input'},
                   'output': {'type': 'string', 'required': True,
                              'excludes': 'output_file'},
                   'output_file': {'schema': file_schema, 'required': True,
                                   'excludes': 'output'},
                   'translator': {'validator': validate_function,
                                  'required': False,
                                  'coerce': str_to_function}}
    schema['connections'] = {'type': 'list', 'schema': conn_schema}
    return schema


def get_schema(fname=None):
    r"""Return the cis_interface schema for YAML options.

    Args:
        fname (str, optional): Full path to the file that the schema should be
            loaded from. If the file dosn't exist, it is created. Defaults to
            _schema_fname.

    Returns:
        dict: cis_interface YAML options.

    """
    if fname is None:
        fname = _schema_fname
    if not os.path.isfile(fname):
        schema = create_schema()
        save_schema(fname, schema)
    return load_schema(fname)


def load_yaml(fname):
    r"""Parse a yaml file defining a run.

    Args:
        fname (str): Path to the yaml file.

    Returns:
        dict: Contents of yaml file.

    """
    fname = os.path.realpath(fname)
    if not os.path.isfile(fname):
        raise IOError("Unable locate yaml file %s" % fname)
    # Open file and parse yaml
    with open(fname, 'r') as f:
        # Mustache replace vars
        yamlparsed = f.read()
        yamlparsed = pystache.render(
            backwards.StringIO(yamlparsed).getvalue(), dict(os.environ))
        yamlparsed = yaml.safe_load(yamlparsed)
    yamlparsed['workingDir'] = os.path.dirname(fname)
    return yamlparsed


def parse_yaml(files):
    r"""Parse list of yaml files.

    Args:
        files (str, list): Either the path to a single yaml file or a list of
            yaml files.

    Raises:
        RuntimeError: If one of the I/O channels is not initialized with driver
            information.

    Returns:
        dict: Dictionary of information parsed from the yamls.

    """
    existing = dict(input={}, output={}, model={}, connection={})
    if isinstance(files, str):
        files = [files]
    # Load each file
    yamls = [load_yaml(f) for f in files]
    # Parse models, then connections to ensure connections can be processed
    for k in ['models', 'connections']:
        for yml in yamls:
            if k not in yml:
                yml[k] = []
            if not isinstance(yml[k], list):
                yml[k] = [yml[k]]
            if k[:-1] in yml:
                if isinstance(yml[k[:-1]], list):
                    yml[k] += yml.pop(k[:-1])
                else:
                    yml[k].append(yml.pop(k[:-1]))
            for x in yml[k]:
                existing = parse_component(x, k[:-1], yml['workingDir'],
                                           existing=existing)
    # Make sure that I/O channels initialized
    for io in ['input', 'output']:
        for k, v in existing[io].items():
            if 'driver' not in v:
                raise RuntimeError("No driver established for %s channel %s" % (
                    io, k))
    return existing


def parse_component(yml, ctype, yamldir, existing=None):
    r"""Parse a yaml entry for a component, adding it to the list of
    existing components.

    Args:
        yml (dict): YAML dictionary for a component.
        ctype (str): Component type. This can be 'input', 'output',
            'model', or 'connection'.
        yamldir (str): Full path to directory containing the yaml this
            component was in.
        existing (dict, optional): Dictionary of existing components.
            Defaults to empty dict.

    Raises:
        TypeError: If yml is not a dictionary.
        ValueError: If dtype is not 'input', 'output', 'model', or
            'connection'.
        RuntimeError: If the yml dictionary is missing a required keyword.
        ValueError: If the component already exists.
        RuntimeError: If 'kwargs' is an entry in the yml.

    Returns:
        dict: All components identified.

    """
    if not isinstance(yml, dict):
        raise TypeError("Component entry in yml must be a dictionary.")
    ctype_list = ['input', 'output', 'model', 'connection']
    if existing is None:
        existing = {k: {} for k in ctype_list}
    if ctype not in ctype_list:
        raise ValueError("'%s' is not a recognized component.")
    # Parse based on type
    if ctype == 'model':
        existing = parse_model(yml, yamldir, existing)
    elif ctype in ['input', 'output']:
        existing = parse_io(yml, yamldir, existing)
    elif ctype == 'connection':
        existing = parse_connection(yml, yamldir, existing)
    yml['workingDir'] = yamldir
    # Ensure component dosn't already exist
    if yml['name'] in existing[ctype]:
        raise ValueError("%s is already a registered '%s' component." % (
            yml['name'], ctype))
    existing[ctype][yml['name']] = yml
    return existing


def parse_model(yml, yamldir, existing):
    r"""Parse a yaml entry for a model.

    Args:
        yml (dict): YAML dictionary for a model.
        yamldir (str): Full path to directory containing the yaml this
            component was in.
        existing (dict): Dictionary of existing components.

    Raises:
        RuntimeError: If the yml dictionary is missing a required keyword.

    Returns:
        dict: Updated log of all entries.

    """
    kws_required = ['name', 'driver', 'args']
    for k in kws_required:
        if k not in yml:
            raise RuntimeError(("The yml specs for component '%s' is missing " +
                                "required keyword '%s'.") % (
                                    yml.get('name', None), k))
    # Init I/O channels
    for io in ['inputs', 'outputs']:
        if io not in yml:
            yml[io] = []
        if not isinstance(yml[io], list):
            yml[io] = [yml[io]]
        if io[:-1] in yml:
            if isinstance(yml[io[:-1]], list):
                yml[io] += yml.pop(io[:-1])
            else:
                yml[io].append(yml.pop(io[:-1]))
        for i in range(len(yml[io])):
            if isinstance(yml[io][i], str):
                yml[io][i] = dict(name=yml[io][i])
    # Add server driver
    if yml.get('is_server', False):
        srv = {'name': yml['name'],
               'driver': 'ServerDriver',
               'args': yml['name'] + '_SERVER'}
        yml['inputs'].append(srv)
        yml['clients'] = []
    # Add client driver
    if yml.get('client_of', []):
        srv_names = yml['client_of']
        if isinstance(srv_names, str):
            srv_names = [srv_names]
        yml['client_of'] = srv_names
        for srv in srv_names:
            cli = {'name': '%s_%s' % (srv, yml['name']),
                   'driver': 'ClientDriver',
                   'args': srv + '_SERVER'}
            yml['outputs'].append(cli)
    # Model index and I/O channels
    yml['model_index'] = len(existing['model'])
    for io in ['inputs', 'outputs']:
        for x in yml[io]:
            x['model_driver'] = yml['name']
            existing = parse_component(x, io[:-1], yamldir, existing=existing)
    return existing

    
def parse_io(yml, yamldir, existing):
    r"""Parse a yaml entry for an I/O channel.

    Args:
        yml (dict): YAML dictionary for an I/O channel.
        yamldir (str): Full path to directory containing the yaml this
            component was in.
        existing (dict): Dictionary of existing components.

    Raises:
        RuntimeError: If the yml dictionary is missing a required keyword.

    Returns:
        dict: Updated log of all entries.

    """
    is_driver = ('driver' in yml)
    kws_required = ['name']
    if is_driver:
        kws_required += ['driver', 'args']
    for k in kws_required:
        if k not in yml:
            raise RuntimeError(("The yml specs for component '%s' is missing " +
                                "required keyword '%s'.") % (
                                    yml.get('name', None), k))
    return existing


def parse_connection(yml, yamldir, existing):
    r"""Parse a yaml entry for a connection between I/O channels.

    Args:
        yml (dict): YAML dictionary for a connection.
        yamldir (str): Full path to directory containing the yaml this
            component was in.
        existing (dict): Dictionary of existing components.

    Raises:
        RuntimeError: If the yml dictionary is missing a required keyword.
        AssertionError: If the 'input' or 'output' entry is not a string.
        RuntimeError: If the 'input' entry is not a model output or file.
        RuntimeError: If neither the 'input' or 'output' entries correspond
            to model I/O channels.
        ValueError: If the 'input' is a file and 'read_meth' entry is not
           'all', 'line', 'table', 'table_array', 'pickle', 'pandas', 'map',
           'ply', or 'obj'.
        ValueError: If the 'output' is a file and 'write_meth' entry is not
           'all', 'line', 'table', 'table_array', 'pickle', 'pandas', 'map',
           'ply', or 'obj'.

    Returns:
        dict: Updated log of all entries.

    """
    kws_required = ['input', 'output']
    for k in kws_required:
        if k not in yml:
            raise RuntimeError(("The yml specs for component '%s' is missing " +
                                "required keyword '%s'.") % (
                                    yml.get('name', None), k))
    assert(isinstance(yml['input'], str))
    assert(isinstance(yml['output'], str))
    in_name = yml.pop('input')
    out_name = yml.pop('output')
    # File input
    if in_name not in existing['output']:
        in_path = os.path.realpath(os.path.join(yamldir, in_name))
        if not os.path.isfile(in_path):
            raise RuntimeError(("Input '%s' not found in any of the registered " +
                                "model outputs and is not a file.") % in_name)
        if out_name not in existing['input']:
            raise RuntimeError(("Output '%s' not found in any of the model " +
                                "inputs and cannot be a file.") % out_name)
        args = in_path
        xi = existing['input'][out_name]
        xi['args'] = args
        read_meth = yml.pop('read_meth', 'all')
        if read_meth == 'all':
            xi['driver'] = 'FileInputDriver'
        elif read_meth == 'line':
            xi['driver'] = 'AsciiFileInputDriver'
        elif read_meth == 'table':
            xi['driver'] = 'AsciiTableInputDriver'
        elif read_meth == 'table_array':
            xi['driver'] = 'AsciiTableInputDriver'
            xi['as_array'] = True
        elif read_meth == 'pickle':
            xi['driver'] = 'PickleFileInputDriver'
        elif read_meth == 'pandas':
            xi['driver'] = 'PandasFileInputDriver'
        elif read_meth == 'map':
            xi['driver'] = 'AsciiMapInputDriver'
        elif read_meth == 'ply':
            xi['driver'] = 'PlyFileInputDriver'
        elif read_meth == 'obj':
            xi['driver'] = 'ObjFileInputDriver'
        else:
            raise ValueError("Invalid read_meth '%s'." % read_meth)
        xo = None
    # File output
    elif out_name not in existing['input']:
        xo = existing['output'][in_name]
        in_temp = xo.get('in_temp', yml.get('in_temp', 'False'))
        if isinstance(in_temp, backwards.string_types):
            in_temp = eval(in_temp)
        if in_temp:
            out_path = out_name
            xo['in_temp'] = True
        else:
            out_path = os.path.realpath(os.path.join(yamldir, out_name))
        args = out_path
        xo['args'] = args
        write_meth = yml.pop('write_meth', 'all')
        if write_meth == 'all':
            xo['driver'] = 'FileOutputDriver'
        elif write_meth == 'line':
            xo['driver'] = 'AsciiFileOutputDriver'
        elif write_meth == 'table':
            xo['driver'] = 'AsciiTableOutputDriver'
        elif write_meth == 'table_array':
            xo['driver'] = 'AsciiTableOutputDriver'
            xo['as_array'] = True
        elif write_meth == 'pickle':
            xo['driver'] = 'PickleFileOutputDriver'
        elif write_meth == 'pandas':
            xo['driver'] = 'PandasFileOutputDriver'
        elif write_meth == 'map':
            xo['driver'] = 'AsciiMapOutputDriver'
        elif write_meth == 'ply':
            xo['driver'] = 'PlyFileOutputDriver'
        elif write_meth == 'obj':
            xo['driver'] = 'ObjFileOutputDriver'
        else:
            raise ValueError("Invalid write_meth '%s'." % write_meth)
        xi = None
    # Generic Input/Output
    else:
        args = '%s_to_%s' % (in_name, out_name)
        # TODO: Use RMQ drivers when models are on different machines
        # Output
        xo = existing['output'][in_name]
        xo['args'] = args
        xo['driver'] = 'OutputDriver'
        # Input
        xi = existing['input'][out_name]
        xi['args'] = args
        xi['driver'] = 'InputDriver'
    # Transfer connection keywords to one connection driver
    if xi is None:
        xo.update(**yml)
    else:
        xi.update(**yml)
    yml['name'] = args
    # Direct comm keywords to input/output
    comm_fields = ['format_str', 'field_names', 'field_units']
    if xi is not None:
        xi.setdefault('icomm_kws', dict())
        for k in comm_fields:
            if k in xi:
                v = xi[k]
                if k in ['field_names', 'field_units']:
                    xi['icomm_kws'].setdefault(k, [n.strip() for n in v.split(',')])
                else:
                    xi['icomm_kws'].setdefault(k, v)
    if xo is not None:
        xo.setdefault('ocomm_kws', dict())
        for k in comm_fields:
            if k in xo:
                v = xo[k]
                if k in ['field_names', 'field_units']:
                    xo['ocomm_kws'].setdefault(k, [n.strip() for n in v.split(',')])
                else:
                    xo['ocomm_kws'].setdefault(k, v)
    return existing
