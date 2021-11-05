import os
import re
import logging
import numpy as np
from yggdrasil import units as unyts
from yggdrasil.drivers.DSLModelDriver import DSLModelDriver
logger = logging.getLogger(__name__)


class ODEError(BaseException):
    pass


class RetryODE(ODEError):
    r"""Error indicating that a solution should be attempted with new
    parameters.

    Args:
        msg (str): Error message.
        temp_solution (bool, optional): If True, the solution found on retry
            will not be stored for future calls. Defaults to False.

    """

    def __init__(self, msg, temp_solution=False):
        self.temp_solution = temp_solution
        super(RetryODE, self).__init__(msg)


class MultipleSolutionsError(RetryODE):
    r"""Exception for case of multiple symbolic solutions."""
    pass


class RetryWithNumeric(RetryODE):
    r"""Error when solution should be found numerically instead."""
    pass


def _get_function(x):
    r"""Extract the function from an expression."""
    from sympy.core.function import AppliedUndef, Subs, Derivative
    if isinstance(x, AppliedUndef):
        return x.func, x.args[0]
    elif isinstance(x, (Subs, Derivative)):
        if isinstance(x, Subs):
            x = x.doit()
        if isinstance(x, Subs):
            deriv = x.expr
            arg = x.point[0]
        else:
            deriv = x
            arg = x.variables[0]
        return deriv.expr.func, arg
    return None, None


class ODEModel(object):
    r"""Class for handling ODE calculations.

    Args:
        eqns (list): Sympy symbolic representation of an ODE
            equation or system of equations with the form
            dx/dt = ... such that the righthand side of each
            equation is the expresion for the derivative.
        t (sympy.Symbol): Independent variable.
        funcs (list): sympy.Function symbols for the functions being solved.
        local_map (dict): Mapping between strings and the corresponding sympy
            objects.
        ics (dict): Boundary conditions.
        param (dict): Constant values for parameters in the equations that
            are not expected to change.
        odeint_kws (dict, optional): Keyword arguments that should be passed
            to scipy.integrate.odeint if it is called in integrating the
            equations numerically.
        fsolve_kws (dict, optional): Keyword arguments that should be passed
            to scipy.optimize.fsolve if it is called in finding the steady
            state solution numerically.
        use_numeric (bool, optional): If True, the equations will be solved
            numerically even if a symbolic solution is possible.
        units (dict, optional): Units for the variables in the equations.

    """

    def __init__(self, eqns, t, funcs, local_map, ics, param,
                 odeint_kws=None, fsolve_kws=None, use_numeric=False,
                 units=None):
        self.eqns0 = [eqns[f.diff(t)] for f in funcs]
        self.eqns = None
        self.constants = None
        self.t = t
        self.units = units
        self.funcs = funcs
        self.local_map = local_map
        self.ics = ics
        self.param = param
        self.sympy_vars = tuple(
            [t] + funcs + [self.local_map[x] for x in param.keys()])
        self.sol = None
        if odeint_kws is None:
            odeint_kws = {}
        self.odeint_kws = odeint_kws
        if fsolve_kws is None:
            fsolve_kws = {}
        self.fsolve_kws = fsolve_kws
        self.use_numeric = use_numeric

    def reset_constants(self, inputs):
        r"""Reset the constants and equations."""
        self.constants = {self.local_map[k]: v for k, v
                          in self.param.items() if k not in inputs}
        self.eqns = self.eqns0
        # self.eqns = []
        # for eqn in self.eqns0:
        #     x = eqn
        #     for k, v in self.constants.items():
        #         x = x.subs(k, v)
        #     self.eqns.append(x)

    def __call__(self, compute_method, inputs):
        r"""Find a solution.

        Args:
            compute_method (str): Method that should be used to find a solution.
            inputs (dict): A mapping of values for the independent variable,
                parameters, and/or dependent variables.

        Returns:
            dict: Mapping between the names of independent variables and their
                value for the determined solution.

        """
        new_ics = {}
        iparam = ODEModelDriver.normalize_ics(
            inputs, self.t, self.local_map, units=self.units,
            store_funcs=new_ics)
        self.ics.update(new_ics)
        method_order = [{}, {'use_numeric': True}]
        if compute_method == 'steady_state':
            method_order.insert(1, {'from_roots': True})
        constants_changed = (
            (self.constants is None)
            or any(k in self.constants for k in inputs.keys()))
        sol = self.sol
        if (sol is None) or new_ics or constants_changed:
            temp_solution = False
            if constants_changed:
                self.reset_constants(inputs)
            for kwargs in method_order:
                try:
                    sol = self.solve(compute_method, **kwargs)
                    break
                except NotImplementedError as e:
                    # Indicates Sympy could not find a symbolic solution
                    logger.info(f"Sympy raised NotImplementedError('{e}'). "
                                f"Another method will be tried.")
                except RetryODE as e:
                    temp_solution = temp_solution or e.temp_solution
            if not sol:
                raise ODEError("No solution could be found")
            if not temp_solution:
                self.sol = sol
        try:
            result = sol(iparam, constants=self.constants)
        except RetryWithNumeric as e:
            assert(not sol.is_numeric)
            sol = self.solve(compute_method, use_numeric=True)
            result = sol(iparam, constants=self.constants)
            if not e.temp_solution:
                self.sol = sol
        return {str(f.__class__): x for f, x in zip(self.funcs, result)}
        
    def solve(self, compute_method, use_numeric=False, from_roots=False):
        r"""Determine a solution and return a function form.

        Args:
            compute_method (str): Method that should be used to find a solution.
            use_numeric (bool, optional): If True, the solution will be found
                numerically. Defaults to False.
            from_roots (bool, optional): If True, the steady state solution
                will be found for solving for the equation roots. Defaults to
                False.

        Returns:
            LambdifySolution: Solution that can be called to determine the
                value of variables for desired parameters.

        """
        from sympy import sympify, Eq, solve
        from sympy.solvers.ode.systems import dsolve_system
        if self.use_numeric:
            use_numeric = True
        dsol = None
        kws = {}
        soltype = None
        if use_numeric:
            soltype = "NUMERIC"
            dsol = {f: eqn.rhs for f, eqn in zip(self.funcs, self.eqns)}
            if compute_method == 'integrate':
                kws.update(ics=self.ics, method='odeint', **self.odeint_kws)
            elif compute_method == 'steady_state':
                kws.update(ics=self.ics, method='fsolve', **self.fsolve_kws)
        elif (compute_method == 'steady_state') and from_roots:
            soltype = "SYMBOLIC STEADY STATE"
            dsol = solve([Eq(eqn.rhs, sympify(0.0)) for eqn in self.eqns],
                         self.funcs, dict=True)
            if len(dsol) > 1:
                raise MultipleSolutionsError(
                    f"More than one symbolic solution for equation roots, "
                    f"retrying numerically: {dsol}")
            dsol = dsol[0]
        else:
            soltype = "SYMBOLIC"
            dsol = dsolve_system(self.eqns, funcs=self.funcs, t=self.t,
                                 ics=self.ics)
            if len(dsol) > 1:  # pragma: debug
                raise MultipleSolutionsError(
                    f"There is more than one symbolic solution, "
                    f"retrying numerically: {dsol}")
            dsol = {eqn.lhs: eqn.rhs for eqn in dsol[0]}
            if compute_method == 'steady_state':
                from sympy import oo
                kws = {'method': 'flimit', 'limits': {self.t: oo}}
        logger.info(f'{soltype} SOLUTION: {dsol}')
        sol = LambdifySolution(self.sympy_vars, dsol, self.funcs,
                               units=self.units, **kws)
        return sol


class LambdifySolution(object):
    r"""Callable solution to an ODE system of equations.

    Args:
        args (list): sympy.Symbol variables in the provided equations that
            are accepted as inputs to the solution function.
        eqns (list): sympy expressions for the solutions or derivatives that
            will be solved numerically.
        funcs (list): sympy.Function independent variables in the provided
            equations.
        ics (dict, optional): Boundary conditions for the provided equations.
        method (str, optional): Numeric method that should be used to solve
            the equations. If not provided (or None), the solution will be
            symbolic and is assumed to already be represented by the provided
            equations.
        units (dict, optional): Units associated with variables in the provided
            equations.
        limits (dict, optional): Mapping of variable limits that should be
            applied after other substitutions are made.
        **kws: Additional keyword arguments will be passed to the numeric
            method used to find a solution (if one is used).
    
    """

    def __init__(self, args, eqns, funcs, ics=None, method=None,
                 units=None, **kws):
        from sympy import lambdify
        self.t = args[0]
        self.args = args
        self.eqns = eqns
        self.funcs = funcs
        self.ics = ics
        self.method = method
        self.units = units
        self.args_units = [units.get(a, None) for a in args]
        self.funcs_units = [units.get(f, None) for f in funcs]
        self.kws = kws
        self.lambdified = lambdify(args, [eqns[f] for f in funcs])
        self.is_numeric = (method in ['odeint', 'fsolve'])
        self.last_state = None

    def solution(self, *args):
        r"""Call the lambdified solution."""
        args = [unyts.add_units(a, u)
                if (u and not unyts.has_units(a) and (a is not None))
                else a for a, u in zip(args, self.args_units)]
        out = self.lambdified(*args)
        out = [unyts.add_units(x, u)
               if (u and not unyts.has_units(x)) else x
               for x, u in zip(out, self.funcs_units)]
        return out

    @property
    def order(self):
        r"""list: Order of arguments to the lambda function."""
        return [x for x in self.args]

    def get_t0(self):
        r"""Get the independent variable associated with the provided ICs."""
        from sympy.core.numbers import Number
        t0 = None
        for v in self.ics.keys():
            _, tv = _get_function(v)
            if t0 is None:
                t0 = tv
            else:
                assert(tv == t0)
        t0_f = t0
        if isinstance(t0, Number):
            # TODO: Check for non-float (e.g. complex)?
            t0_f = np.float64(t0)
        return t0, t0_f

    def _fodeint(self, X, t, args):
        args = [t] + list(X) + list(args)
        return self.solution(*args)

    def odeint(self, iparam, from_prev=False, **kwargs):
        r"""Wrapper for calling scipy.integrate.odeint."""
        from scipy.integrate import odeint
        if from_prev and (self.last_state is not None):
            t0_f, X0 = self.last_state
        else:
            t0, t0_f = self.get_t0()
            X0 = [self.ics[f.subs(self.t, t0)] for f in self.funcs]
        param = [iparam.get(k, None) for k in self.order]
        NX = len(X0) + 1
        t = np.array([t0_f, param[0]])
        out = odeint(self._fodeint, X0, t, args=(param[NX:],), **kwargs)[-1]
        self.last_state = (t[-1], out)
        return out

    def _fsolve(self, X, args):
        args = list(X) + list(args)
        return [X[0]] + self.solution(*args)

    def fsolve(self, iparam, **kwargs):
        r"""Wrapper for calling scipy.optimize.fsolve."""
        from scipy.optimize import fsolve
        t0, t0_f = self.get_t0()
        X0 = [t0_f] + [self.ics[f.subs(self.t, t0)] for f in self.funcs]
        param = [iparam.get(k, None) for k in self.order[len(X0):]]
        return fsolve(self._fsolve, X0, args=(param,))[1:]

    def flimit(self, iparam, limits={}):
        r"""Compute the value through substitution followed by limit."""
        from sympy import lambdify, Limit
        out = []
        for f in self.funcs:
            x = self.eqns[f]
            for k, v in iparam.items():
                x = x.subs(k, v)
            for k, v in limits.items():
                try:
                    x = x.limit(k, v)
                except NotImplementedError:  # pragma: debug
                    raise RetryWithNumeric("Complex limit")
            if isinstance(x, Limit):
                raise RetryWithNumeric("Complex limit")
            out.append(x)
        f = lambdify(tuple([]), out)
        return [float(x) if isinstance(x, int) else x for x in f()]

    def __call__(self, param, constants={}):
        iparam = dict(param)
        if constants:
            iparam.update(constants)
        if self.method is None:
            try:
                out = self.solution(*[iparam.get(k, None) for k in self.order])
            except BaseException as e:  # pragma: debug
                raise RetryWithNumeric(e)
            if any(np.isnan(x) for x in out):  # pragma: debug
                raise RetryWithNumeric("NaN", temp_solution=True)
            return out
        return getattr(self, self.method)(iparam, **self.kws)


class ODEModelDriver(DSLModelDriver):
    r"""Class for running ODE models.

    Args:
        equations (list): Symbolic representations of equations or the name
            of a text file containing an equation on each line.
        compute_method (str, optional): Method that should be used to compute
            outputs for received inputs. Valid methods include:
                integrate: Compute the value(s) of the ODE solution for the
                    parameters/independent variable values received as input.
                steady_state: Determine the steady state solution to the
                    ODE equations based on parameter values received as
                    input.
        independent_var (list, optional): Name of independent variable.
            Defaults to 't'.
        independent_var_units (str, optional): Units of the independent
            variable. If not provided, the independent variable is treated
            as unitless.
        dependent_vars (list, optional): Names of dependent variables in the
            provided equations. If not provided, all variables in the
            equation that are not parameters or the independent variable will
            be considered a dependent variable.
        boundary_conditions (dict, optional): Mapping between variables and
            their boundary conditions.
        parameters (dict, optional): Mapping between named parameters in the
            equations and their values.
        assumptions (dict, optional): Mapping between a variable or parameter
            name and a map of sympy assumption keywords for that variable. A
            full list of supported sympy assumptions can be found here
            https://docs.sympy.org/latest/modules/core.html#module-sympy.core.
              assumptions
        odeint_kws (dict, optional): Options that should be passed to the
            scipy odeint integration routine if numeric integration is used
            (in the event that sympy cannot find a symbolic solution or
            use_numeric is True). In addition to the keyword arguments
            accepted by scipy.integrate.odeint, the following are also
            supported:
              from_prev (bool, optional): If True, the integration should
                  always begin from the previous end state instead of starting
                  from the initial conditions (default behavior).
        fsolve_kws (dict, optional): Options that should be passed to the
            scipy fsolve routine when solving for the steady state solution if
            numeric integration is used (in the even that sympy cannot find
            a symbolic solution or use_numeric is True).
        use_numeric (bool, optional): If True, numeric methods will be used to
            find a solution without attempting to find a symbolic solution.
            Defaults to False.

    """
    _schema_subtype_description = 'Model is a symbolic ODE model.'
    _schema_properties = {
        'compute_method': {'type': 'string', 'default': 'integrate',
                           'choices': ['integrate', 'steady_state']},
        'independent_var': {'type': 'string'},
        'independent_var_units': {'type': 'string'},
        'dependent_vars': {'type': 'array', 'items': {'type': 'string'}},
        'boundary_conditions': {
            'type': 'object',
            'additionalProperties': {'type': 'float'}},
        'parameters': {
            'type': 'object',
            'additionalProperties': {'type': 'float'}},
        'assumptions': {
            'type': 'object',
            'additionalProperties': {
                'type': 'object',
                'additionalProperties': {'type': 'boolean'}}},
        'odeint_kws': {'type': 'object'},
        'fsolve_kws': {'type': 'object'},
        'use_numeric': {'type': 'boolean', 'default': False},
    }
    language = 'ode'
    interface_dependencies = ['sympy']
    _derivative_regexes = [
        r'd(?:\^(?P<n_top>\d+))?\s*(?P<f>\w+)\s*'
        r'(?P<args>\(\s*ARG\s*(?:\,\s*ARG\s*)*\))?\s*/'
        r'\s*d\s*(?P<t>\w+)(?:\^(?P<n_bottom>\d+))?',
        r'(?P<f>\w+)\s*(?P<n_tics>\'+)(?:\s*\(\s*(?P<t>ARG)\s*\))?'
    ]

    @classmethod
    def language_version(cls, **kwargs):
        r"""Determine the version of this language.

        Args:
            **kwargs: Keyword arguments are passed to cls.run_executable.

        Returns:
            str: Version of compiler/interpreter for this language.

        """
        try:
            import sympy
            return sympy.__version__
        except ImportError:  # pragma: debug
            raise RuntimeError("sympy not installed.")

    def parse_arguments(self, args, **kwargs):
        r"""Sort model arguments to determine which one is the executable
        and which ones are arguments.

        Args:
            args (list): List of arguments provided.
            **kwargs: Additional keyword arguments are passed
                to the parent class's method.

        """
        super(ODEModelDriver, self).parse_arguments(args, **kwargs)
        if os.path.isfile(self.model_file):
            raise NotImplementedError
        else:
            self.equations = self.args

    @classmethod
    def extract_derivatives(cls, equation, arg_regex=r'\w+',
                            match=False):
        r"""Get information about derivatives contained in the provided
        equation.

        Args:
            equation (str): Equation to extract
            arg_regex (str, optional): Regex used to represent arguments.
                Defaults to r'\w+'.
            match (bool, optional): If True, the entire expression will be
                matched against the regex. Defaults to False.

        Returns:
            list: Dictionaries of information about the recovered derivatives.

        """
        def match2dict(m):
            mdict = m.groupdict()
            iout = {'name': m.group(0),
                    'f': m.group('f'),
                    't': mdict.get('t', 't'),
                    'n': 1}
            if mdict.get('n_tics', None):
                iout['n'] = len(mdict['n_tics'])
            elif mdict.get('n_top', None) or mdict.get('n_bottom', None):
                assert(mdict['n_top'] == mdict['n_bottom'])
                iout['n'] = int(mdict['n_top'])
            return iout
            
        out = []
        for regex in cls._derivative_regexes:
            regex = regex.replace('ARG', arg_regex)
            if match:
                m = re.match(regex, equation)
                if m:
                    return match2dict(m)
            else:
                for m in re.finditer(regex, equation):
                    out.append(match2dict(m))
        return out

    @classmethod
    def replace_derivatives(cls, equation, symbols):
        r"""Replace derivative expressions with versions that sympy can parse.

        Args:
            equation (str): Equation to extract
            symbols (dict): Existing dict for tracking variables parsed from
                the equation.

        Returns:
            str: Updated version of the equation.

        """
        out = equation
        for x in cls.extract_derivatives(equation):
            if x['t'] is None:
                x['t'] = 't'
            args = [f"{x['f']}({x['t']})"] + x['n'] * [x['t']]
            out = out.replace(x['name'], f"Derivative({', '.join(args)})")
            if symbols['independent_var'] is None:
                symbols['independent_var'] = x['t']
            if (((x['f'] not in symbols['dependent_bases'])
                 and (x['f'] not in symbols['dependent_funcs']))):
                symbols['dependent_funcs'].append(x['f'])
        for f in symbols['dependent_funcs']:
            func_regex = r'(?<!\w)' + f + r'(?!(?:\w)|(?:\s*\())'
            for m in reversed(list(re.finditer(func_regex, out))):
                out = (out[:m.start()]
                       + f"{f}({symbols['independent_var']})"
                       + out[m.end():])
        return out

    @classmethod
    def normalize_ics(cls, ics, t, local_map, units=None, store_funcs=None):
        r"""Normalize ICs, adding units as necessary."""
        from sympy import sympify
        arg_regex = r'(?:\-|\+)?\d+(?:\.\d+)?(?:(?:e|E)(\-|\+)?\d+?)?'
        out = {}
        for k, v in ics.items():
            m = cls.extract_derivatives(k, arg_regex=arg_regex, match=True)
            f = None
            if m:
                f = local_map[m['f']]
                arg = float(m['t'])
                kt = f(t).diff(t, int(m['n']))
                k0 = kt.subs(t, arg)
            else:
                k0 = sympify(k, locals=local_map)
                f, arg = _get_function(k0)
                kt = k0
                if f:
                    kt = k0.subs(arg, t)
            if f and units and units.get(t, None):
                tic = unyts.add_units(float(arg), units[t])
                k0 = kt.subs(t, tic)
            if (units is not None) and unyts.has_units(v):
                units[kt] = unyts.get_units(v)
            if (store_funcs is not None) and f:
                store_funcs[k0] = v
            else:
                out[k0] = v
        return out

    @property
    def model_wrapper_kwargs(self):
        r"""dict: Keyword arguments for the model wrapper."""
        out = super(ODEModelDriver, self).model_wrapper_kwargs
        out.update(
            inputs=self.inputs,
            outputs=self.outputs,
            equations=self.equations,
            independent_var=self.independent_var,
            independent_var_units=self.independent_var_units,
            dependent_vars=self.dependent_vars,
            parameters=self.parameters,
            assumptions=self.assumptions,
            boundary_conditions=self.boundary_conditions,
            compute_method=self.compute_method,
            odeint_kws=self.odeint_kws,
            fsolve_kws=self.fsolve_kws,
            use_numeric=self.use_numeric)
        return out

    @classmethod
    def setup_model(cls, equations=None, independent_var=None,
                    dependent_vars=None, parameters=None, assumptions=None,
                    boundary_conditions=None, odeint_kws=None,
                    fsolve_kws=None, use_numeric=False,
                    input_vars=None, independent_var_units=None):
        r"""Get ODE solution using Sympy."""
        import sympy
        from sympy import sympify, Symbol, Eq, Function
        if dependent_vars is None:
            dependent_vars = []
        symbols = {
            'independent_var': independent_var,
            'dependent_bases': [x.split('(', 1)[0] for x in dependent_vars],
            'dependent_funcs': []}
        equations = [cls.replace_derivatives(x, symbols) for x in equations]
        dependent_vars += symbols['dependent_funcs']
        if parameters is None:
            parameters = {}
        if assumptions is None:
            assumptions = {}
        if independent_var is None:
            assert(symbols['independent_var'])
            independent_var = symbols['independent_var']
        local_map = {
            independent_var: Symbol(
                independent_var, **assumptions.get(independent_var, {}))}
        for k in parameters.keys():
            local_map[k] = Symbol(k, **assumptions.get(k, {}))

        def add_function(x, skip_dep=False):
            if isinstance(x, str):
                x_str = x
                if '(' not in x:
                    # Assume that function depends on independent var
                    x_str += f'({independent_var})'
                x = sympify(x_str, locals=local_map)
            else:
                x_str = str(x)
            xf = x.__class__
            xfunc, xargs = x_str.split('(', 1)
            if (str(xf) != xfunc) or (xfunc in assumptions):
                xa = sympify('f(' + xargs, locals=local_map)
                xf = Function(xfunc, **assumptions.get(xfunc, {}))
                x = xf(*xa.args)
            v = str(x)
            if xf == getattr(sympy, str(xf), None):
                return v
            local_map[str(xf)] = xf
            local_map[v] = x
            if not skip_dep:
                if v not in dependent_vars:
                    dependent_vars.append(v)
            return x

        def add_vars(x):
            if isinstance(x, str):
                try:
                    x = sympify(x, locals=local_map)
                except TypeError:
                    # Allows for the equation in the YAML to use the function
                    # name without arguments (e.g. 'f' vs 'f(t)')
                    local_map2 = dict(local_map)
                    for v in dependent_vars:
                        local_map2[v.split('(', 1)[0]] = local_map[v]
                    x = sympify(x, locals=local_map2)
            v = str(x)
            if v in local_map:
                return local_map[v]
            if x.args:
                if isinstance(x, Function):
                    add_function(x)
                # This is not a stable API, so a new class may need to be
                # created for future versions of sympy
                x._args = tuple(add_vars(xx) for xx in x.args)
            elif isinstance(x, Symbol) and (str(x) != independent_var):
                x = add_function(v)
            return x

        t = local_map[independent_var]
        funcs = [add_function(v, skip_dep=True) for v in dependent_vars]
        eqns = {}
        nder = {f: 0 for f in funcs}
        for x in equations:
            lhs = add_vars(x.split('=')[0])
            rhs = add_vars(x.split('=')[1])
            eqns[lhs] = Eq(lhs, rhs)
            nder[lhs.expr] = max(nder[lhs.expr], lhs.args[1][1])
        ics = {}
        units = None
        if boundary_conditions:
            units = {t: independent_var_units}
            ics = cls.normalize_ics(boundary_conditions, t, local_map,
                                    units=units)
        # Use substitutions to make intermediate orders explicit
        subs = {}
        for f, nmax in nder.items():
            for i in range(1, nmax):
                k = f.diff(t, i)
                if k not in eqns:
                    v = Function(f"{f.__class__}_d{i}")(t)
                    eqns[k] = Eq(k, v)
                    funcs.append(v)
                    local_map[str(v)] = v
                    k2 = f.diff(t, i + 1)
                    subs[k] = v
                    if k2 in eqns:
                        eqns[v.diff(t, 1)] = eqns.pop(k2)
        for k, v in subs.items():
            for f in list(eqns.keys()):
                if f != k:
                    eqns[f] = eqns[f].subs(k, v)
            for f in list(ics.keys()):
                ics[f.subs(k, v).doit()] = ics.pop(f)
            for f in list(units.keys()):
                units[f.subs(k, v).doit()] = units.pop(f)
        return ODEModel(eqns, t, funcs, local_map, ics, parameters,
                        odeint_kws=odeint_kws, fsolve_kws=fsolve_kws,
                        use_numeric=use_numeric, units=units)

    @classmethod
    def model_wrapper(cls, env=None, working_dir=None, inputs=[],
                      outputs=[], compute_method='integrate',
                      integrator_settings={}, **kwargs):
        r"""Model wrapper."""
        if env is not None:
            os.environ.update(env)
        if working_dir is not None:
            os.chdir(working_dir)
        # Setup interface objects
        input_map, output_map = cls.setup_interface(
            inputs=inputs, outputs=outputs)
        input_vars = []
        for v in input_map.values():
            input_vars += v['vars']
        # Determine symbolic equations via Sympy
        model = cls.setup_model(input_vars=input_vars, **kwargs)
        # Perform computations for each received input
        while True:
            flag = False
            # Receive input
            input_vals = {}
            for k, v in input_map.items():
                flag, value = v['comm'].recv_dict(key_order=v['vars'])
                if not flag:
                    logger.info(f"No more input from {k}")
                    break
                for iv in v['vars']:
                    input_vals[iv] = value[iv]
            if not flag:
                break
            # Compute output
            output_vals = model(compute_method, input_vals)
            # Send output
            for k, v in output_map.items():
                iout = {iv: output_vals[iv] for iv in v['vars']}
                flag = v['comm'].send_dict(iout, key_order=v['vars'])
                if not flag:  # pragma: debug
                    raise RuntimeError(f"Error sending to {k}")

    @classmethod
    def get_testing_options(cls):
        r"""Method to return a dictionary of testing options for this class.

        Returns:
            dict: Dictionary of variables to use for testing. Key/value pairs:
                kwargs (dict): Keyword arguments for driver instance.
                deps (list): Dependencies to install.

        """
        out = super(ODEModelDriver, cls).get_testing_options()
        out.update(
            requires_partner=True,
            source=[],
            args=['d^2f/dx^2=-9*f(x)+A'],
            kwargs={'independent_var': 'x',
                    'boundary_conditions': {'f(0)': 1.0},
                    'parameters': {'A': 1}})
        return out
