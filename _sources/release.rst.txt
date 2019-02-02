
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

#. Merge branch into master after tests pass and code review complete
#. Create tag with new version on master::

   $ git tag x.x.x
   
#. Push to github (this triggers deployment of source distribution and wheels to PyPI)::

   $ git push; git push --tags
   
#. Update conda-forge build
#. Checkout ``gh-pages`` branch if it dosn't already exist (See below), regenerate docs and push to gh-pages branch::

   $ cd docs
   $ make ghpages


Docs Checkout
=============

Before running ``make ghpages``, you must first checkout the 'ghpages' branch 
in the appropriate location. This only has to be done once on each machine you 
publish docs from. From the ``yggdrasil`` source directory::

   $ cd ../
   $ git clone https://github.com/cropsinsilico/yggdrasil.git yggdrasil_docs
   $ cd yggdrasil_docs
   $ git checkout gh-pages
