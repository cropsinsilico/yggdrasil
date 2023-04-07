.. _units_rst:


Units
=====

Units are handled via language-specific libraries described blow with every
effort made to ensure that the same units are available in each by updating
the unit registries where needed. Units are specified via strings
associated with the units (usually the abbreviation; e.g.
``'cm'`` for centimeters or ``'umol'`` for micromoles). In addition, units can be
expressed as composites via symbolic arithmetic (e.g. ``'km/s'`` for kilometers
per second or ``'km**2'`` for square kilometer)

Schema Datatypes
----------------

The primary case where users will encounter units is within types associated
with model inputs and outputs in model specification YAML files. If a YAML
specifies a connection between a model output and input that do not have the
same units, |yggdrasil| will automatically perform the conversion from the
units of the sending model to the units of the receiving model. If the units
are not compatible, an error will be raised.

Units can be added to numeric scalars and arrays.

Language Specific Support
-------------------------

Python
~~~~~~

Backwards Compatibility
.......................

Prior to version 2.0, |yggdrasil| used `unyt <https://unyt.readthedocs.io/en/stable/>`_ for unit support in Python.
After 2.0, |yggdrasil| migrating to using a Python wrapped C++ units system based on unyt that is now used in C++ as well. |yggdrasil| still supports the use of unyt classes for backwards compatibility, but unyt class instances will be normalized to the analagous new classes during serialization by rapidjson.


Scalar Creation
...............

::
   
  >>> from yggdrasil.units import Quantity
  >>> x = Quantity(1., 'cm')
  >>> x
  Quantity(1., 'cm')
  >>> str(x)
  '1.0 cm'
  >>> str(x.units)
  'cm'
  >>> x.value
  1.0


Array Creation
..............

::
  
  >>> from yggdrasil.units import QuantityArray
  >>> import numpy as np
  >>> y = QuantityArray(np.ones(5), 'km/s')
  >>> y
  QuantityArray([1., 1., 1., 1., 1.], 'km*(s**-1)')
  >>> str(y)
  '[1. 1. 1. 1. 1.] km*(s**-1)'
  >>> str(y.units)
  'km*(s**-1)'
  >>> y.value
  array([1., 1., 1., 1., 1.])


Arithmetic
..........

Any operations possible in Python with scalars or numpy arrays will also be possible with Quantity or QuantityArray objects.::

   >>> x *= 5
   >>> x
   Quantity(5., 'cm')
   >>> y / x
   Quantity([20000., 20000., 20000., 20000., 20000.], 's**-1')
   >>> x + 1
   UnitsError: Incompatible units: '' and 'cm'
   >>> x + Quantity(1, 'm')
   Quantity(105., 'cm')
   >>> x ** 2
   Quantity(25., 'cm**2')
   >>> x % 2
   Quantity(1., 'cm')

   
Additional Methods
..................

For backwards compat, units in python can also be added to numeric types (or retrieved) using several methods from
the |yggdrasil| units submodule::

  >>> from yggdrasil import units
  >>> import numpy as np
  >>> x = units.add_units(1.0, 'cm')
  >>> x
  Quantity(1., 'cm')
  >>> units.get_units(x)
  'cm'
  >>> units.get_data(x)
  1.0
  >>> y = units.add_units(np.ones(5), 'km/s')
  >>> y
  QuantityArray([1., 1., 1., 1., 1.], 'km*(s**-1)')
  >>> units.get_units(y)
  'km*(s**-1)'
  >>> units.get_data(y)
  array([1., 1., 1., 1., 1.])


C++
~~~

Scalar Creation
...............

::

   #include <iostream>
   #include "YggInterface.hpp"
   rapidjson::units::Quantity<double> x(1.0, "cm");
   std::cout << "x = " << x << std::endl;

Output: ::

   x = 1 cm

   
Array Creation
..............

::
  
   #include <iostream>
   #include "YggInterface.hpp"
   double arr[5] = {1.0, 1.0, 1.0, 1.0, 1.0};
   rapidjson::units::QuantityArray<double> y(arr, "km/s");
   std::cout << "y = " << y << std::endl;

Output: ::

   y = [1.0, 1.0, 1.0, 1.0, 1.0] cm


C Language
~~~~~~~~~~

Units in C are inplmeented by wrapping the C++ unit classes as generic objects.

Scalar Creation
...............

::

   #include "YggInterface.h"
   generic_t x;
   generic_set_double(x, 1.0, "cm");
   printf("x = ");
   display_generic(x);
   printf("\n");

Output: ::

  x = 1 cm

Array Creation
..............

::
  
   #include "YggInterface.h"
   generic_t y;
   printf("x = ");
   double arr[5] = {1.0, 1.0, 1.0, 1.0, 1.0};
   generic_set_1darray_double(y, arr, 5, "cm");
   display_generic(y);
   printf("\n");

Output: ::

   y = [1.0, 1.0, 1.0, 1.0, 1.0] cm


..
   Fortran
   ~~~~~~~

   Scalar Creation
   ...............

   ::

      use fygg
      type(ygggeneric) :: x
      call generic_


R Language
~~~~~~~~~~

In R, units are represented via the `units <https://cran.r-project.org/web/packages/units/index.html>`_ package. Details on adding units to quantites in R can be found `here <https://cran.r-project.org/web/packages/units/vignettes/units.html>`_.


MATLAB
~~~~~~

In MATLAB, units are represented via `symbolic units <https://www.mathworks.com/help/symbolic/units-of-measurement.html?s_tid=CRUX_lftnav>`_ if the ``YGG_MATLAB_SYMUNIT`` environment variables is set to ``true``, othwerise the value is passed to MATLAB without the units. Details on adding units to quantaties in MATALB can be found `here <https://www.mathworks.com/help/symbolic/units-conversion.html>`_.


Julia
~~~~~

In Julia, units are represented via the `Unitful <https://painterqubits.github.io/Unitful.jl/stable/>`_ package. Details on adding units to quantaties in Julia can be found `here <https://painterqubits.github.io/Unitful.jl/stable/newunits/>`_.

