.. _docker_rst:


Docker Containers
=================

For convenience, |yggdrasil| provides `Docker <https://www.docker.com/>`_ images and tools for building Docker images. To get started using these images, you will need to do a few things first.

#. **Download and install docker** from `here <https://docs.docker.com/get-docker/>`_.
#. **Sign-up for DockerHub** `here <https://hub.docker.com/>`_, start docker, and sign-in using your docker hub credentials (either via the desktop app or the `command line <https://docs.docker.com/engine/reference/commandline/login/>`_).

Release Images
--------------

For each tagged release of |yggdrasil|, a Docker image will be published to the ``cropsinsilico/yggdrasil`` `DockerHub repository <https://hub.docker.com/repository/docker/cropsinsilico/yggdrasil>`_.

After installing Docker, you can pull the latest release image by running::

  $ docker pull cropsinsilico/yggdrasil

or if you need a specific version, ``[VER]``::

  $ docker pull cropsinsilico/yggdrasil:v[VER]

You can then run the image as an interactive container::

  $ docker run -it cropsinsilico/yggdrasil

If you pulled a specific version, include the version tag in the run command (e.g. ``docker run -it cropsinsilico/yggdrasil:v[VER]``).

This will start a container using the image and will open a command prompt with container access. You can run |yggdrasil| commands from this prompt. If you would like to run an integration that uses models from your local machine, you will need to mount the model directory as a volume when you launch the container. For example, if you have a model contained in the directory ``/path/to/model``, then you can mount the model as a volume in the container under the directory ``/model_vol`` via::

  $ docker run -it --volume=/path/to/model:/model_vol cropsinsilico/yggdrasil

You will then be able to access the model from inside the container and can run integrations using that model.

.. note::

   If the directory being mounted is not in the directory that the ``docker run`` command is being issued from, the path will need to be absolute.
  

Executable Images
-----------------

In addition to release images, an executable image will be published for each tagged release of |yggdrasil|. Executable images will be published to the ``cropsinsilico/yggdrasil-executable`` `DockerHub repository <https://hub.docker.com/repository/docker/cropsinsilico/yggdrasil-executable>`_ and can be pulled via::

  $  docker pull cropsinsilico/yggdrasil-executable

Executable images are different than the release images in that they are meant to be treated as an executable and can be used to run integrations using |yggdrasil| without opening the container command line. Running the image without any arguments will display the help for the ``yggrun`` CLI.::

  $ docker run -it cropsinsilico/yggdrasil-executable

YAML specification files (and any other ``yggrun`` flags) can be passed to this command to run an integration. If they are not located in a Git repository (see :ref:`this discussion <git_models_rst>` for a discussion of using repo-base models), then they must be added to the container via a mounted volume and the path provided to the command should be relative to the directory that the volume is mounted at in the container.

For example, if you want to use a YAML, ``/path/to/model/model.yml`` that uses models in the ``/path/to/model/`` directory, you would add the directory containing the YAML as a volume and call the executable with YAML as input as follows::

  $ docker run -it --volume=/path/to/model/:/model_vol cropsinsilico/yggdrasil-executable /model_vol/model.yml

For convenience, you can also download/copy the Python script located `here <https://github.com/cropsinsilico/yggdrasil/blob/main/utils/run_docker.py>`_, which allows you to just specify the paths to the YAMLs and any other ``yggrun`` options (it will set the volumes based on the directories containing the YAMLs). The above example would then be::

  $ python run_docker.py /model_vol/model.yml

In addition, this script allows the paths to the YAMLs to be relative rather than absolute and, if passed the ``--pull-docker-image`` flag, it can pull the latest executable image before running it.

.. _service_docker_rst:

Service Images
--------------

|yggdrasil| also provides images that run |yggdrasil|'s :ref:`integration service manager <remote_rst>` as a web application. As the service images do not contain any services by default, these images are best used as bases for building your own Docker image that copies in a file containing a mapping of integrations that should be exposed as services and those directories containing models.

For example, if you have a services file ``services.yml`` that defines two integrations.

.. code-block:: yaml

   foo:
     - foo/model.yml
   bar:
     - bar/modelA.yml
     - oth/modelB.yml

Then the Dockerfile that will be able to run those services is

.. code-block:: docker

   FROM cropsinsilico/yggdrasil-service:v1.8.0
   COPY services.yml .
   COPY foo ./foo
   COPY bar ./bar
   COPY oth ./oth

After building, the new Docker image (e.g. ``docker build -t my-yggdrasil-service .``), the app is started by running the image, taking care to set the port that will be used by the app via an environment variable::

  $ docker run --env PORT=5000 my-yggdrasil-service

The port that should be used in production will be determined by the host machine (e.g. a port exposed on a cloud resource). Such derived Docker images are also suitable for deployment via the `Heroku <https://www.heroku.com/>`_ platform (see `this <https://devcenter.heroku.com/articles/container-registry-and-runtime>`_ tutorial on registering Docker images with Heroku).

.. note::

   The |yggdrasil| service manager application automatically looks for a ``services.yml`` file in the ``WORKDIR`` for the container at startup. If you put the file in another location or give it another name, you will need to set the ``INTEGRATION_SERVICES`` environment variable for the container to the file's path.

.. note::

   For security, YAML files located in remote Git repositories will not be allowed as part of integrations that the service manager runs; such repositories should be cloned in the Docker image instead.


Development Images
------------------

Occasionally during development it may be necessary for the |yggdrasil| team to create images for specific commits. These will be published to the ``cropsinsilico/yggdrasil-dev`` `DockerHub repository <https://hub.docker.com/repository/docker/cropsinsilico/yggdrasil-dev>`_. If you know that such an image exists for a commit with the ID string ``[COMMIT]``, you can pull it via::

  $ docker pull cropsinsilico/yggdrasil-dev:[COMMIT]

Such images operate in the same fashion as the release images described above and can be run in the same manner.


Building New Images
-------------------

The ``utils/build_docker.py`` from the |yggdrasil| repository can be used to build/push new Docker images.


To build a new Docker image containing the tagged release, ``RELEASE``, run::

  $ python utils/build_docker.py --release RELEASE

To build a new Docker image containing commit, ``COMMIT``, run::

  $ python utils/build_docker.py --commit COMMIT

If you add the ``--push`` flag to either of these commands, the image will be pushed to DockerHub after it is built. If you add the ``executable`` argument, the image will be built such that it exposes the |yggdrasil| CLI and can be used as an executable image in the way described above. If you add the ``service`` argument, a service image with the specified release/commit will be built.
