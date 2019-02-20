
Release Steps
=============

#. [on branch/fork] Make code changes adding desired feature(s).
#. [on branch/fork] Run tests locally.::

   $ cistest -svx --nologcapture

#. [on branch/fork] Regenerate schema if you added any new components (there will be an erorr in the tests if you need to regenerate the schema).:: 

   $ cisschema
   $ git add cis_interface/.cis_schema.yml
   $ git commit -m "Updated .cis_schema.yml"
   $ git push origin [BRANCH]

#. [on branch/fork] Make sure all CI tests pass (`travis <>`_, `appveyor <>`_).::
#. [on branch/fork] Update docs to reflect new features and make sure they build locally::

   $ cd docs
   $ make autodoc

#. [on branch/fork] Test conda-forge recipe locally using steps below.
#. [on branch/fork] Open pull request to merge changes into master
#. Merge branch into master after tests pass and code review complete
#. Create tag with new version on master::

   $ git tag x.x.x
   
#. Push to github. Pushing a tag will trigger travis testing of the conda build recipe in the |cis_interface| repository (under recipe) and, on success, the deployment of source distribution and wheels to PyPI.::

   $ git push; git push --tags

#. If there are any errors, make updates to the repo/recipe as necessary, delete the tag (provided it has not deployed to PyPI) and push it again.::

   $ git tag -d x.x.x
   $ git push origin :refs/tags/x.x.x
   $ git tag x.x.x
   $ git push; git push --tags
   
#. Once the source distribution has been uploaded to PyPI, update the conda-forge recipe on the cropsinsilico feedstock fork `here <https://github.com/cropsinsilico/cis_interface-feedstock>`_ with the changes from the |cis_interface| source repository, the new version, and the SHA256 for the release (this can be found `here <https://pypi.org/project/cis-interface/#files>`_) and create a pull request to merge the changes into the `conda-forge <https://github.com/conda-forge/cis_interface-feedstock>`_ feedstock.
#. Checkout ``gh-pages`` branch if it dosn't already exist (See below), regenerate docs and push to gh-pages branch::

   $ cd docs
   $ make ghpages


Updating and Testing the Conda Recipe
=====================================

#. Install ``conda-build`` if you don't already have it.::
     
   $ conda install conda-build

#. Update the recipe (``recipe/meta.yaml``) to reflect any changes to the dependencies.
#. Create a new conda environment for testing.::

   $ conda create -n test_cis_interface python=3.6
   $ source activate test_cis_interface

#. Build the updated recipe.::

   $ conda build <path>/<to>/<recipe>/meta.yaml

#. Install the local build of |cis_interface|.::

   $ conda install --use-local -y cis_interface

#. Reconfigure |cis_interface| to use test installation and run the tests.::

   $ cisconfig
   $ cistest -svx --nologcapture

#. Deactivate the test environment and reconfigure |cis_interface| to use the original installation.::

   $ conda deactivate
   $ cisconfig


After the initial creation of the environment etc., the procedure for debugging the recipe will be:

#. Make changes to the source code/recipe.
#. Get clean environment (``--force-reinstall`` dosn't seem to work with ``--use-local``).::

   $ conda uninstall -y cis_interface
   $ conda build purge

#. Re-build the recipe from the local source without tests.::

   $ conda build --no-test <path>/<to>/<recipe>/meta.yaml

#. Force re-install of the local build.::

   $ conda install --use-local -y cis_interface

#. Run the tests.::

   $ cistest -svx --nologcapture
     

Docs Checkout
=============

Before running ``make ghpages``, you must first checkout the 'ghpages' branch 
in the appropriate location. This only has to be done once on each machine you 
publish docs from. From the ``cis_interface`` source directory::

   $ cd ../
   $ git clone https://github.com/cropsinsilico/cis_interface.git cis_interface_docs
   $ cd cis_interface_docs
   $ git checkout gh-pages
