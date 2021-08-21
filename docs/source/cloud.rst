.. _remote_rst:


Running Integrations as Remote Services
=======================================

In release 1.7, the ability to run models as services that can be accessed by integrations running on remote machines was added to |yggdrasil|.


Setting Up an Integration as a Service
--------------------------------------

Host Requirements
~~~~~~~~~~~~~~~~~

* |yggdrasil| must be installed
* A port must be available that can be used to serve a Flask REST API
  [TODO: How to specify the port that should be used]
* The integrations that will be requested must be located on the host machine and must be registered as services (see below).
* A |yggdrasil| service manager must be started via::

    $ yggdrasil integration-service-manager start

  Since the service manager must continue running, in many cases, you will want to start it as a background process.

Registering Models
~~~~~~~~~~~~~~~~~~

In order for an integration to be run on the host machine, it must first be registered via |yggdrasil|'s ``integration-service-manager`` CLI. Usage is::

  $ yggdrasil integration-service-manager register <integration-name> <integration-yamls ...>

``integration-name`` is a unique name that will be allocated with the integration and used in requests to connect to or query the status of the integration service. ``integration-yamls`` is one ore more YAML specification files defining the integration. Any inputs or outputs that are not connected to another model or file in the YAML, will be available for connection by remote models.


Connecting an Integration to a Remote Service
---------------------------------------------
