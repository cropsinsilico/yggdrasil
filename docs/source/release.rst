
Release Steps
=============

#. [on branch] Update docs to reflect new features
#. [on branch] Increment version in setup.py
#. [on branch] Increment version in docs
#. [on branch] Regenerate schema (``cisschema``)
#. Merge into master
#. Upload to PyPI

   #. PyPI Test: ``python setup.py sdist upload -r pypitest``
   #. PyPI: ``python setup.py sdist upload -r pypi``

#. Update conda-forge
#. Regenerate docs
