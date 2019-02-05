
Release Steps
=============

#. [on branch] Regenerate schema:: 

   $ yggschema
   $ git add yggdrasil/.ygg_schema.yml
   $ git add yggdrasil/.ygg_metaschema.json
   $ git commit -m "Updated .ygg_schema.yml and .ygg_metaschema.json"
   $ git push origin [BRANCH]

#. [on branch] Open pull request to merge changes into master
#. [on branch] Update docs to reflect new features and make sure they build locally::

   $ cd docs
   $ make autodoc

#. Test conda-forge recipe locally using steps below.
#. Merge branch into master after tests pass and code review complete
#. Create tag with new version on master::

   $ git tag x.x.x
   
#. Push to github (this triggers deployment of source distribution and wheels to PyPI)::

   $ git push; git push --tags
   
#. Once the source distribution has been uploaded to PyPI, update the conda-forge recipe
on the cropsinsilico feedstock fork
`here <https://github.com/cropsinsilico/yggdrasil-feedstock>`_ with the new version
and SHA256 (this can be found
`here <https://pypi.org/project/yggdrasil-framework/#files>`_) and create a pull request
to merge the changes into the
`conda-forge <https://github.com/conda-forge/yggdrasil-feedstock>`_ feedstock.
#. Checkout ``gh-pages`` branch if it dosn't already exist (See below), regenerate docs and push to gh-pages branch::

   $ cd docs
   $ make ghpages


Updating and Testing the Conda Recipe
=====================================

#. Install ``conda-build`` if you don't already have it.::
     
   $ conda install conda-build

#. Clone the feedstock fork.::

   $ git clone https://github.com/cropsinsilico/yggdrasil-feedstock.git

#. Update the recipe to reflect any changes to the dependencies.
#. Update the source section of ``meta.yaml`` to use your local installation by specifying a path and commenting out the ``url`` and ``sha256`` entries.::

   source:
     path: <path to local yggdrasil>

#. Create a new conda environment for testing.::

   $ conda create -n test_yggdrasil python=3.6
   $ source activate test_yggdrasil

#. Build the updated recipe.::

   $ conda build <path>/<to>/<recipe>/meta.yaml

#. Install the local build of |yggdrasil|.::

   $ conda install --use-local yggdrasil

#. Run the tests.::

   $ yggtest -svx --nologcapture


After the initial creation of the environment etc., the procedure for debugging the recipe will be:

#. Make changes to the source code/recipe.

#. Get clean environment (``--force-reinstall`` dosn't seem to work with ``--use-local``).::

   $ conda uninstall yggdrasil
   $ conda build purge

#. Re-build the recipe from the local source without tests.::

   $ conda build --no-test <path>/<to>/<recipe>/meta.yaml

#. Force re-install of the local build.::

   $ conda install --use-local yggdrasil

#. Run the tests.::

   $ yggtest -svx --nologcapture
     

Docs Checkout
=============

Before running ``make ghpages``, you must first checkout the 'ghpages' branch 
in the appropriate location. This only has to be done once on each machine you 
publish docs from. From the ``yggdrasil`` source directory::

   $ cd ../
   $ git clone https://github.com/cropsinsilico/yggdrasil.git yggdrasil_docs
   $ cd yggdrasil_docs
   $ git checkout gh-pages
