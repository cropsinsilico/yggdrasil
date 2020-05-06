.. _timesync_io_rst:

Timestep Synchronization
========================

Many models are time dependent with variables being updated as the time is incremented. When integrating two (or more) models that have timestep's, care must be taken to ensure that variables are correctly synchonized between the models at each timestep. To aid in this process |yggdrasil| provides a special timestep synchronization interface.

In the example below, two model are initialized from the same source code. Both models have two state variables (``x`` and ``y``) that are calculated as a sine and cosine with periods of 10 days and 5 days respectively; the two models differ only in the size of their timesteps and the units that they use to represent time (the timestep and units for each model are set by input arguments to the model as passed in the yaml).

In the yaml file below, the models are defined as usual, but they also have the ``timesync`` set to ``True``. Setting the ``timesync`` parameter to ``True`` tells |yggdrasil| that the model has time dependent variables that need to be synchonized. If there are any models with ``timesync = True``, |yggdrasil| sets up a third model behind the scene's to handle synchronization between the models with the parameter.

.. include:: examples/timesync1_io_yml.rst


In addition to the yaml parameter, models performing timestep synchonization will need to make use of the timestep interface. In Python, this is ``YggTimestep``. At each timestep (including the initial time), the model then calls the ``call`` method for the timestep interface. The output variable (the variable being sent as a request by the ``call`` method) is excepted to be the time of the timestep and a mapping type between state varaible names and their values at the timestep. The return variable (the variable received in response by the ``call`` method) will be a mapping type between state variable names and their values that have been updated with information from the other models.
	     
.. include:: examples/timesync1_io_src.rst


Controlling Synchonization
--------------------------

.. include:: examples/timesync2_io_src.rst


.. include:: examples/timesync2_io_yml.rst

Synonyms (Conversion)
~~~~~~~~~~~~~~~~~~~~~

Interpolation
~~~~~~~~~~~~~

Aggregation
~~~~~~~~~~~


In addition to dictionaries mapping from variable to method, a single value can be provided for the ``aggregation`` and ``interpolation`` parameter; the same method will the be used for all of the variables e.g.::
  
  - name: statesync
    language: timesync
    synonyms:
      x: [xvar, timesync:xvar2x, timesync:x2xvar]
      y: yvar
    aggregation: min
    interpolation: nearest
