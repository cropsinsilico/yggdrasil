import os
import re
import copy
import pprint
import logging
import numpy as np
from yggdrasil import units as unyts
from yggdrasil.drivers.DSLModelDriver import DSLModelDriver
try:
    import sympy
    from sympy import (sympify, lambdify, Symbol, Function, Derivative, Eq,
                       Limit, solve, oo)
    from sympy.core.numbers import Number
    from sympy.core.function import UndefinedFunction, AppliedUndef, Subs
    from sympy.solvers.ode.systems import dsolve_system
except ImportError:
    pass
logger = logging.getLogger(__name__)


# TODO:
#   - Allow inputs to be called at more than two levels, this would also
#     apply to the automated wrapping of model functions


class ODEError(BaseException):
    r"""Error indicating a problems with creating/evaluating an ODE model."""
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
    r"""Utility for extracting components from an expression containing
    a function or derivative.

    Args:
        x (sympy.Expression): SymPy expression for a function or derivative.

    Returns:
        tuple: The function object, the independent variable symbol that the
            function depends on, and the order of the derivative (if one is
            present). If there is not a function or derivative present, all
            three tuple members will be None.

    """
    if isinstance(x, AppliedUndef):
        return x.func, x.args[0], None
    elif isinstance(x, (Subs, Derivative)):
        if isinstance(x, Subs):
            x = x.doit()
        if isinstance(x, Subs):
            deriv = x.expr
            arg = x.point[0]
        else:
            deriv = x
            arg = x.variables[0]
        degree = deriv.args[1][1]
        return deriv.expr.func, arg, degree
    return None, None, None


class ODEModel(object):
    r"""Class for handling ODE calculations.

    Args:
        eqns (list): String symbolic representation of an ODE
            equation or system of equations with the form
            dx/dt = ... such that the righthand side of each
            equation is the expresion for the derivative.
        t (str, optional): Independent variable name. Defaults to 't' if it
            cannot be inferred from the expression.
        funcs (list, optional): String symbols for the functions being solved.
            If not provided, the names of the dependent variables are inferred
            from the equations.
        ics (dict, optional): Boundary conditions.
        param (dict, optional): Constant values for parameters in the
            equations that are not expected to change.
        assumptions (dict, optional): Mapping between a variable or parameter
            name and a map of sympy assumption keywords for that variable. A
            full list of supported sympy assumptions can be found here
            https://docs.sympy.org/latest/modules/core.html#module-sympy.core.
              assumptions
        units (dict, optional): Units for the variables in the equations.
        t_units (str, optional): Units for the independent variable. It will
            be treated as dimensionless if not provided.
        odeint_kws (dict, optional): Keyword arguments that should be passed
            to scipy.integrate.odeint if it is called in integrating the
            equations numerically. If 'name' in present, scipy.integrate.ode
            will be used instead and these arguments will be passed to the
            set_integrator method. In addition, the following keywords are
            also supported:
              from_prev (bool, optional): If True, the integration should
                  always begin from the previous end state instead of starting
                  from the initial conditions (default behavior).
        fsolve_kws (dict, optional): Options that should be passed to the
            scipy fsolve routine when solving for the steady state solution if
            numeric integration is used (in the event that sympy cannot find
            a symbolic solution or use_numeric is True).
        use_numeric (bool, optional): If True, numeric methods will be used to
            find a solution without attempting to find a symbolic solution.
            Defaults to False.

    """
    _derivative_regexes = [
        r'd(?:\^(?P<n_top>\d+))?\s*(?P<f>\w+)\s*'
        r'(?:\(\s*(?P<args>ARG\s*(?:\,\s*ARG\s*)*)\))?\s*/'
        r'\s*d\s*(?P<t>\w+)(?:\^(?P<n_bottom>\d+))?',
        r'(?P<f>\w+)\s*(?P<n_tics>\'+)(?:\s*\(\s*(?P<t>ARG)\s*\))?'
    ]
    _noarg_function_regex = (
        r'(?<!\w)FUNC(?!(?:\w)|(?:\s*\())'
    )
    _function_regex = (
        r'(?<!\w)FUNC\((?P<args>\s*ARG\s*(?:\,\s*ARG\s*)*)\)'
    )
    _func_regex = r'\w+'
    _arg_regex = (
        r'(?:(?:\w+)|(?:(?:\-|\+)?\d+(?:\.\d+)?'
        r'(?:(?:e|E)(\-|\+)?\d+?)?))'
    )

    def __init__(self, eqns, t=None, funcs=None, ics={}, param=None,
                 assumptions=None, units=None, t_units=None,
                 odeint_kws=None, fsolve_kws=None, use_numeric=False):
        if funcs is None:
            funcs = []
        if param is None:
            param = {}
        if assumptions is None:
            assumptions = {}
        if units is None:
            units = {}
        if odeint_kws is None:
            odeint_kws = {}
        if fsolve_kws is None:
            fsolve_kws = {}
        self.eqns = {}
        self.constants = None
        self.t = None
        self.units = dict(units)
        self.funcs = []
        self.local_map = {k: Symbol(k, **assumptions.get(k, {}))
                          for k in param.keys()}
        self.ics = {}
        self.param = dict(param)
        self.assumptions = dict(assumptions)
        self.t_units = t_units
        if t is not None:
            self.add_t(t)
        if isinstance(eqns, str):
            eqns = [eqns]
        eqns = [self.replace_derivatives(eqn) for eqn in eqns]
        for x in funcs:
            self.add_func(x.split('(', 1)[0])
        eqns = [self.replace_functions(eqn) for eqn in eqns]
        for x in eqns:
            lhs = self.sympify(x.split('=')[0])
            rhs = self.sympify(x.split('=')[1])
            self.eqns[lhs] = Eq(lhs, rhs)
            for k in self.locate_unknown_symbols(self.eqns[lhs]):
                self.local_map[str(k)] = k
                self.param[str(k)] = None
        assert(not self.normalize_inputs(ics))
        self.complete_system()
        self.funcs_deriv = [f.diff(self.t) for f in self.funcs]
        self.sol = None
        self.odeint_kws = dict(odeint_kws)
        self.fsolve_kws = dict(fsolve_kws)
        self.use_numeric = use_numeric

    @property
    def func_names(self):
        r"""list: Names of independent variables in the equations."""
        return [str(f.__class__) for f in self.funcs]

    @property
    def sympy_vars(self):
        r"""tuple: Order of variables in arguments to lambdified equations."""
        return tuple([self.t] + self.funcs
                     + [self.local_map[x] for x in self.param.keys()])
            
    def __str__(self):
        return (f"ODEModel(t='{self.t}',funcs={self.funcs},param={self.param},"
                f"ics={self.ics}")

    def add_t(self, x):
        r"""Add an independent variable for the set of equations.

        Args:
            x (str): Variable name.

        Returns:
            sympy.Symbol: Variable symbol.

        """
        if (self.t is None) and (x is not None):
            self.t = Symbol(x, **self.assumptions.get(x, {}))
            self.local_map[x] = self.t
            if self.t_units:
                self.units[self.t] = self.t_units
        return self.t

    def add_func(self, x):
        r"""Add a dependent variable for the set of equations.

        Args:
            x (str): Variable name.

        Returns:
            sympy.Symbol: Function symbol.

        """
        if isinstance(x, str):
            x_str = x
            if '(' not in x:
                # Assume that function depends on independent var
                x_str += f'({self.t})'
            x = sympify(x_str, locals=self.local_map)
        else:
            x_str = str(x)
        xf = x.__class__
        xfunc, xargs = x_str.split('(', 1)
        if (str(xf) != xfunc) or (xfunc in self.assumptions):
            xa = sympify('f(' + xargs, locals=self.local_map)
            xf = Function(xfunc, **self.assumptions.get(xfunc, {}))
            x = xf(*xa.args)
        v = str(x)
        if xf == getattr(sympy, str(xf), None):
            return v
        if x not in self.funcs:
            self.local_map[str(xf)] = xf
            self.local_map[v] = x
            self.funcs.append(x)
        return x

    def extract_derivatives(self, equation):
        r"""Get information about derivatives contained in the provided
        equation.

        Args:
            equation (str): Equation to extract derivatives from.

        Returns:
            list: Match dictionaries for the matched derivatives.

        """
        
        def match2dict(m):
            mdict = m.groupdict()
            iout = {'name': m.group(0),
                    'f': m.group('f'),
                    't': mdict.get('t', 't'),
                    'n': 1}
            iout['tval'] = mdict.get('args', iout['t'])
            if iout['tval']:
                iout['tval'] = iout['tval'].strip()
            if mdict.get('n_tics', None):
                iout['n'] = len(mdict['n_tics'])
            elif mdict.get('n_top', None) or mdict.get('n_bottom', None):
                assert(mdict['n_top'] == mdict['n_bottom'])
                iout['n'] = int(mdict['n_top'])
            return iout
            
        out = []
        for regex in self._derivative_regexes:
            regex = regex.replace('ARG', self._arg_regex)
            for m in re.finditer(regex, equation):
                out.append(match2dict(m))
        return out

    def check_t(self, eqn, t, subs=None):
        r"""Check that a function argument is either a constant or matches the
        independent variable from previously parsed equations.

        Args:
            eqn (str): Equation containing the independent variable being checked.
            t (str): Dependent variable to check against the existing one.
            subs (list, optional): Existing list that substitutions should be
                added to for constants.

        """
        if t and (t != str(self.t)):
            try:
                t = float(t)
                if self.t in self.units:
                    t = unyts.add_units(t, self.units[self.t])
                if isinstance(subs, list) and (len(subs) == 0):
                    subs.append((self.t, t))
                else:
                    return False
            except (TypeError, ValueError):
                raise ODEError(f"One equation ({eqn}) has a different "
                               f"independent variable ({t}) than "
                               f"other equations ({self.t})")
        return True
    
    def replace_derivatives(self, eqn, subs=None):
        r"""Replace derivative expressions with versions that sympy can
        parse.

        Args:
            eqn (str): Equation to be modified.
            subs (list, optional): Existing list that substitutions should be
                added to for constants.

        Returns:
            str: Modified equation.

        """
        replace_derivs = []
        for x in self.extract_derivatives(eqn):
            replace_derivs.append(x)
            self.add_t(x['t'])
        self.add_t('t')  # Fallback
        out = eqn
        for x in replace_derivs:
            self.add_func(x['f'])
            args = [f"{x['f']}({self.t})"] + x['n'] * [str(self.t)]
            replacement = f"Derivative({', '.join(args)})"
            if x['t'] != x['tval']:
                assert(self.check_t(eqn, x['t']))
            if not self.check_t(eqn, x['tval'], subs=subs):
                replacement += f".subs({self.t}, {x['tval']})"
            out = out.replace(x['name'], replacement)
        return out

    def replace_functions(self, eqn, subs=None):
        r"""Replace function expressions without forms with explicit
        functional dependence on the independent variable with versions that
        sympy can parse.

        Args:
            eqn (str): Equation to be modified.
            subs (list, optional): Existing list that substitutions should be
                added to for constants.

        Returns:
            str: Modified equation.

        """
        out = eqn
        for k, v in self.local_map.items():
            if isinstance(v, UndefinedFunction):
                func_regex = self._function_regex.replace('FUNC', k).replace(
                    'ARG', self._arg_regex)
                for m in reversed(list(re.finditer(func_regex, out))):
                    if self.check_t(eqn, m.group('args'), subs=subs):
                        out = (out[:m.start()]
                               + f"{k}({self.t})"
                               + out[m.end():])
                # Places where function name appears without arguments,
                # assuming (t) is implied
                func_regex = self._noarg_function_regex.replace('FUNC', k)
                for m in reversed(list(re.finditer(func_regex, out))):
                    out = (out[:m.start()]
                           + f"{k}({self.t})"
                           + out[m.end():])
        return out

    def sympify(self, x):
        r"""Convert an expression into a Sympy symbolic expression.

        Args:
            x (str): Expression.

        Returns:
            sympy.Expression: Symbolic expression.

        """
        subs = []
        out = self.replace_derivatives(x, subs=subs)
        out = self.replace_functions(out, subs=subs)
        out = sympify(out, locals=self.local_map)
        for a, b in subs:
            out = out.subs(a, b)
        return out

    def locate_unknown_symbols(self, x):
        r"""Locate symbols in the provided expression that are not existing
        parameters or independent/dependent variables.

        Args:
            x (sympy.Expression): Expression.

        Returns:
            list: Unregistered symbols from x.

        """
        out = []
        if isinstance(x, Symbol):
            if not ((x == self.t) or (x in self.funcs) or (str(x) in self.param)):
                out.append(x)
        for xx in x.args:
            out += self.locate_unknown_symbols(xx)
        return out

    def normalize_inputs(self, inputs):
        r"""Normalize model inputs, adding units as necessary and sorting out
        initial conditions. If there are units present for a variable that
        does not already have assigned units, they are added.
        
        Args:
            inputs (dict): Mapping of model inputs including dependent
                variables, parameters, and/or initial conditions where the
                keys are strings.
        
        Returns:
            dict: Mapping of model inputs where keys are symbols. Initial
                conditions are added to the 'ics' class member.

        """
        out = {}
        if inputs:
            for k, v in inputs.items():
                k0 = self.sympify(k)
                f, arg, _ = _get_function(k0)
                kt = k0
                if f:
                    kt = k0.subs(arg, self.t)
                if unyts.has_units(v):
                    if kt in self.units:
                        v = v.in_units(self.units[kt])
                    else:
                        self.units[kt] = unyts.get_units(v)
                if f:
                    self.ics[k0] = v
                    self.sol = None
                else:
                    out[k0] = v
        return out

    def complete_system(self):
        r"""Complete the system of equations by introducing dummy equations
        for missing derivatives."""
        nder = {}
        for x in self.eqns.keys():
            f, _, deg = _get_function(x)
            if deg:
                nder.setdefault(f, 0)
                nder[f] = max(nder[f], deg)
        subs = {}
        t = self.t
        for f, nmax in nder.items():
            for i in range(1, nmax):
                k = f(t).diff(t, i)
                if k not in self.eqns:
                    v = Function(f"{f}_d{i}")(t)
                    self.eqns[k] = Eq(k, v)
                    self.funcs.append(v)
                    self.local_map[str(v)] = v
                    k2 = f(t).diff(t, i + 1)
                    subs[k] = v
                    if k2 in self.eqns:
                        self.eqns[v.diff(t, 1)] = self.eqns.pop(k2)
        for k, v in subs.items():
            for f in list(self.eqns.keys()):
                if f != k:
                    self.eqns[f] = self.eqns[f].subs(k, v)
            for f in list(self.ics.keys()):
                self.ics[f.subs(k, v).doit()] = self.ics.pop(f)
            for f in list(self.units.keys()):
                self.units[f.subs(k, v).doit()] = self.units.pop(f)

    # Methods for solving ODE
    def __call__(self, compute_method, inputs, output_vars):
        r"""Find a solution.

        Args:
            compute_method (str): Method that should be used to find a solution.
            inputs (dict): A mapping of values for the independent variable,
                parameters, and/or dependent variables.
            output_vars (list): Variables that should be output.

        Returns:
            dict: Mapping between the names of independent variables and their
                value for the determined solution.

        """
        iparam = self.normalize_inputs(inputs)
        method_order = [{}, {'use_numeric': True}]
        if compute_method == 'steady_state':
            method_order.insert(1, {'from_roots': True})
        constants_changed = (
            (self.constants is None)
            or any(k in self.constants for k in inputs.keys()))
        sol = self.sol
        if (sol is None) or constants_changed:
            temp_solution = False
            if constants_changed:
                self.constants = {self.local_map[k]: v for k, v
                                  in self.param.items() if k not in inputs}
            first_attempt = constants_changed
            for kwargs in method_order:
                try:
                    sol = self.solve(compute_method,
                                     first_attempt=first_attempt, **kwargs)
                    break
                except NotImplementedError as e:
                    # Indicates Sympy could not find a symbolic solution
                    logger.info(f"Sympy raised NotImplementedError('{e}'). "
                                f"Another method will be tried.")
                except RetryODE as e:
                    temp_solution = temp_solution or e.temp_solution
                first_attempt = False
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
        out = {str(f.__class__): x for f, x in zip(self.funcs, result)}
        for v in output_vars:
            if v in self.funcs:
                continue
            else:
                iparam.update({f: x for f, x in zip(self.funcs, result)})
                out[v] = sol.evaluate(v, iparam, constants=self.constants)
        return out
        
    def solve(self, compute_method, use_numeric=False, from_roots=False,
              first_attempt=True):
        r"""Determine a solution and return a function form.

        Args:
            compute_method (str): Method that should be used to find a solution.
            use_numeric (bool, optional): If True, the solution will be found
                numerically. Defaults to False.
            from_roots (bool, optional): If True, the steady state solution
                will be found for solving for the equation roots. Defaults to
                False.
            first_attempt (bool, optional): If True, this is the first attempt
                at a solution and additional log messages will be emitted.
                Defaults to False.

        Returns:
            LambdifySolution: Solution that can be called to determine the
                value of variables for desired parameters.

        """
        if self.use_numeric:
            use_numeric = True
        derivs = {eqn.lhs: eqn.rhs for eqn in self.eqns.values()}
        if first_attempt:
            derivs_str = pprint.pformat({str(k): str(v) for k, v in derivs.items()})
            logger.info(f'SYMBOLIC ODE EQUATIONS:\n{derivs_str}')
        dsol = None
        kws = {}
        soltype = None
        if use_numeric:
            soltype = "NUMERIC"
            if compute_method == 'integrate':
                kws.update(ics=self.ics, method='odeint', **self.odeint_kws)
            elif compute_method == 'steady_state':
                kws.update(ics=self.ics, method='fsolve', **self.fsolve_kws)
            dsol = {}
        elif (compute_method == 'steady_state') and from_roots:
            soltype = "SYMBOLIC STEADY STATE"
            dsol = solve([Eq(self.eqns[f].rhs, sympify(0.0))
                          for f in self.funcs_deriv],
                         self.funcs, dict=True)
            if len(dsol) > 1:
                raise MultipleSolutionsError(
                    f"More than one symbolic solution for equation roots, "
                    f"retrying numerically: {dsol}")
            dsol = dsol[0]
        else:
            soltype = "SYMBOLIC"
            dsol = dsolve_system([self.eqns[f] for f in self.funcs_deriv],
                                 funcs=self.funcs, t=self.t, ics=self.ics)
            if len(dsol) > 1:  # pragma: debug
                raise MultipleSolutionsError(
                    f"There is more than one symbolic solution, "
                    f"retrying numerically: {dsol}")
            
            dsol = {eqn.lhs: eqn.rhs for eqn in dsol[0]}
            if compute_method == 'steady_state':
                kws = {'method': 'flimit', 'limits': {self.t: oo}}
        if dsol:
            dsol_str = {str(k): str(v) for k, v in dsol.items()}
            logger.info(f'{soltype} SOLUTION:\n{dsol_str}')
        sol = LambdifySolution(self.sympy_vars, derivs, dsol, self.funcs,
                               units=self.units, **kws)
        return sol


class LambdifySolution(object):
    r"""Callable solution to an ODE system of equations.

    Args:
        args (list): sympy.Symbol variables in the provided equations that
            are accepted as inputs to the solution function.
        sys (dict): Mapping between lhs & rhs in system of equations.
        sol (dict): Mapping between functions and solutions to sys.
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

    def __init__(self, args, sys, sol, funcs, ics=None, method=None,
                 units=None, **kws):
        self.t = args[0]
        self.args = args
        self.sys = sys
        self.sol = sol
        self.funcs = funcs
        self.ics = ics
        self.method = method
        self.units = units
        self.t_units = units.get(self.t, None)
        self.kws = kws
        self.is_numeric = (not bool(sol))
        if self.is_numeric:
            eqns = [sys[Derivative(f, self.t)] for f in funcs]
        else:
            eqns = [sol[f] for f in funcs]
        self.solution = self.lambdify(args, eqns, funcs)
        self.last_state = None
        self._expressions = {}

    def lambdified_expression(self, var):
        r"""Get a lambdified expression for a function or derivative."""
        if var in self._expressions:
            return self._expressions[var]
        expr = None
        if var in self.sys:
            expr = self.sys[var]
        elif var in self.sol:
            expr = self.sol[var]
        else:
            f, arg, deg = _get_function(var)
            if deg and (f in self.sol):
                expr = Derivative(self.sol[f], deg)
            elif deg and (Derivative(f, 1) in self.sys):
                expr = Derivative(self.sys[Derivative(f, 1)], deg - 1)
            else:
                raise ODEError(f"No expression could be found or derived "
                               f"for '{var}'")
        self._expressions[var] = self.lambdify(self.args, [expr], [var])
        return self._expressions[var]

    def evaluate(self, var, iparam, constants=None):
        r"""Evaluate for a specific function, parameter, variable."""
        iparam = dict(iparam)
        if constants:
            iparam.update(constants)
        if var in iparam:
            return iparam[var]
        elif self.ics and (var in self.ics):
            return self.ics[var]
        fexpr = self.lambdified_expression(var)
        return fexpr(*[iparam.get(k, None) for k in self.order])[0]

    def lambdify(self, args, expr, funcs):
        r"""Lambdify an expression, adding units to function arguments and
        return values."""
        args_units = [self.units.get(a, None) for a in args]
        funcs_units = [self.units.get(f, None) for f in funcs]
        fexpr = lambdify(args, expr)

        def flambdified(*iargs):
            iargs = [unyts.add_units(a, u)
                     if (u and not unyts.has_units(a) and (a is not None))
                     else a for a, u in zip(iargs, args_units)]
            out = fexpr(*iargs)
            out = [float(x) if isinstance(x, int) else x for x in out]
            out = [unyts.add_units(x, u)
                   if (u and not unyts.has_units(x)) else x
                   for x, u in zip(out, funcs_units)]
            return out

        return flambdified

    @property
    def order(self):
        r"""list: Order of arguments to the lambda function."""
        return [x for x in self.args]

    def get_t0(self):
        r"""Get the independent variable associated with the provided ICs."""
        t0 = None
        for v in self.ics.keys():
            _, tv, __ = _get_function(v)
            if t0 is None:
                t0 = tv
            else:
                assert(tv == t0)
        t0_f = t0
        if isinstance(t0, Number):
            # TODO: Check for non-float (e.g. complex)?
            t0_f = np.float64(t0)
        return t0, t0_f

    def _fodeint(self, t, X, args, t0):
        args = [t0 + t] + list(X) + list(args)
        return self.solution(*args)

    def odeint(self, iparam, from_prev=False, **kwargs):
        r"""Wrapper for calling scipy.integrate.odeint."""
        from scipy.integrate import ode, odeint
        if from_prev and (self.last_state is not None):
            t0_f, X0 = self.last_state
        else:
            t0, t0_f = self.get_t0()
            X0 = [self.ics[f.subs(self.t, t0)] for f in self.funcs]
        param = [iparam.get(k, None) for k in self.order]
        NX = len(X0) + 1
        tF = param[0]
        if tF == t0_f:
            out = X0
        elif 'name' in kwargs:
            x_ode = ode(self._fodeint)
            x_ode.set_integrator(**kwargs)
            x_ode.set_f_params(param[NX:], t0_f)
            x_ode.set_initial_value(X0, 0.0)
            out = x_ode.integrate(tF - t0_f)
        else:
            t = np.array([0.0, tF - t0_f])
            out = odeint(self._fodeint, X0, t, args=(param[NX:], t0_f),
                         tfirst=True, **kwargs)[-1]
            # x_ode = solve_ivp(self._fodeint, (t0_f, tF), X0,
            #                   args=(param[NX:], 0.0),
            #                   t_eval=np.array([tF]), **kwargs)
            # if not x_ode['success']:
            #     raise ODEError(f"Error in scipy.integrate.solve_ivp: "
            #                    f"'{x_ode['message']}'")
            # out = x_ode['y'][-1]
        self.last_state = (tF, out)
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
        out = []
        for f in self.funcs:
            x = self.sol[f]
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
        f = self.lambdify(tuple([]), out, self.funcs)
        return f()

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
                integrate: [DEFAULT] Compute the value(s) of the ODE solution
                    for the parameters/independent variable values received as
                    input.
                steady_state: Determine the steady state solution to the
                    ODE equations based on parameter values received as
                    input.
        independent_var (list, optional): Name of independent variable.
            Defaults to 't' if it cannot be inferred from the expression.
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
        odeint_kws (dict, optional): Keyword arguments that should be passed
            to scipy.integrate.odeint if it is called in integrating the
            equations numerically. If 'name' in present, scipy.integrate.ode
            will be used instead and these arguments will be passed to the
            set_integrator method. In addition, the following keywords are
            also supported:
              from_prev (bool, optional): If True, the integration should
                  always begin from the previous end state instead of starting
                  from the initial conditions (default behavior).
        fsolve_kws (dict, optional): Options that should be passed to the
            scipy fsolve routine when solving for the steady state solution if
            numeric integration is used (in the event that sympy cannot find
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
                    independent_var_units=None):
        r"""Get ODE solution using Sympy."""
        return ODEModel(equations, t=independent_var, funcs=dependent_vars,
                        ics=boundary_conditions, param=parameters,
                        assumptions=assumptions,
                        t_units=independent_var_units,
                        odeint_kws=odeint_kws, fsolve_kws=fsolve_kws,
                        use_numeric=use_numeric)

    @classmethod
    def model_wrapper(cls, env=None, working_dir=None, inputs=[],
                      outputs=[], compute_method='integrate',
                      integrator_settings={}, **kwargs):
        r"""Model wrapper."""
        if env is not None:
            os.environ.update(env)
        # Setup interface objects
        input_map, output_map = cls.setup_interface(
            inputs=inputs, outputs=outputs)
        input_vars = {}
        for v in input_map.values():
            if v['vars']:
                for k in v['vars']:
                    input_vars.setdefault(k, [])
                    input_vars[k].append(v)
            else:
                v['vars'] = None
        multiples = {k: [x['name'] for x in v]
                     for k, v in input_vars.items() if len(v) > 1}
        if multiples:  # pragma: debug
            raise ODEError(
                f"{len(multiples)} variables are coming from more than one "
                f"input channel:\n{pprint.pformat(multiples)}")

        def _set_input_vars(value, v):
            out = []
            for k in value.keys():
                if k not in input_vars:
                    input_vars[k] = [v]
                    out.append(k)
            return out
        
        # Determine symbolic equations via Sympy
        model = cls.setup_model(**kwargs)
        logger.info(f"MODEL: {model}")
        default_ovars = model.func_names
        output_vars = []
        for v in output_map.values():
            if not v.get('vars', None):
                v['vars'] = default_ovars
            output_vars += v['vars']
        output_vars = {k: model.sympify(k) for k in set(output_vars)}
        # Get static inputs
        input_vals0 = {}
        for k, v in input_map.items():
            if not v.get('outside_loop', False):
                continue
            flag, value = v['comm'].recv_dict(key_order=v['vars'])
            if not flag:  # pragma: debug
                raise RuntimeError(f"Error receiving from static input {k}")
            if not v['vars']:
                v['vars'] = _set_input_vars(value, v)
            for iv in v['vars']:
                input_vals0[iv] = value[iv]
        # Perform computations for each received input
        first_loop = True
        while True:
            flag = False
            # Receive input
            input_vals = copy.deepcopy(input_vals0)
            for k, v in input_map.items():
                if v.get('outside_loop', False):
                    continue
                flag, value = v['comm'].recv_dict(key_order=v['vars'])
                if not flag:
                    if first_loop:
                        raise RuntimeError(f"Error receiving from {k}")
                    logger.info(f"No more input from {k}")
                    break
                if not v['vars']:
                    v['vars'] = _set_input_vars(value, v)
                for iv in v['vars']:
                    input_vals[iv] = value[iv]
            if not flag:
                break
            # Compute output
            output_vals = model(compute_method, input_vals,
                                list(output_vars.values()))
            for k, v in output_vars.items():
                if v in output_vals:
                    output_vals[k] = output_vals[v]
            # Send output
            for k, v in output_map.items():
                iout = {iv: output_vals[iv] for iv in v['vars']}
                flag = v['comm'].send_dict(iout, key_order=v['vars'])
                if not flag:  # pragma: debug
                    raise RuntimeError(f"Error sending to {k}")
            first_loop = False

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
            args=['d^2f/dx^2=-9*f(x)'],
            kwargs={'independent_var': 'x',
                    'boundary_conditions': {'f(0)': 1.0}})
        return out
