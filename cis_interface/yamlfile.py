import os
import pprint
import pystache
import yaml
from cis_interface import backwards
from cis_interface.schema import standardize, get_schema


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
    if not isinstance(yamlparsed, dict):  # pragma: debug
        raise ValueError("Loaded yaml is not a dictionary.")
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
    # Standardize format of models and connections to be lists and
    # add working_dir to each
    comp_keys = ['models', 'connections']
    for yml in yamls:
        standardize(yml, comp_keys)
        for k in comp_keys:
            for x in yml[k]:
                if isinstance(x, dict):
                    x.setdefault('working_dir', yml['working_dir'])
    # Combine models & connections
    yml_all = {}
    for k in comp_keys:
        yml_all[k] = []
        for yml in yamls:
            yml_all[k] += yml[k]
    return yml_all


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
    s = get_schema()
    # Parse files using schema
    yml_prep = prep_yaml(files)
    # print('prepped')
    # pprint.pprint(yml_prep)
    yml_norm = s.validate(yml_prep, normalize=True)
    # print('normalized')
    # pprint.pprint(yml_norm)
    # Parse models, then connections to ensure connections can be processed
    existing = None
    for k in ['models', 'connections']:
        for yml in yml_norm[k]:
            existing = parse_component(yml, k[:-1], existing=existing)
    # Make sure that I/O channels initialized
    for io in ['input', 'output']:
        for k, v in existing[io].items():
            if 'driver' not in v:
                raise RuntimeError("No driver established for %s channel %s" % (
                    io, k))
    # Link io drivers back to models
    existing = link_model_io(existing)
    # print('drivers')
    # pprint.pprint(existing)
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
    s = get_schema()
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
    elif ctype in ['input', 'output']:
        for k in ['icomm_kws', 'ocomm_kws']:
            if k not in yml:
                continue
            for x in yml[k]['comm']:
                if 'comm' not in x:
                    if 'filetype' in x:
                        x['comm'] = s['file'].subtype2class[x['filetype']]
                    elif 'commtype' in x:
                        x['comm'] = s['comm'].subtype2class[x['commtype']]
    # Ensure component dosn't already exist
    if yml['name'] in existing[ctype]:
        pprint.pprint(existing)
        pprint.pprint(yml)
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
    _lang2driver = get_schema()['model'].subtype2class
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
        RuntimeError: If the 'inputs' entry is not a model output or file.
        RuntimeError: If neither the 'inputs' or 'outputs' entries correspond
            to model I/O channels.

    Returns:
        dict: Updated log of all entries.

    """
    schema = get_schema()
    # File input
    is_file = {'inputs': [], 'outputs': []}
    iname_list = []
    for x in yml['inputs']:
        is_file['inputs'].append(schema.is_valid_component('file', x))
        if is_file['inputs'][-1]:
            fname = os.path.expanduser(x['name'])
            if not os.path.isabs(fname):
                fname = os.path.join(x['working_dir'], fname)
            fname = os.path.normpath(fname)
            if (not os.path.isfile(fname)) and (not x.get('wait_for_creation', False)):
                raise RuntimeError(("Input '%s' not found in any of the registered "
                                    + "model outputs and is not a file.") % x['name'])
            x['address'] = fname
        else:
            iname_list.append(x['name'])
    # File output
    oname_list = []
    for x in yml['outputs']:
        is_file['outputs'].append(schema.is_valid_component('file', x))
        if is_file['outputs'][-1]:
            fname = os.path.expanduser(x['name'])
            if not x.get('in_temp', False):
                if not os.path.isabs(fname):
                    fname = os.path.join(x['working_dir'], fname)
                fname = os.path.normpath(fname)
            x['address'] = fname
        else:
            oname_list.append(x['name'])
    iname = ','.join(iname_list)
    oname = ','.join(oname_list)
    if not iname:
        args = oname
    elif not oname:
        args = iname
    else:
        args = '%s_to_%s' % (iname, oname)
    name = args
    # TODO: Use RMQ drivers when models are on different machines
    # ocomm_pair = ('DefaultComm', 'rmq')
    # icomm_pair = ('rmq', 'DefaultComm')
    # Output driver
    xo = None
    if iname:  # empty name results when all of the inputs are files
        iyml = yml['inputs']
        xo = {'name': iname, 'model_driver': [],
              'icomm_kws': {'comm': []},
              'ocomm_kws': {'comm': []}}
        for i, y in enumerate(iyml):
            if not is_file['inputs'][i]:
                xo['icomm_kws']['comm'].append(existing['output'][y['name']])
                xo['icomm_kws']['comm'][-1].update(**y)
                xo['model_driver'] += existing['output'][y['name']]['model_driver']
                del existing['output'][y['name']]
        # Add single non-file intermediate output comm if there are any non-file
        # outputs and an output comm for each file output
        if (sum(is_file['outputs']) < len(is_file['outputs'])):
            xo['ocomm_kws']['comm'].append({'name': args, 'no_suffix': True})
        for i, y in enumerate(yml['outputs']):
            if is_file['outputs'][i]:
                xo['ocomm_kws']['comm'].append(y)
        existing = parse_component(xo, 'output', existing)
        xo['args'] = args
        xo['driver'] = 'OutputDriver'
    # Input driver
    xi = None
    if oname:  # empty name results when all of the outputs are files
        oyml = yml['outputs']
        xi = {'name': oname, 'model_driver': [],
              'icomm_kws': {'comm': []},
              'ocomm_kws': {'comm': []}}
        for i, y in enumerate(oyml):
            if not is_file['outputs'][i]:
                xi['ocomm_kws']['comm'].append(existing['input'][y['name']])
                xi['ocomm_kws']['comm'][-1].update(**y)
                xi['model_driver'] += existing['input'][y['name']]['model_driver']
                del existing['input'][y['name']]
        # Add single non-file intermediate input comm if there are any non-file
        # inputs and an input comm for each file input
        if (sum(is_file['inputs']) < len(is_file['inputs'])):
            xi['icomm_kws']['comm'].append({'name': args, 'no_suffix': True})
        for i, y in enumerate(yml['inputs']):
            if is_file['inputs'][i]:
                xi['icomm_kws']['comm'].append(y)
        existing = parse_component(xi, 'input', existing)
        xi['args'] = args
        xi['driver'] = 'InputDriver'

    # Parse drivers
    
    # Transfer connection keywords to one connection driver
    conn_keys_gen = ['inputs', 'outputs']
    conn_keys = list(set(schema['connection'].properties) - set(conn_keys_gen))
    yml_conn = {}
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
