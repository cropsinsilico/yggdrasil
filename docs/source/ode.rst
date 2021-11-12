.. _ode_rst:

Symbolic ODE Models
===================

|yggdrasil| allows models consisting of ordinary differential equations (ODEs) to be specified symbolically in the YAML file itself (or in a separate file). |yggdrasil| uses `SymPy <https://www.sympy.org/en/index.html>`_ to represent the equations symbolically and will attempt to use SymPy to solve the equations symbolically. If SymPy cannot find a symbolic solution, |yggdrasil| will use `scipy <https://scipy.org/>`_ routines to find numeric solutions. Equations can be expressed in any syntax accepted by SymPy, may include dependent variables without the functional form, and have derivatives expressed in the form of ``d^nf/dt^n`` or ``f'(t)``. ODE models can take as input values for the independent variable, equation parameters, or initial conditions; output values can include values for the dependent variables, derivatives, equation parameters, or initial conditions, but will default to the dependent variables unless otherwise specified.

The model parameters that can be used to control the model behavior are specified in the table below:

.. include:: tables/class_table_ODEModelDriver_args.rst

For example, the YAML below defines a model from a system with one ODE equation that can be solved symbolically. The model can take as input ``t`` (the independent variable, units of ``hr``), the parameter ``A`` (units of ``hr**-2``), and/or the initial condition ``f(0)`` (units of ``kg``), and returns as output the value of ``f(t)`` (units of ``kg``) for each set of input parameters (the default behavior). If other variables are desired in the output (e.g. parameters or derivatives), they can be specified via the ``vars`` option for the model output definition.

.. include:: examples/ode1_yml.rst

Numeric Integration
-------------------
	     
If the equations cannot be solved symbolically (or ``use_numeric`` is ``true``), they will be solved numerically. For example, the ODE defined in the YAML shown below cannot be solved symbolically, and ``scipy.integrate.odeint`` (or ``scipy.integrate.ode`` if an integrator were specified via ``odeint_kws``) is used to determine the value of the dependent variables at the timesteps received from the ``input`` channel for the parameters set in the YAML and received from the ``param`` channel.

.. include:: examples/ode2_yml.rst

Steady State Solution
---------------------

By default, |yggdrasil| will solve/integrate the equations to a desired value for the independent variable using the specified parameters, but it can also return the steady-state solution for an equation by setting ``compute_method`` to ``steady_state`` as in the YAML below. The is useful for evaluating steady-state models under different parameters or initial conditions.

.. include:: examples/ode3_yml.rst

When possible, |yggdrasil| will use SymPy to symbolically solve for time dependent solution to the system of ODEs and then take the limit as the independent variable goes to infinity. If a solution cannot be found symbolically, or the limit cannot be taken symbolically, |yggdrasil| will try the following methods to solve for the steady state solution (e.g. ``dx/dt = 0``) directly:

#. Solve the system of ``dx/dt = 0`` equations symbolically
#. Solve the system of ``dx/dt = 0`` equations numerically using ``scipy.optimize.fsolve``
	     
Units
-----

Units can be attached to any variable in the equations by adding them to the values in the YAML or in the received messages. Units on boundary condition value will be used to set the units for independent variables. The identified units will be propagated through the equation when solving for outputs.

Special Symbols
---------------

For the most part, |yggdrasil| can infer which symbols in the equations should be parameters, dependent variables, or the independent variable, but sometimes it is necessary to provide some direction as `some symbols <https://docs.sympy.org/latest/modules/functions/special.html>`_ have a special meaning to SymPy and will be interpreted as such unless otherwise directed. If you would like to use one as a parameter or variable in an equations, be sure to explicitly specify it in the YAML under the ``parameters``, ``independent_var``, or ``dependent_vars`` option as in the :ref:`ode2` example which includes and ``E1`` parameter that conflicts with SymPy's `E1 generalized exponential integral <https://docs.sympy.org/latest/modules/functions/special.html#sympy.functions.special.error_functions.E1>`_.

Assumptions
-----------

The ``assumptions`` parameter allows you to place constraints on the variables in the equations that may assist in finding a symbolic solution. For example, the YAML below constrains the equation parameters ``m``, ``k``, & ``b`` to be positive and the dependent variable ``y`` to be a real number. These constraints make in possible for SymPy to solve the equations symbolically.

.. include:: examples/ode4_yml.rst

A list of supported assumptions can be found `here <https://docs.sympy.org/latest/modules/core.html#module-sympy.core.assumptions>`_.
