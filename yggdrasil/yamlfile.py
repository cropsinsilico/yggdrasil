import os
import copy
import pprint
import pystache
import yaml
import json
import git
import io as sio
from yggdrasil.schema import standardize, get_schema
from urllib.parse import urlparse


def load_yaml(fname):
    r"""Parse a yaml file defining a run.

    Args:
        fname (str, file, dict): Path to a YAML file, an open file descriptor
            to a file containing a YAML, or a loaded YAML document. If fname starts with
            'git:' then the code will assume the file is in a remote git repository. The
            remainder of fname can be the full url to the YAML file
            (http://mygit.repo/foo/bar/yaml/interesting.yml) or just the repo and
            YAML file (the server is assumed to be github.com if not given)
            (foo/bar/yam/interesting.yaml will be interpreted as
            http://github.com/foo/bar/yam/interesting.yml).

    Returns:
        dict: Contents of yaml file.

    """
    opened = False
    if isinstance(fname, dict):
        yamlparsed = copy.deepcopy(fname)
        yamlparsed.setdefault('working_dir', os.getcwd())
        return yamlparsed
    elif isinstance(fname, str):
        # pull foreign file
        if fname.startswith('git:'):
            # drop the git prefix
            fname = fname[4:]
            # make sure we start with a full url
            if 'http' not in fname:
                url = 'http://github.com/' + fname
            else:
                url = fname
            # get the constituent url parts
            parsed = urlparse(url)
            # get the path component
            splitpath = parsed.path.split('/')
            # the first part is the 'owner' of the repo
            owner = splitpath[1]
            # the second part is the repo name
            reponame = splitpath[2]
            # the full path is the file name and location
            # turn the file path into an os based format
            fname = os.path.join(*splitpath)
            # check to see if the file already exists, and clone if it does not
            if not os.path.exists(fname):
                # create the url for cloning the repo
                cloneurl = parsed.scheme + '://' + parsed.netloc + '/' + owner + '/' +\
                    reponame
                # clone the repo into the appropriate directory
                _ = git.Repo.clone_from(cloneurl, os.path.join(owner, reponame))
                # now that it is cloned, just pass the yaml file (and path) onwards
        fname = os.path.realpath(fname)
        if not os.path.isfile(fname):
            raise IOError("Unable locate yaml file %s" % fname)
        fd = open(fname, 'r')
        opened = True
    else:
        fd = fname
        if (hasattr(fd, 'name') and (not fd.name.startswith('<'))):
            fname = fd.name
        else:
            fname = os.path.join(os.getcwd(), 'stream')
    # Mustache replace vars
    yamlparsed = fd.read()
    yamlparsed = pystache.render(
        sio.StringIO(yamlparsed).getvalue(), dict(os.environ))
    if fname.endswith('.json'):
        yamlparsed = json.loads(yamlparsed)
    else:
        yamlparsed = yaml.safe_load(yamlparsed)
    if not isinstance(yamlparsed, dict):  # pragma: debug
        raise ValueError("Loaded yaml is not a dictionary.")
    yamlparsed['working_dir'] = os.path.dirname(fname)
    if opened:
        fd.close()
    return yamlparsed


def prep_yaml(files):
    r"""Prepare yaml to be parsed by jsonschema including covering backwards
    compatible options.

    Args:
        files (str, list): Either the path to a single yaml file or a list of
            yaml files. Entries can also be opened file descriptors for files
            containing YAML documents or pre-loaded YAML documents.

    Returns:
        dict: YAML ready to be parsed using schema.

    """
    # Load each file
    if not isinstance(files, list):
        files = [files]
    yamls = [load_yaml(f) for f in files]
    # Load files pointed to
    for y in yamls:
        if 'include' in y:
            new_files = y.pop('include')
            if not isinstance(new_files, list):
                new_files = [new_files]
            for f in new_files:
                if not os.path.isabs(f):
                    f = os.path.join(y['working_dir'], f)
                yamls.append(load_yaml(f))
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
    # Create server/client connections
    for srv, clients in existing['server'].items():
        yml = {'inputs': [{'name': x} for x in clients],
               'outputs': [{'name': srv}],
               'driver': 'RPCRequestDriver',
               'name': existing['input'][srv]['model_driver'][0]}
        existing = parse_component(yml, 'connection', existing=existing)
        existing['model'][yml['dst_models'][0]]['clients'] = yml['src_models']
    existing.pop('server')
    # Make sure that I/O channels initialized
    opp_map = {'input': 'output', 'output': 'input'}
    for io in ['input', 'output']:
        remove = []
        for k in list(existing[io].keys()):
            v = existing[io][k]
            if 'driver' not in v:
                if v.get('is_default', False):
                    remove.append(k)
                elif 'default_file' in v:
                    new_conn = {io + 's': [v['default_file']],
                                opp_map[io] + 's': [v]}
                    existing = parse_component(new_conn, 'connection',
                                               existing=existing)
                else:
                    raise RuntimeError("No driver established for %s channel %s" % (
                        io, k))
        # Remove unused default channels
        for k in remove:
            for m in existing[io][k]['model_driver']:
                for i, x in enumerate(existing['model'][m][io + 's']):
                    if x['name'] == k:
                        existing['model'][m][io + 's'].pop(i)
                        break
            existing[io].pop(k)
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
    ctype_list = ['input', 'output', 'model', 'connection', 'server']
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
    language = yml.pop('language')
    yml['driver'] = _lang2driver[language]
    # Add timesync server
    if yml.get('timesync', False):
        if yml['timesync'] is True:
            yml['timesync'] = 'timesync'
        tsync = yml['timesync']
        yml.setdefault('client_of', [])
        yml['client_of'].append(tsync)
        if tsync not in existing['model']:
            tsync_yml = {'name': tsync, 'args': [],
                         'language': 'timesync', 'is_server': True,
                         'working_dir': os.getcwd(),
                         'inputs': [], 'outputs': []}
            existing = parse_component(tsync_yml, 'model',
                                       existing=existing)
    if (language == 'timesync'):
        if (yml['name'] in existing['model']):
            existing['model'].pop(yml['name'])
        yml.update(is_server=True, inputs=[], outputs=[])
    # Add server input
    if yml.get('is_server', False):
        srv = {'name': '%s:%s' % (yml['name'], yml['name']),
               'working_dir': yml['working_dir'],
               'is_timesync': (language == 'timesync')}
        yml['clients'] = []
        yml['inputs'].append(srv)
        existing['server'].setdefault(srv['name'], [])
    # Add client output
    if yml.get('client_of', []):
        for srv in yml['client_of']:
            srv_name = '%s:%s' % (srv, srv)
            if srv == yml.get('timesync', False):
                cli_name = '%s:%s' % (yml['name'], srv)
            else:
                cli_name = '%s:%s_%s' % (yml['name'], srv, yml['name'])
            cli = {'name': cli_name,
                   'working_dir': yml['working_dir']}
            yml['outputs'].append(cli)
            existing['server'].setdefault(srv_name, [])
            existing['server'][srv_name].append(cli_name)
    # Model index and I/O channels
    yml['model_index'] = len(existing['model'])
    for io in ['inputs', 'outputs']:
        for x in yml[io]:
            x['model_driver'] = [yml['name']]
            x['partner_model'] = yml['name']
            x['partner_language'] = language
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
    # Connection
    xx = {'src_models': [], 'dst_models': [],
          'icomm_kws': {'comm': []},
          'ocomm_kws': {'comm': []}}
    for i, y in enumerate(yml['inputs']):
        if is_file['inputs'][i]:
            xx['icomm_kws']['comm'].append(y)
        else:
            xx['icomm_kws']['comm'].append(existing['output'][y['name']])
            xx['icomm_kws']['comm'][-1].update(**y)
            xx['src_models'] += existing['output'][y['name']]['model_driver']
            del existing['output'][y['name']]
    for i, y in enumerate(yml['outputs']):
        if is_file['outputs'][i]:
            xx['ocomm_kws']['comm'].append(y)
        else:
            xx['ocomm_kws']['comm'].append(existing['input'][y['name']])
            xx['ocomm_kws']['comm'][-1].update(**y)
            xx['dst_models'] += existing['input'][y['name']]['model_driver']
            del existing['input'][y['name']]
    # TODO: Split comms if models are not co-located and the master
    # process needs access to the message passed
    yml.update(xx)
    yml.setdefault('driver', 'ConnectionDriver')
    yml.setdefault('name', name)
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
    # Add connections
    for io in existing['connection'].values():
        for m in io['src_models']:
            existing['model'][m]['output_drivers'].append(io)
        for m in io['dst_models']:
            existing['model'][m]['input_drivers'].append(io)
    # Add input drivers
    for io in existing['input'].values():
        for m in io['model_driver']:
            existing['model'][m]['input_drivers'].append(io)
    # Add output drivers
    for io in existing['output'].values():
        for m in io['model_driver']:
            existing['model'][m]['output_drivers'].append(io)
    return existing
