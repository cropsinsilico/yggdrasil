import os
import functools
import numpy as np
import pandas as pd
from yggdrasil import units, tools, multitasking
from yggdrasil.drivers.DSLModelDriver import DSLModelDriver


def chain_conversion(*args):
    r"""Get a conversion function from a list of conversion
    functions. The functions will be applied in the order they are
    supplied.

    Args:
        *args: Conversion functions to chain.

    Returns:
        function: Conversion function.

    """
    def fconvert(x):
        out = x
        for a in args:
            if a is not None:
                out = a(out)
        return out
    return fconvert


def convert_with_nan(func):
    r"""Wrap conversion function so that NaNs are not ignored.

    Args:
        func (function): Function that should be applied when NaNs
            are not present.

    Returns:
        function: Wrapped conversion function.

    """
    @functools.wraps(func)
    def func_nan(x):
        if x.isna().any(axis=None):
            return np.nan
        elif isinstance(func, str):
            return x.apply(func)
        else:
            return func(x)
    return func_nan
            

class TimeSyncModelDriver(DSLModelDriver):
    r"""Class for synchronizing states for timesteps between two models.

    Args:
        synonyms (dict, optional): Mapping from variable name to lists
            of alternate variables that should also be merged with the
            variable name specified in the key. List entries can be
            either names of variables or 3-element tuples containing
            the alternate variable name, a function for converting
            from the alternate variable to the key variable, and a
            function for converting from the key variable to the
            alternate variable. Defaults to empty dictionary.
        aggregation (str, dict, optional): Method(s) that should be used
            to aggregate synonymous variables across models. This can
            be a single method that should be used for all synonymous
            variables or a dictionary mapping between synonymous variables
            and the method that should be used by that variable. If a
            variable is not present in the dictionary or a values is
            not provided, 'mean' will be used. See the documentation
            for pandas.DataFrame.aggregate for available options.
        interpolation (str, dict, optional): Method(s) that should be
            used to interpolate missing timesteps. This can be a single
            method or a dictionary mapping between model name and the
            interpolation methods that should be used for variables from
            that model. Defaults to 'index'. See the documentation
            for pandas.DataFrame.interpolate for available options.

    """

    _schema_subtype_description = ('Model is dedicated to synchronizing'
                                   'timesteps between other models.')
    _schema_properties = {
        'synonyms': {'type': 'object',
                     'additionalProperties': {
                         'type': 'array',
                         'items': {'anyOf': [
                             {'type': 'string'},
                             {'type': 'array',
                              'items': [
                                  {'type': 'string'},
                                  {'type': 'function'},
                                  {'type': 'function'}]}]}},
                     'default': {}},
        'aggregation': {
            'anyOf': [{'type': 'function'},
                      {'type': 'string'},
                      {'type': 'object',
                       'additionalProperties': {
                           'anyOf': [{'type': 'function'},
                                     {'type': 'string'}]}}],
            'default': 'mean'},
        'interpolation': {
            'oneOf': [{'type': 'string'},
                      {'type': 'object',
                       'additionalProperties': {
                           'type': 'string'}}],
            'default': 'index'}}
    language = 'timesync'

    def __init__(self, name, *args, **kwargs):
        super(TimeSyncModelDriver, self).__init__(name, *args, **kwargs)
        self.inv_synonyms = {}
        for s0, x in self.synonyms.items():
            for s in x:
                if isinstance(s, (tuple, list)):
                    assert(len(s) == 3)
                    name, fto, ffrom = s[:]
                else:
                    name = s
                    fto = None
                    ffrom = None
                self.inv_synonyms[name] = (s0, fto, ffrom)

    def parse_arguments(self, args, **kwargs):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are ignored.

        """
        assert(isinstance(args, list) and (len(args) == 0))
        self.model_file = 'dummy'
        
    @property
    def model_wrapper_args(self):
        r"""tuple: Positional arguments for the model wrapper."""
        return (self.name, self.inv_synonyms, self.interpolation,
                self.aggregation)

    @classmethod
    def model_wrapper(cls, name, inv_synonyms, interpolation,
                      aggregation, env=None):
        r"""Model wrapper."""
        from yggdrasil.languages.Python.YggInterface import YggRpcServer
        if env is not None:
            os.environ.update(env)
        rpc = YggRpcServer(name)
        threads = {}
        times = []
        tables = {}
        table_units = {'base': {}}
        table_lock = multitasking.RLock()
        while True:
            # Receive values from client models
            flag, values, request_id = rpc.recv_from()
            if not flag:
                print("timesync server: End of input.")
                break
            t, state = values[:]
            t_pd = units.convert_to_pandas_timedelta(t)
            client_model = rpc.ocomm[request_id].client_model
            # Update record
            with table_lock:
                if client_model not in tables:
                    tables[client_model] = pd.DataFrame({'time': times})
                # Update units
                if client_model not in table_units:
                    # NOTE: this assumes that units will not change
                    # between timesteps for a single model. Is there a
                    # case where this might not be true?
                    table_units[client_model] = {
                        k: units.get_units(v) for k, v in state.items()}
                    table_units[client_model]['time'] = units.get_units(t)
                    for k, v in table_units[client_model].items():
                        table_units['base'].setdefault(k, v)
                        if k in inv_synonyms:
                            table_units['base'].setdefault(
                                inv_synonyms[k][0], v)
                # Update the state
                if t_pd not in times:
                    times.append(t_pd)
                for model, table in tables.items():
                    new_data = {'time': [t_pd]}
                    if model == client_model:
                        new_data.update({k: [units.get_data(v)]
                                         for k, v in state.items()})
                    new_data = pd.DataFrame(new_data)
                    idx = table['time'].isin([t_pd])
                    if not idx.any():
                        table = table.append(new_data)
                    elif model == client_model:
                        table = table.drop(table.index[idx])
                        table = table.append(new_data)
                    tables[model] = table.sort_values('time')
            # Assign thread to handle checking when data is filled in
            variables = list(state.keys())
            threads[request_id] = multitasking.YggTaskLoop(
                target=cls.response_loop,
                args=(client_model, request_id, rpc, t_pd,
                      variables, tables, table_units, table_lock,
                      inv_synonyms, interpolation, aggregation))
            threads[request_id].start()
        # Cleanup threads
        for v in threads.values():
            if v.is_alive():
                v.wait(5.0)
        for v in threads.values():
            if v.is_alive():
                v.terminate()

    @classmethod
    def response_loop(cls, client_model, request_id, rpc,
                      time, variables, tables, table_units, table_lock,
                      inv_synonyms, interpolation, aggregation):
        r"""Check for available data and send response if it is
        available.

        Args:
            client_model (str): Name of model that made the request.
            request_id (str): ID associated with request that should
                be responded to.
            rpc (ServerComm): Server RPC comm that should be used to
                reply to the request when the data is available.
            time (pandas.Timedelta): Time to get variables at.
            variables (list): Variables that should be available.
            tables (dict): Mapping from model name to pandas DataFrames
                containing variables supplied by the model.
            table_units (dict): Mapping from model name to dictionaries
                mapping from variable names to units.
            table_lock (RLock): Thread-safe lock for accessing table.
            inv_synonyms (dict): Dictionary mapping from variables to
                base variables and mapping functions used to convert
                between the variables. Defaults to empty dict and no
                conversions are performed.
            interpolation (dict): Mapping from model name to the
                interpolation method that should be used. Defaults to
                empty dictionary.
            aggregation (dict): Mapping from variable name to the
                aggregation method that should be used. Defaults to
                empty dictionary.

        """
        if not rpc.all_clients_connected:
            # Don't start sampling until all clients have connected
            tools.sleep(1.0)
            return
        tot = cls.merge(tables, table_units, table_lock, rpc.open_clients,
                        inv_synonyms, interpolation, aggregation)
        state = {}
        valid = True
        for v in variables:
            v_alt, fto, ffrom = inv_synonyms.get(v, (v, None, None))
            v_res = tot.loc[time, v_alt]
            if pd.isna(v_res):
                valid = False
                break
            v_res = units.convert_to(
                units.add_units(v_res, table_units['base'][v_alt]),
                table_units[client_model][v])
            if ffrom is not None:
                v_res = ffrom(v_res)
            state[v] = v_res
        if valid:
            time_u = units.convert_to(units.convert_from_pandas_timedelta(time),
                                      table_units[client_model]['time'])
            flag = rpc.send_to(request_id, state)  # time_u, state)
            if not flag:
                raise RuntimeError(("Failed to send response to "
                                    "request %s for time %s from "
                                    "model %s.")
                                   % (request_id, time_u, client_model))
            raise multitasking.BreakLoopException
        tools.sleep(1.0)
    
    @classmethod
    def merge(cls, tables, table_units, table_lock, open_clients,
              inv_synonyms, interpolation, aggregation):
        r"""Merge tables from models to get data.

        Args:
            tables (dict): Mapping from model name to pandas DataFrames
                containing variables supplied by the model.
            table_units (dict): Mapping from model name to dictionaries
                mapping from variable names to units.
            table_lock (RLock): Thread-safe lock for accessing table.
            open_clients (list): Clients that are still open.
            inv_synonyms (dict): Dictionary mapping from variables to
                base variables and mapping functions used to convert
                between the variables. Defaults to empty dict and no
                conversions are performed.
            interpolation (dict): Mapping from model name to the
                interpolation method that should be used. Defaults to
                empty dictionary.
            aggregation (dict): Mapping from variable name to the
                aggregation method that should be used. Defaults to
                empty dictionary.


        """
        interp_default = 'index'
        if isinstance(interpolation, str):
            interp_default = interpolation
            interpolation = {}
        # Interpolate
        table_temp = {}
        with table_lock:
            for k, v in tables.items():
                if k in open_clients:
                    limit_area = 'inside'
                else:
                    limit_area = None
                v = v.set_index('time')
                table_temp[k] = v.interpolate(
                    method=interpolation.get(k, interp_default),
                    limit_area=limit_area)
        # Rename + transformation
        for model, v in table_temp.items():
            for k in v.columns:
                if k == 'time':
                    continue
                kbase = inv_synonyms.get(k, (k, None, None))
                funits = units.get_conversion_function(table_units[model][k],
                                                       table_units['base'][kbase[0]])
                fk = chain_conversion(kbase[1], funits)
                if kbase[0] != k:
                    v[kbase[0]] = v[k]
                    v = v.drop(k, axis=1)
                v[kbase[0]] = v[kbase[0]].apply(fk)
            table_temp[model] = v
        # Append
        out = pd.DataFrame()
        for k, v in table_temp.items():
            out = out.append(v)
        # Groupby + aggregate
        if isinstance(aggregation, dict):
            aggregation = {k: convert_with_nan(v) for k, v
                           in aggregation.items()}
        else:
            aggregation = convert_with_nan(aggregation)
        out = out.groupby('time').agg(aggregation)
        return out
