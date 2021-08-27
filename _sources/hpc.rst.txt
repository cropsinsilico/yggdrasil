.. _hpc_rst:


High Performance Computing (HPC)
================================

As of version 1.7, |yggdrasil| includes support for running integrations (networks of models) on High Performance Computing (HPC) clusters via MPI (either `OpenMPI <https://www.open-mpi.org/>`_ or `MPICH <https://www.mpich.org/>`_) and `mpi4py <https://mpi4py.readthedocs.io/en/stable/>`_. |yggdrasil| will distribute models in an integration evenly amongst the available processes and coordinate message passing between them.

You can run a |yggdrasil| integration using MPI, by passing the usual ``yggrun`` command to ``mpiexec/mpirun/srun`` e.g.::

  $ mpiexec -n 2 yggrun model1.yml model2.yml

Setup
-----

To run an integration using |yggdrasil|, you must be able to install |yggdrasil| on the cluster. The existing packages and permissions of the cluster will determine how |yggdrasil| should be installed.

* If conda is already installed on the target cluster, you can install |yggdrasil| directly into an environment of your choosing. If the target cluster uses a package manager, you may need to activate/load the conda installation.::

    $ conda install -c conda-forge yggdrasil

* If conda is not installed, you can install miniconda into your home directory (which you should have permission for) via a login node and then install |yggdrasil| via conda (you may need to log out and back in before using conda for the first time). e.g.::

    $ wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    $ bash miniconda.sh -b -p $HOME/miniconda export PATH="$HOME/miniconda/bin:$PATH"

* If conda is not installed and you cannot install conda due to limitations on packages for cluster users, but Python and pip are installed, you can install |yggdrasil| via pip as a user package. If the target cluster uses a package manager, you may need to activate/load a Python installation (version 3.6 or higher). You will need to complete additional installation steps for non-Python languages as described for the normal :ref:`pip-based installation <manual_install_rst>`::

    $ python -m pip install yggdrasil-framework --user


Writing the Job Script
----------------------

Many of the specifics of how you would set up your job script will depend on the scheduler used by the cluster you are targeting (e.g. SLURM, Torque), but there are some general tips:

* Make sure that the YAML files defining the integration and the model codes are located in a directory accessible on compute nodes (usually your home directory or a dedicated drive).
* Activate/load packages you will need that are provided by the cluster package manager (e.g. conda, Python, MPI).
* If you used conda to install |yggdrasil|, activate the environment that |yggdrasil| was installed in before calling ``mpiexec/mpirun/srun``.

Example SLURM Job Script
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: slurm

   #!/bin/bash
   #SBATCH --partition=general
   #SBATCH --job-name=example_name
   #SBATCH --cpus-per-task 4
   #SBATCH --ntasks=4
   #SBATCH --mem-per-cpu=500MB

   module load miniconda

   conda activate env_name

   mpiexec -np $SLURM_NTASKS yggrun model1.yml model2.yml > output.txt
