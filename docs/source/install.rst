############
Installation
############

Basic Installation
------------------

..todo:: Links to PyPI release

|cis_interface| can be installed from either PyPI using ``pip``::

  $ pip install cis_interface

or by cloning the `Git <https://git-scm.com/>`_ repository on
`Github <https://github.com/cropsinsilico/cis_interface>`_::

  $ git clone https://github.com/cropsinsilico/cis_interface.git

and then building the distribution.::

  $ cd cis_interface
  $ python setup.py install

If you do not have admin privileges on the target machine, ``--user`` can be
added to either the ``pip`` or ``setup.py`` installation commands.


Additional Steps for Matlab Models
----------------------------------

To run Matlab models, you will also need to install the Matlab engine for 
Python. This requires that you have an existing Matlab installation and license.

Instructions for installing the Matlab engine as a python package can be found
`here <https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html>`_.


Additional Steps for RabbitMQ Message Passing
---------------------------------------------

RabbitMQ connections allow messages to be passed between models when the
models are not running on the same machine. To use these connections
(those with the prefix 'RMQ'), the framework must have access to a
RabbitMQ server. If you have access to an existing RabbitMQ server,
the information for that server can either be provided to the
RabbitMQ connection driver
(See :class:`cis_interface.drivers.RMQDriver.RMQDriver`) or added
to the cis_interface config file (See
`Configuration Options <config.rst>`__ for information on setting
config options).

Starting a local RabbitMQ Server is also relatively easy. Details on
downloading, installing, and starting a RabbitMQ server can be found
`here <https://www.rabbitmq.com/download.html>`_. The default values
for RabbitMQ related properties in the config file are set to the defaults
for starting a RabbitMQ server.
