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
  

Executable Images
-----------------

In addition to release images, an executable image will be published for each tagged release of |yggdrasil|. Executable images will be published to the ``cropsinsilico/yggdrasil-executable`` `DockerHub repository <https://hub.docker.com/repository/docker/cropsinsilico/yggdrasil-executable>`_ and can be pulled via::

  $  docker pull cropsinsilico/yggdrasil-executable

Executable images are different than the release images in that they are meant to be treated as an executable and can be used to run integrations using |yggdrasil| without opening the container command line.

TODO


Development Images
------------------

Occasionally during development it may be necessary for the |yggdrasil| team to create images for specific commits. These will be published to the ``cropsinsilico/yggdrasil-dev`` `DockerHub repository <https://hub.docker.com/repository/docker/cropsinsilico/yggdrasil-dev>`_. If you know that such an image exists for a commit with the ID string ``[COMMIT]``, you can pull it via::

  $ docker pull cropsinsilico/yggdrasil-dev:[COMMIT]

Such images operate in the same fashion as the release images described above and can be run in the same manner.


Building New Images
-------------------

The ``utils/build_docker.py`` from the |yggdrasil| repository can be used to build/push new Docker images.


To build a new Docker image containing the tagged release, ``RELEASE``, run::

  $ python utils/build_docker.py release RELEASE

To build a new Docker image containing commit, ``COMMIT``, run::

  $ python utils/build_docker.py commit COMMIT

If you add the ``--push`` flag to either of these commands, the image will be pushed to DockerHub after it is built. If you add the ``--executable`` flag, the image will be built such that it exposes the |yggdrasil| CLI and can be used as an executable image in the way described above.
