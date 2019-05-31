.. _units_rst:


Units
=====

Units are handled via the `unyt <https://unyt.readthedocs.io/en/stable/>`_
package in Python >=3 and via `pint <https://pint.readthedocs.io/en/0.9/>`_
in Python 2. In both cases, units are specified via strings
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

Python Objects
--------------

In Python, units can be added to numeric types (or retrieved) using the
|yggdrasil| units submodule which wraps the particular behavior of the
underlying packages. Using unyt::

  >>> from yggdrasil import units
  >>> x = units.add_units(1.0, 'cm')
  >>> x
  unyt_quantity(1., 'cm')
  >>> units.get_units(x)
  'cm'
  >>> units.get_data(x)
  1.0

or using pint::

  >>> from yggdrasil import units
  >>> x = units.add_units(1.0, 'cm')
  >>> x
  1.0 <Unit('centimeter')>
  >>> units.get_units(x)
  'centimeter'
  >>> units.get_data(x)
  1.0

