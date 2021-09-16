.. _remote_rst:


Running Integrations as Services
================================

In release 1.7.1, the ability to run models as services that can be accessed by integrations running on remote machines was added to |yggdrasil|. This feature allows models (or sets of models) to be exposed for external use without the need to have the model source code or install it on your local machine. It is intended to make it easier for scientists to share models and foster collaboration. Future releases will include tools for exploring remote models & integrations via visualizations.

Setting Up an Integration as a Service
--------------------------------------

Host Requirements
~~~~~~~~~~~~~~~~~

* |yggdrasil| must be installed
* A port must be available that can be used to serve a Flask REST API. The port should be either set via the ``--port`` flag to the ``integration-service-manager start`` command (last requirement) or in the ``PORT`` environment variable before starting the service manager.
* The URL that will be used by remote integrations to contact the service manager must be specified either via the ``--remote-url`` flag to the ``integration-service-manager start`` command (last requirement) or in the ``YGGDRASIL_SERVICE_HOST_URL`` environment variable before starting the service manager.
* The integrations that will be requested must be located on the host machine (including YAMLs and source code) and must be registered as services (see below).
* A |yggdrasil| service manager must be started via::

    $ yggdrasil integration-service-manager [--port PORT] start [--remote-url REMOTE_URL]

  Since the service manager must continue running, in many cases, you will want to start it as a background process.

.. note::

   For convenience, there are Docker images available that launch the service manager as a web application using `gunicorn <https://gunicorn.org/>`_. See the documentation :ref:`here <service_docker_rst>` for additional details about the Docker images and how to use them.

Registering Integrations
~~~~~~~~~~~~~~~~~~~~~~~~

In order for an integration to be run on the host machine, it must first be registered via |yggdrasil|'s ``integration-service-manager`` CLI. Usage is::

  $ yggdrasil integration-service-manager register <integration-name> <integration-yamls ...>

``integration-name`` is a unique name that will be allocated with the integration and used in requests to connect to or query the status of the integration service. ``integration-yamls`` is one ore more YAML specification files defining the integration. Any inputs or outputs that are not connected to another model or file in the YAML, will be available for connection by remote models.

For example, to register the photosynthesis model from the :ref:`fakeplant example <fakeplant_rst>`, we would run::

  $ yggdrasil integration-service-manager register photosynthesis yggdrasil/examples/fakeplant/photosynthesis.yml

When a remote integration connects to the service manager and requests the ``photosynthesis`` integration service, the model will be started and channels will be opened to its inputs (``light_intensity``, ``temperature``, ``co2``) and outputs (``photosynthesis_rate``). The remote integration can make connections to these channels in the same way it would if the ``photosynthesis`` model (and it's YAML) were part of the integration.

.. note::

   For security, YAML files located in remote Git repositories will not be allowed as part of integrations that the service manager runs.


Registering Multiple Integrations at Once
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To save time, |yggdrasil| also allows you to register multiple integrations at once from a YAML file containing a set of mappings between integration names and the YAML specification files defining them. The example services file below defines two integrations, each specified by one YAML file.

.. code-block:: yaml

   photosynthesis:
     - yggdrasil/examples/fakeplant/photosynthesis.yml
   rpcFibSrv:
     - yggdrasil/examples/rpcFib/rpcFibSrv_c.yml

To register all of the integrations contained in this file, you would run::
  
  $ yggdrasil integration-service-manager register SERVICES_FILE

where ``SERVICES_FILE`` is the full path to the file.


Connecting an Integration to a Remote Service
---------------------------------------------

Client Requirements
~~~~~~~~~~~~~~~~~~~

* |yggdrasil| must be installed
* You must be able to connect to the remote host's service manager. You can check the status via::

    $ yggdrasil integration-service-manager --address ADDRESS status

  The ``ADDRESS`` field is required and must be the URL for the service manager (i.e. the value set in ``YGGDRASIL_SERVICE_HOST_URL`` or via ``--remote-url`` in the command to start the service manager).
  
Service YAML Entry
~~~~~~~~~~~~~~~~~~

Integrations can connect to remote integration services by including ``service`` entries in the YAML integration specification files. For example, the entry below requests the ``photosynthesis`` integration service from the |yggdrasil| flask service manager located at http://remote_service_manager_url/.

.. code-block:: yaml

   service:
     name: photosynthesis
     type: flask
     address: http://remote_service_manager_url/

This service entry is treated as a placeholder for the ``photosynthesis`` YAML entry. As such, it can be directly swapped for the ``photosynthesis.yml`` file in running the ``fakeplant`` example assuming that all of the other models are locally available. For example, if the service entry were saved to ``photosynthesis_service.yml``, we could run the ``fakeplant`` example, but using the remote copy of the ``photosynthesis`` model via::

  $ yggrun canopy.yml light.yml photosynthesis_service.yml growth_python.yml fakeplant.yml

Multiple services can also be included in the same entry. For example, if there were a ``growth`` service as well that should be used instead of the local ``growth`` model in the ``fakeplant`` example, the YAML entry above would be updated to

.. code-block:: yaml

   services:
     - name: photosynthesis
       type: flask
       address: http://remote_service_manager_url/
     - name: growth
       type: flask
       address: http://another_remote_service_manager_url/


Performance
-----------

It is important to keep in mind that connecting to remote integrations over an internet connection introduces a great deal of overhead and a certain degree of fragility into integrations that is not present when all models are running locally. Such connections between models make integrations dependent on the speed and reliability of the internet connection both at the host and client. If performant and stable communication times are import for your use case, we advise looking for a way to run the integrations locally.
