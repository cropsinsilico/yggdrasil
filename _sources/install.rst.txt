############
Installation
############

Basic Installation
------------------

..todo:: Links to PyPI release

|cis_interface| can be installed from either PyPI using ``pip``::

  $ pip install cis_interface

or by cloning the `Git <https://git-scm.com/>`_ repository on `Github <https://github.com/cropsinsilico/cis_interface>`_::

  $ git clone https://github.com/cropsinsilico/cis_interface.git

and then building the distribution.::

  $ cd cis_interface
  $ python setup.py install

If you do not have admin privileges on the target machine, ``--user`` can be added to either the ``pip`` or ``setup.py`` installation commands.


Additional Steps for Matlab Models
----------------------------------

To run Matlab models, you will also need to install the Matlab engine for 
Python. This requires that you have an existing Matlab installation and license.

Instructions for installing the Matlab engine as a python package can be found
`<here <https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html>`_.


Additional Steps for RabbitMQ Message Passing
---------------------------------------------
