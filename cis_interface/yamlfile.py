import os
import pprint
import pystache
import yaml
from cis_interface import backwards
from cis_interface.schema import get_schema


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
    yamlparsed['working_dir'] = os.path.dirname(fname)
    return yamlparsed


def prep_yaml(files):
    r"""Prepare yaml to be parsed by Cerberus using schema including covering
    backwards compatible options.

    Args:
        files (str, list): Either the path to a single yaml file or a list of
            yaml files.

    Returns:
        dict: YAML ready to be parsed using schema.

    """
    # Load each file
    if isinstance(files, str):
        files = [files]
    yamls = [load_yaml(f) for f in files]
    # Combine models & connections
    yml_all = {}
    for k in ['models', 'connections']:
        yml_all[k] = []
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
                if isinstance(x, dict):
                    x.setdefault('working_dir', yml['working_dir'])
            yml_all[k] += yml[k]
    # Prep models and connections
    iodict = {'inputs': {}, 'outputs': {}, 'connections': []}
    for yml in yml_all['models']:
        prep_model(yml, iodict)
    bridge_io_drivers(yml_all, iodict)
    yml_all['connections'] += iodict['connections']
    for yml in yml_all['connections']:
        prep_connection(yml, iodict)
    return yml_all


def prep_model(yml, iodict):
    r"""Prepare yaml model entry for parsing with schema.

    Args:
        yml (dict): YAML entry for model that will be modified.
        iodict (dict): Log of all input/outputs.

    """
    class2language = get_schema().class2language
    # Standardize format of input/output
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
            if 'driver' in yml[io][i]:
                yml[io][i].setdefault('working_dir', yml['working_dir'])
            if 'name' in yml[io][i]:
                iodict[io][yml[io][i]['name']] = yml[io][i]
    # Replace driver with language
    if ('language' not in yml) and ('driver' in yml):
        yml['language'] = class2language[yml.pop('driver')][0]
    # String to list
    if ('client_of' in yml) and (not isinstance(yml['client_of'], list)):
        yml['client_of'] = [yml['client_of']]


def prep_connection(yml, iodict):
    r"""Prepare yaml connection entry for parsing with schema.

    Args:
        yml (dict): YAML entry for connection that will be modified.
        iodict (dict): Log of all input/outputs.

    """
    # Plural
    if ('inputs' in yml):
        yml['input'] = yml.pop('inputs')
    if ('outputs' in yml):
        yml['output'] = yml.pop('outputs')
    # Input
    if ('input' in yml):
        if isinstance(yml['input'], list) and (len(yml['input']) == 1):
            yml['input'] = yml['input'][0]
        if ((isinstance(yml['input'], str) and
             (yml['input'] not in iodict['outputs']) and
             ('input_file' not in yml))):
            yml['input_file'] = yml.pop('input')
        elif isinstance(yml['input'], list):
            for x in yml['input']:
                if x not in iodict['outputs']:
                    raise RuntimeError('%s not connected and cannot be a file.' % x)
    if isinstance(yml.get('input_file', None), str):
        yml['input_file'] = dict(name=yml['input_file'])
    if ('read_meth' in yml):
        if 'input_file' not in yml:
            raise ValueError("'read_meth' set, but input is not a file.")
        yml['input_file'].update(**rwmeth2filetype(yml.pop('read_meth')))
    # Output
    if ('output' in yml):
        if isinstance(yml['output'], list) and (len(yml['output']) == 1):
            yml['output'] = yml['output'][0]
        if ((isinstance(yml['output'], str) and
             (yml['output'] not in iodict['inputs']) and
             ('output_file' not in yml))):
            yml['output_file'] = yml.pop('output')
        elif isinstance(yml['output'], list):
            for x in yml['output']:
                if x not in iodict['inputs']:
                    raise RuntimeError('%s not connected and cannot be a file.' % x)
    if isinstance(yml.get('output_file', None), str):
        yml['output_file'] = dict(name=yml['output_file'])
    if ('write_meth' in yml):
        if 'output_file' not in yml:
            raise ValueError("'write_meth' set, but output is not a file.")
        yml['output_file'].update(**rwmeth2filetype(yml.pop('write_meth')))
    # Error if neither input nor output is connected to a model
    if ('input_file' in yml) and ('output_file' in yml):
        raise RuntimeError(("Input '%s' and Output '%s' are both being " +
                            "considered as files since neither is connected " +
                            "to a model.") % (yml['input_file']['name'],
                                              yml['output_file']['name']))
    # Move remaining keys to input/output comm/file
    working_dir = yml.pop('working_dir', None)
    s = get_schema()
    conn_keys = list(set(s['connection'].keys()))

    def migrate_keys(from_dict, to_dict):
        klist = list(from_dict.keys())
        if not isinstance(to_dict, list):
            to_dict = [to_dict]
        for k in klist:
            if k not in conn_keys:
                v = from_dict.pop(k)
                for d in to_dict:
                    d.setdefault(k, v)

    if 'input_file' in yml:
        if working_dir:
            yml['input_file'].setdefault('working_dir', working_dir)
        migrate_keys(yml, yml['input_file'])
    elif 'output_file' in yml:
        if working_dir:
            yml['output_file'].setdefault('working_dir', working_dir)
        migrate_keys(yml, yml['output_file'])
    elif 'input' in yml:
        if isinstance(yml['input'], list):
            io_names = yml['input']
        else:
            io_names = [yml['input']]
        allio = [iodict['outputs'][x] for x in io_names]
        migrate_keys(yml, allio)
    # Error should be raised if there is no input
        

def bridge_io_drivers(yml, iodict):
    r"""Create connection from input/output driver.

    Args:
        dict: YAML entry for model output that should be modified.
        iodict (dict): Log of all input/outputs.

    """
    s = get_schema()
    conn_keys_gen = ['input', 'input_file', 'output', 'output_file']
    file_keys = list(set(s['file'].keys()) - set(s['comm'].keys()))
    conn_keys = list(set(s['connection'].keys()) - set(conn_keys_gen))
    idrivers = []
    odrivers = []
    pairs = []
    new_connections = []
    for x in iodict['inputs'].values():
        if ('driver' in x) and ('args' in x):
            idrivers.append((x['args'], x['name']))
    for x in iodict['outputs'].values():
        if ('driver' in x) and ('args' in x):
            iidx = None
            for i, (iargs, iname) in enumerate(idrivers):
                if x['args'] == iargs:
                    iidx = i
                    break
            if iidx is not None:
                pairs.append((x['name'], idrivers.pop(iidx)[1]))
            else:
                odrivers.append((x['args'], x['name']))
    # Create direct connections from output to input
    for (oname, iname) in pairs:
        oyml = iodict['outputs'][oname]
        iyml = iodict['inputs'][iname]
        conn = dict(input=oname, output=iname)
        new_connections.append((oyml, iyml, conn))
        oyml.pop('working_dir', None)
        iyml.pop('working_dir', None)
    # File input
    for k, v in idrivers:
        oyml = None
        iyml = iodict['inputs'][v]
        fyml = dict(name=k, filetype=cdriver2filetype(iyml['driver']))
        conn = dict(input_file=fyml, output=v)
        new_connections.append((oyml, iyml, conn))
    # File output
    for k, v in odrivers:
        oyml = iodict['outputs'][v]
        iyml = None
        fyml = dict(name=k, filetype=cdriver2filetype(oyml['driver']))
        conn = dict(output_file=fyml, input=v)
        new_connections.append((oyml, iyml, conn))
    # Transfer keyword arguments
    for oyml, iyml, conn in new_connections:
        if oyml is None:
            fkey = 'input_file'
            fyml = iyml
            ymls = [iyml]
        elif iyml is None:
            fkey = 'output_file'
            fyml = oyml
            ymls = [oyml]
        else:
            fkey = None
            fyml = None
            ymls = [oyml, iyml]
        # File keywords
        if fyml is not None:
            for k in file_keys:
                if k in fyml:
                    conn[fkey][k] = fyml.pop(k)
        # Connection keywords
        for y in ymls:
            for k in conn_keys:
                if k not in y:
                    continue
                if k == 'translator':
                    conn.setdefault(k, [])
                    conn[k].append(y.pop(k))
                else:
                    conn.setdefault(k, y.pop(k))
            del y['driver'], y['args']
        # Add connection
        iodict['connections'].append(conn)


def rwmeth2filetype(rw_meth):
    out = {}
    if rw_meth == 'all':
        out['filetype'] = 'binary'
    elif rw_meth == 'line':
        out['filetype'] = 'ascii'
    elif rw_meth == 'table_array':
        out['filetype'] = 'table'
        out['as_array'] = True
    else:
        out['filetype'] = rw_meth
    return out


def cdriver2filetype(driver):
    r"""Convert a connection driver to a file type.

    Args:
        driver (str): The name of the connection driver.

    Returns:
        str: The corresponding file type for the driver.

    """
    schema = get_schema()
    conntypes = schema.class2conntype
    filetypes = schema.class2filetype
    if driver not in conntypes:
        raise ValueError("%s is not a registered connection driver." % driver)
    icomm, ocomm, direction = conntypes[driver][0]
    if direction == 'input':
        ftype = filetypes[icomm][0]
    else:
        ftype = filetypes[ocomm][0]
    return ftype


def parse_yaml(files):
    r"""Parse list of yaml files.

    Args:
        files (str, list): Either the path to a single yaml file or a list of
            yaml files.

    Raises:
        ValueError: If the yml dictionary is missing a required keyword or has
            an invalid value.
        RuntimeError: If one of the I/O channels is not initialized with driver
            information.

    Returns:
        dict: Dictionary of information parsed from the yamls.

    """
    # Parse files using schema
    yml_prep = prep_yaml(files)
    v = get_schema().validator
    yml_norm = v.normalized(yml_prep)
    if not v.validate(yml_norm):
        pprint.pprint(yml_norm)
        pprint.pprint(v.errors)
        raise ValueError("Invalid yaml.")
    yml_all = v.document
    # Parse models, then connections to ensure connections can be processed
    existing = None
    for k in ['models', 'connections']:
        for yml in yml_all[k]:
            existing = parse_component(yml, k[:-1], existing=existing)
    # Make sure that I/O channels initialized
    for io in ['input', 'output']:
        for k, v in existing[io].items():
            if 'driver' not in v:
                raise RuntimeError("No driver established for %s channel %s" % (
                    io, k))
    # Link io drivers back to models
    existing = link_model_io(existing)
    return existing


def parse_component(yml, ctype, existing=None):
    r"""Parse a yaml entry for a component, adding it to the list of
    existing components.

    Args:
        yml (dict): YAML dictionary for a component.
        ctype (str): Component type. This can be 'input', 'output',
            'model', or 'connection'.
        existing (dict, optional): Dictionary of existing components.
            Defaults to empty dict.

    Raises:
        TypeError: If yml is not a dictionary.
        ValueError: If dtype is not 'input', 'output', 'model', or
            'connection'.
        ValueError: If the component already exists.

    Returns:
        dict: All components identified.

    """
    if not isinstance(yml, dict):
        raise TypeError("Component entry in yml must be a dictionary.")
    ctype_list = ['input', 'output', 'model', 'connection',
                  'model_input', 'model_output']
    if existing is None:
        existing = {k: {} for k in ctype_list}
    if ctype not in ctype_list:
        raise ValueError("'%s' is not a recognized component.")
    # Parse based on type
    if ctype == 'model':
        existing = parse_model(yml, existing)
    elif ctype == 'connection':
        existing = parse_connection(yml, existing)
    # Ensure component dosn't already exist
    if yml['name'] in existing[ctype]:
        raise ValueError("%s is already a registered '%s' component." % (
            yml['name'], ctype))
    existing[ctype][yml['name']] = yml
    return existing


def parse_model(yml, existing):
    r"""Parse a yaml entry for a model.

    Args:
        yml (dict): YAML dictionary for a model.
        existing (dict): Dictionary of existing components.

    Returns:
        dict: Updated log of all entries.

    """
    _lang2driver = get_schema().language2class
    yml['driver'] = _lang2driver[yml.pop('language')]
    # Add server driver
    if yml.get('is_server', False):
        srv = {'name': yml['name'],
               'driver': 'ServerDriver',
               'args': yml['name'] + '_SERVER',
               'working_dir': yml['working_dir']}
        yml['inputs'].append(srv)
        yml['clients'] = []
    # Add client driver
    if yml.get('client_of', []):
        srv_names = yml['client_of']
        # prep_model converts to list
        # if isinstance(srv_names, str):
        #     srv_names = [srv_names]
        yml['client_of'] = srv_names
        for srv in srv_names:
            cli = {'name': '%s_%s' % (srv, yml['name']),
                   'driver': 'ClientDriver',
                   'args': srv + '_SERVER',
                   'working_dir': yml['working_dir']}
            yml['outputs'].append(cli)
    # Model index and I/O channels
    yml['model_index'] = len(existing['model'])
    for io in ['inputs', 'outputs']:
        for x in yml[io]:
            x['model_driver'] = [yml['name']]
            existing = parse_component(x, io[:-1], existing=existing)
    return existing
            
    
def parse_connection(yml, existing):
    r"""Parse a yaml entry for a connection between I/O channels.

    Args:
        yml (dict): YAML dictionary for a connection.
        existing (dict): Dictionary of existing components.

    Raises:
        RuntimeError: If the 'input' entry is not a model output or file.
        RuntimeError: If neither the 'input' or 'output' entries correspond
            to model I/O channels.

    Returns:
        dict: Updated log of all entries.

    """
    schema = get_schema()
    comm2conn = schema.conntype2class
    ftyp2comm = schema.filetype2class
    conn_keys_gen = ['input', 'input_file', 'output', 'output_file']
    conn_keys = list(set(schema['connection'].keys()) - set(conn_keys_gen))
    yml_conn = {}
    if not isinstance(yml.get('input', []), list):
        yml['input'] = [yml['input']]
    if not isinstance(yml.get('output', []), list):
        yml['output'] = [yml['output']]
    # File input
    if 'input_file' in yml:
        fname = os.path.expanduser(yml['input_file']['name'])
        if not os.path.isabs(fname):
            fname = os.path.join(yml['input_file']['working_dir'], fname)
        fname = os.path.normpath(fname)
        if not os.path.isfile(fname):
            raise RuntimeError(("Input '%s' not found in any of the registered " +
                                "model outputs and is not a file.") % fname)
        args = fname
        name = ','.join(yml['output'])
        ocomm_pair = None
        icomm_pair = (ftyp2comm[yml['input_file']['filetype']], 'DefaultComm')
        yml_conn.update(**yml['input_file'])
    # File output
    elif 'output_file' in yml:
        fname = os.path.expanduser(yml['output_file']['name'])
        if not yml['output_file'].get('in_temp', False):
            if not os.path.isabs(fname):
                fname = os.path.join(yml['output_file']['working_dir'], fname)
            fname = os.path.normpath(fname)
        args = fname
        name = ','.join(yml['input'])
        ocomm_pair = ('DefaultComm', ftyp2comm[yml['output_file']['filetype']])
        icomm_pair = None
        yml_conn.update(**yml['output_file'])
    # Generic Input/Output
    else:
        iname = ','.join(yml['input'])
        oname = ','.join(yml['output'])
        args = '%s_to_%s' % (iname, oname)
        name = args
        # TODO: Use RMQ drivers when models are on different machines
        # ocomm_pair = ('DefaultComm', 'rmq')
        # icomm_pair = ('rmq', 'DefaultComm')
        ocomm_pair = ('DefaultComm', 'DefaultComm')
        icomm_pair = ('DefaultComm', 'DefaultComm')
    # Output driver
    xo = None
    if ocomm_pair is not None:
        iyml = yml['input']
        iname = ','.join(iyml)
        if len(iyml) == 1:
            xo = existing['output'][iyml[0]]
        else:
            xo = {'name': iname, 'comm': [], 'model_driver': []}
            for y in iyml:
                xo['comm'].append(existing['output'][y])
                xo['model_driver'] += existing['output'][y]['model_driver']
                del existing['output'][y]
            existing = parse_component(xo, 'output', existing)
        xo['args'] = args
        xo['driver'] = comm2conn[(ocomm_pair[0], ocomm_pair[1], 'output')]
    # Input driver
    xi = None
    if icomm_pair is not None:
        oyml = yml['output']
        oname = ','.join(oyml)
        if len(oyml) == 1:
            xi = existing['input'][oyml[0]]
        else:
            xi = {'name': oname, 'comm': [], 'model_driver': []}
            for y in oyml:
                xi['comm'].append(existing['input'][y])
                xi['model_driver'] += existing['input'][y]['model_driver']
                del existing['input'][y]
            existing = parse_component(xi, 'input', existing)
        xi['args'] = args
        xi['driver'] = comm2conn[(icomm_pair[0], icomm_pair[1], 'input')]
    # Transfer connection keywords to one connection driver
    yml_conn.pop('name', None)
    for k in conn_keys:
        if k in yml:
            yml_conn[k] = yml[k]
    if xi is None:
        xo.update(**yml_conn)
    else:
        xi.update(**yml_conn)
    yml['name'] = name
    return existing


def link_model_io(existing):
    r"""Link I/O drivers back to the models they communicate with.

    Args:
        existing (dict): Dictionary of existing components.

    Returns:
        dict: Dictionary with I/O drivers added to models.

    """
    # Add fields
    for m in existing['model'].keys():
        existing['model'][m]['input_drivers'] = []
        existing['model'][m]['output_drivers'] = []
    # Add input dirvers
    for io in existing['input'].values():
        for m in io['model_driver']:
            existing['model'][m]['input_drivers'].append(io)
    # Add output dirvers
    for io in existing['output'].values():
        for m in io['model_driver']:
            existing['model'][m]['output_drivers'].append(io)
    return existing
