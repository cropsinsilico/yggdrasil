import os
import copy
import pprint
import chevron
import yaml
import json
import git
import io as sio
from yggdrasil.schema import standardize, get_schema
from urllib.parse import urlparse
from yaml.constructor import (
    ConstructorError, BaseConstructor, Constructor, SafeConstructor)


class YAMLSpecificationError(RuntimeError):
    r"""Error raised when the yaml specification does not meet expectations."""
    pass


def no_duplicates_constructor(loader, node, deep=False):
    # https://gist.github.com/pypt/94d747fe5180851196eb
    """Check for duplicate keys."""
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        value = loader.construct_object(value_node, deep=deep)
        if key in mapping:
            raise ConstructorError("while constructing a mapping", node.start_mark,
                                   "found duplicate key (%s)" % key, key_node.start_mark)
        mapping[key] = value
    return loader.construct_mapping(node, deep)


for cls in (BaseConstructor, Constructor, SafeConstructor):
    cls.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                        no_duplicates_constructor)


def clone_github_repo(fname, commit=None, local_directory=None):
    r"""Clone a GitHub repository, returning the path to the local copy of the
    file pointed to by the URL if there is one.

    Args:
        fname (str): URL to a GitHub repository or a file in a GitHub
            repository that should be cloned.
        commit (str, optional): Commit that should be checked out. Defaults
            to None and the HEAD of the default branch is used.
        local_directory (str, optional): Local directory that the file should
            be cloned into. Defaults to None and the current working directory
            will be used.

    Returns:
        str: Path to the local copy of the repository or file in the
            repository.

    """
    from yggdrasil.services import _service_host_env, _service_repo_dir
    if local_directory is None:
        local_directory = os.environ.get(_service_repo_dir, os.getcwd())
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
    fname = os.path.join(local_directory, *splitpath)
    # check to see if the file already exists, and clone if it does not
    if not os.path.exists(fname):
        if os.environ.get(_service_host_env, False):
            raise RuntimeError("Cloning of unvetted git repo is "
                               "not permitted on a integration "
                               "service manager.")
        # create the url for cloning the repo
        cloneurl = parsed.scheme + '://' + parsed.netloc + '/' + owner + '/' +\
            reponame
        # clone the repo into the appropriate directory
        repo = git.Repo.clone_from(cloneurl, os.path.join(local_directory,
                                                          owner, reponame))
        if commit is not None:
            repo.git.checkout(commit)
        repo.close()
        # now that it is cloned, just pass the yaml file (and path) onwards
    return os.path.realpath(fname)


def load_yaml(fname, yaml_param=None, directory_for_clones=None):
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
        yaml_param (dict, optional): Parameters that should be used in
            mustache formatting of YAML files. Defaults to None and is
            ignored.
        directory_for_clones (str, optional): Directory that git repositories
            should be cloned into. Defaults to None and the current working
            directory will be used.

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
            fname = clone_github_repo(fname[4:],
                                      local_directory=directory_for_clones)
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
    if yaml_param is None:
        yaml_param = {}
    yamlparsed = fd.read()
    yamlparsed = chevron.render(
        sio.StringIO(yamlparsed).getvalue(), dict(os.environ, **yaml_param))
    if fname.endswith('.json'):
        yamlparsed = json.loads(yamlparsed)
    else:
        yamlparsed = yaml.safe_load(yamlparsed)
    if not isinstance(yamlparsed, dict):  # pragma: debug
        raise YAMLSpecificationError("Loaded yaml is not a dictionary.")
    yamlparsed['working_dir'] = os.path.dirname(fname)
    if opened:
        fd.close()
    return yamlparsed


def prep_yaml(files, yaml_param=None, directory_for_clones=None):
    r"""Prepare yaml to be parsed by jsonschema including covering backwards
    compatible options.

    Args:
        files (str, list): Either the path to a single yaml file or a list of
            yaml files. Entries can also be opened file descriptors for files
            containing YAML documents or pre-loaded YAML documents.
        yaml_param (dict, optional): Parameters that should be used in
            mustache formatting of YAML files. Defaults to None and is
            ignored.
        directory_for_clones (str, optional): Directory that git repositories
            should be cloned into. Defaults to None and the current working
            directory will be used.

    Returns:
        dict: YAML ready to be parsed using schema.

    """
    from yggdrasil.services import IntegrationServiceManager
    # Load each file
    if not isinstance(files, list):
        files = [files]
    yamls = [load_yaml(f, yaml_param=yaml_param,
                       directory_for_clones=directory_for_clones)
             for f in files]
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
    # Replace references to services with service descriptions
    for i, y in enumerate(yamls):
        services = y.pop('services', [])
        if 'service' in y:
            services.append(y.pop('service'))
        if services:
            y.setdefault('models', [])
            if 'model' in y:
                y['models'].append(y.pop('model'))
        for x in services:
            request = {'action': 'start'}
            for k in ['name', 'yamls', 'yaml_param']:
                if k in x:
                    request[k] = x.pop(k)
            if 'type' in x:
                x.setdefault('service_type', x.pop('type'))
            x.setdefault('for_request', True)
            cli = IntegrationServiceManager(**x)
            response = cli.send_request(**request)
            assert(response.pop('status') == 'complete')
            y['models'].append(response)
    # Standardize format of models and connections to be lists and
    # add working_dir to each
    comp_keys = ['models', 'connections']
    for yml in yamls:
        standardize(yml, comp_keys)
        for k in comp_keys:
            for x in yml[k]:
                if isinstance(x, dict):
                    if (k == 'models') and ('repository_url' in x):
                        repo_dir = clone_github_repo(
                            x['repository_url'],
                            commit=x.get('repository_commit', None),
                            local_directory=directory_for_clones)
                        x.setdefault('working_dir', repo_dir)
                    else:
                        x.setdefault('working_dir', yml['working_dir'])
    # Combine models & connections
    yml_all = {}
    for k in comp_keys:
        yml_all[k] = []
        for yml in yamls:
            yml_all[k] += yml[k]
    return yml_all


def parse_yaml(files, complete_partial=False, partial_commtype=None,
               model_only=False, model_submission=False, yaml_param=None,
               directory_for_clones=None):
    r"""Parse list of yaml files.

    Args:
        files (str, list): Either the path to a single yaml file or a list of
            yaml files.
        complete_partial (bool, optional): If True, unpaired input/output
            channels are allowed and reserved for use (e.g. for calling the
            model as a function). Defaults to False.
        partial_commtype (dict, optional): Communicator kwargs that should be
            be used for the connections to the unpaired channels when
            complete_partial is True. Defaults to None and will be ignored.
        model_only (bool, optional): If True, the YAML will not be evaluated
            as a complete integration and only the individual components will
            be parsed. Defaults to False.
        model_submission (bool, optional): If True, the YAML will be evaluated
            as a submission to the yggdrasil model repository and model_only
            will be set to True. Defaults to False.
        yaml_param (dict, optional): Parameters that should be used in
            mustache formatting of YAML files. Defaults to None and is
            ignored.
        directory_for_clones (str, optional): Directory that git repositories
            should be cloned into. Defaults to None and the current working
            directory will be used.

    Raises:
        ValueError: If the yml dictionary is missing a required keyword or
            has an invalid value.
        RuntimeError: If one of the I/O channels is not initialized with
            driver information.

    Returns:
        dict: Dictionary of information parsed from the yamls.

    """
    s = get_schema()
    # Parse files using schema
    yml_prep = prep_yaml(files, yaml_param=yaml_param,
                         directory_for_clones=directory_for_clones)
    # print('prepped')
    # pprint.pprint(yml_prep)
    if model_submission:
        models = []
        for yml in yml_prep['models']:
            wd = yml.pop('working_dir', None)
            x = s.validate_model_submission(yml)
            if wd:
                x['working_dir'] = wd
            models.append(x)
        yml_prep['models'] = models
        model_only = True
    yml_norm = s.validate(yml_prep, normalize=True,
                          no_defaults=True, required_defaults=True)
    # print('normalized')
    # pprint.pprint(yml_norm)
    # Determine if any of the models require synchronization
    timesync_names = []
    for yml in yml_norm['models']:
        if yml.get('timesync', False):
            if yml['timesync'] is True:
                yml['timesync'] = 'timesync'
            if not isinstance(yml['timesync'], list):
                yml['timesync'] = [yml['timesync']]
            for i, tsync in enumerate(yml['timesync']):
                if isinstance(tsync, str):
                    tsync = {'name': tsync}
                    yml['timesync'][i] = tsync
                timesync_names.append(tsync['name'])
            yml.setdefault('timesync_client_of', [])
            yml['timesync_client_of'].append(tsync['name'])
    for tsync in set(timesync_names):
        for m in yml_norm['models']:
            if m['name'] == tsync:
                assert(m['language'] == 'timesync')
                m.update(is_server=True, inputs=[], outputs=[])
                break
        else:
            yml_norm['models'].append({'name': tsync,
                                       'args': [],
                                       'language': 'timesync',
                                       'is_server': True,
                                       'working_dir': os.getcwd(),
                                       'inputs': [],
                                       'outputs': []})
    # Parse models, then connections to ensure connections can be processed
    existing = None
    for k in ['models', 'connections']:
        for yml in yml_norm[k]:
            existing = parse_component(yml, k[:-1], existing=existing)
    # Exit early
    if model_only:
        return yml_norm
    # Add stand-in model that uses unpaired channels
    if complete_partial:
        existing = complete_partial_integration(
            existing, complete_partial, partial_commtype=partial_commtype)
    # Create server/client connections
    for srv, srv_info in existing['server'].items():
        clients = srv_info['clients']
        if srv not in existing['input']:
            continue
        yml = {'inputs': [{'name': x} for x in clients],
               'outputs': [{'name': srv}],
               'driver': 'RPCRequestDriver',
               'name': existing['input'][srv]['model_driver'][0]}
        if srv_info.get('replaces', None):
            yml['outputs'][0].update({
                k: v for k, v in srv_info['replaces']['input'].items()
                if k not in ['name']})
            yml['response_kwargs'] = {
                k: v for k, v in srv_info['replaces']['output'].items()
                if k not in ['name']}
        existing = parse_component(yml, 'connection', existing=existing)
        existing['model'][yml['dst_models'][0]]['clients'] = yml['src_models']
    existing.pop('server')
    # Make sure that servers have clients and clients have servers
    for k, v in existing['model'].items():
        if v.get('is_server', False):
            for x in existing['model'].values():
                if v['name'] in x.get('client_of', []):
                    break
            else:
                raise YAMLSpecificationError(
                    "Server '%s' does not have any clients.", k)
        elif v.get('client_of', False):
            for s in v['client_of']:
                missing_servers = []
                if s not in existing['model']:
                    missing_servers.append(s)
                if missing_servers:
                    print(list(existing['model'].keys()))
                    raise YAMLSpecificationError(
                        "Servers %s do not exist, but '%s' is a client of them."
                        % (missing_servers, v['name']))
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
                elif (io == 'input') and ('default_value' in v):
                    # TODO: The keys moved should be automated based on schema
                    # if the ValueComm has anymore parameters added
                    vdef = {'name': v['name'],
                            'default_value': v.pop('default_value'),
                            'count': v.pop('count', 1),
                            'commtype': 'value'}
                    new_conn = {'inputs': [vdef],
                                'outputs': [v]}
                    existing = parse_component(new_conn, 'connection',
                                               existing=existing)
                else:
                    raise YAMLSpecificationError(
                        "No driver established for %s channel %s" % (io, k))
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


def complete_partial_integration(existing, name, partial_commtype=None):
    r"""Patch input/output channels that are not connected to a stand-in model.

    Args:
        existing (dict): Dictionary of existing components.
        name (str): Name that should be given to the new model.
        partial_commtype (dict, optional): Communicator kwargs that should be
            be used for the connections to the unpaired channels. Defaults to
            None and will be ignored.

    Returns:
        dict: Updated dictionary of components.

    """
    if isinstance(name, bool):
        name = 'dummy_model'
    new_model = {'name': name,
                 'language': 'dummy',
                 'args': 'dummy',
                 'working_dir': os.getcwd(),
                 'inputs': [],
                 'outputs': []}
    new_connections = []
    # Locate unmatched channels
    miss = {}
    dir2opp = {'input': 'output', 'output': 'input'}
    for io in dir2opp.keys():
        miss[io] = [k for k in existing[io].keys()
                    if not (((io == 'input') and (k in existing['server']))
                            or existing[io][k].get('is_default', False))]
    for srv_info in existing['server'].values():
        if not srv_info['clients']:
            new_model.setdefault('client_of', [])
            new_model['client_of'].append(srv_info['model_name'])
    # TODO: Check that there arn't any missing servers
    # for conn in existing['connection'].values():
    #     for io1, io2 in dir2opp.items():
    #         if ((io1 + 's') in conn):
    #             for x in conn[io1 + 's']:
    #                 if x in miss[io2]:
    #                     miss[io2].remove(x)
    # Create connections to dummy model
    for io1, io2 in dir2opp.items():
        for i in miss[io1]:
            dummy_channel = 'dummy_%s' % i
            dummy_comm = copy.deepcopy(existing[io1][i])
            for k in ['address', 'for_service', 'commtype', 'host']:
                dummy_comm.pop(k, None)
            dummy_comm['name'] = dummy_channel
            if partial_commtype is not None:
                dummy_comm.update(partial_commtype)
            new_model[io2 + 's'].append(dummy_comm)
            new_connections.append({io1 + 's': [{'name': dummy_channel}],
                                    io2 + 's': [{'name': i}]})
    # Parse new components
    existing = parse_component(new_model, 'model', existing=existing)
    for new_conn in new_connections:
        existing = parse_component(new_conn, 'connection', existing=existing)
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
    # s = get_schema()
    if not isinstance(yml, dict):
        raise YAMLSpecificationError("Component entry in yml must be a dictionary.")
    ctype_list = ['input', 'output', 'model', 'connection', 'server']
    if existing is None:
        existing = {k: {} for k in ctype_list}
    if ctype not in ctype_list:
        raise YAMLSpecificationError("'%s' is not a recognized component.")
    # Parse based on type
    if ctype == 'model':
        existing = parse_model(yml, existing)
    elif ctype == 'connection':
        existing = parse_connection(yml, existing)
    # elif ctype in ['input', 'output']:
    #     for k in ['inputs', 'outputs']:
    #         if k not in yml:
    #             continue
    #         for x in yml[k]:
    #             if 'commtype' not in x:
    #                 if 'filetype' in x:
    #                     x['commtype'] = s['file'].subtype2class[x['filetype']]
    #                 elif 'commtype' in x:
    #                     x['commtype'] = s['comm'].subtype2class[x['commtype']]
    # Ensure component dosn't already exist
    if yml['name'] in existing[ctype]:
        pprint.pprint(existing)
        pprint.pprint(yml)
        raise YAMLSpecificationError("%s is already a registered '%s' component." % (
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
    # Add server input
    if yml.get('is_server', False):
        srv = {'name': '%s:%s' % (yml['name'], yml['name']),
               'commtype': 'default',
               'datatype': {'type': 'bytes'},
               'args': yml['name'] + '_SERVER',
               'working_dir': yml['working_dir']}
        if yml.get('function', False) and isinstance(yml['is_server'], bool):
            if (len(yml['inputs']) == 1) and (len(yml['outputs']) == 1):
                yml['is_server'] = {'input': yml['inputs'][0]['name'],
                                    'output': yml['outputs'][0]['name']}
            else:
                raise YAMLSpecificationError(
                    "The 'is_server' parameter is boolean for the model '%s' "
                    "and the 'function' parameter is also set. "
                    "If the 'function' and 'is_server' parameters are used "
                    "together, the 'is_server' parameter must be a mapping "
                    "with 'input' and 'output' entries specifying which of "
                    "the function's input/output variables should be received"
                    "/sent from/to clients. e.g. \n"
                    "\t-input: input_variable\n"
                    "\t-output: output_variables\n" % yml['name'])
        replaces = None
        if isinstance(yml['is_server'], dict):
            replaces = {}
            for io in ['input', 'output']:
                replaces[io] = None
                if not yml['is_server'][io].startswith('%s:' % yml['name']):
                    yml['is_server'][io] = '%s:%s' % (yml['name'], yml['is_server'][io])
                for i, x in enumerate(yml[io + 's']):
                    if x['name'] == yml['is_server'][io]:
                        replaces[io] = x
                        replaces[io + '_index'] = i
                        yml[io + 's'].pop(i)
                        break
                else:
                    raise YAMLSpecificationError(
                        "Failed to locate an existing %s channel "
                        "with the name %s." % (io, yml['is_server'][io]))
            srv['server_replaces'] = replaces
            yml['inputs'].insert(replaces['input_index'], srv)
        else:
            yml['inputs'].append(srv)
        yml['clients'] = []
        existing['server'].setdefault(srv['name'],
                                      {'clients': [],
                                       'model_name': yml['name']})
        if replaces:
            existing['server'][srv['name']]['replaces'] = replaces
    # Mark timesync clients
    timesync = yml.pop('timesync_client_of', [])
    if timesync:
        yml.setdefault('client_of', [])
        yml['client_of'] += timesync
    # Add client output
    if yml.get('client_of', []):
        for srv in yml['client_of']:
            srv_name = '%s:%s' % (srv, srv)
            if srv in timesync:
                cli_name = '%s:%s' % (yml['name'], srv)
            else:
                cli_name = '%s:%s_%s' % (yml['name'], srv, yml['name'])
            cli = {'name': cli_name,
                   'working_dir': yml['working_dir']}
            yml['outputs'].append(cli)
            existing['server'].setdefault(srv_name, {'clients': [],
                                                     'model_name': srv})
            existing['server'][srv_name]['clients'].append(cli_name)
    # Model index and I/O channels
    yml['model_index'] = len(existing['model'])
    for io in ['inputs', 'outputs']:
        for x in yml[io]:
            if ((yml.get('function', False) and (not x.get('outside_loop', False))
                 and yml.get('is_server', False))):
                x.setdefault('dont_copy', True)
            if yml.get('allow_threading', False) or (
                    (yml.get('copies', 1) > 1)
                    and (not x.get('dont_copy', False))):
                x['allow_multiple_comms'] = True
            # TODO: Replace model_driver with partner_model?
            x['model_driver'] = [yml['name']]
            x['partner_model'] = yml['name']
            if yml.get('copies', 1) > 1:
                x['partner_copies'] = yml['copies']
            x['partner_language'] = language
            existing = parse_component(x, io[:-1], existing=existing)
    for k in yml.get('env', {}).keys():
        if not isinstance(yml['env'][k], str):
            yml['env'][k] = json.dumps(yml['env'][k])
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
                raise YAMLSpecificationError(
                    ("Input '%s' not found in any of the registered "
                     + "model outputs and is not a file.") % x['name'])
            x['address'] = fname
        elif 'default_value' in x:
            x['address'] = x['default_value']
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
          'inputs': [], 'outputs': []}
    for i, y in enumerate(yml['inputs']):
        if is_file['inputs'][i] or ('default_value' in y):
            xx['inputs'].append(y)
        else:
            new = existing['output'][y['name']]
            new.update(y)
            xx['inputs'].append(new)
            xx['src_models'] += existing['output'][y['name']]['model_driver']
            del existing['output'][y['name']]
    for i, y in enumerate(yml['outputs']):
        if is_file['outputs'][i]:
            xx['outputs'].append(y)
        else:
            new = existing['input'][y['name']]
            new.update(y)
            xx['outputs'].append(new)
            xx['dst_models'] += existing['input'][y['name']]['model_driver']
            del existing['input'][y['name']]
    # TODO: Split comms if models are not co-located and the main
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
    return existing
