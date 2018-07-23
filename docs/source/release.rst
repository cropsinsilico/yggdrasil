
Release Steps
=============

#. [on branch] Regenerate schema:: 

   $ cisschema
   $ git add cis_interface/.cis_schema.yml
   $ git commit -m "Updated .cis_schema.yml"
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
#. Regenerate docs and push to gh-pages branch::

   $ cd docs
   $ make ghpages
