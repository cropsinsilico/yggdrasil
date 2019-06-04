.. _general_rst:

General Development Notes
#########################

Development Workflow
====================

Development of |yggdrasil| should be done on branches and/or forks that
are then merged in via pull request after passing linting (via
`flake8 <http://flake8.pycqa.org/en/latest/>`_), testing (via
continuous integration on
`travis <https://travis-ci.org/cropsinsilico/yggdrasil>`_ and
`appveyor <https://ci.appveyor.com/project/langmm/yggdrasil>`_),
and code review. Prior to beginning new development,
developers should open a Github issue on the repository that describes
the proposed changes and/or features so that discussion can help identify
potential sticking points, features that already exist but are poorly documented,
and features that would break a significant portion of the code.


Testing
=======

All development should be accompanied by tests. |yggdrasil| aims to
maintain 100% test coverage, so tests should be provided in pull
requests including new development. |yggdrasil| provides base classes to
aid in testing for most major classes (which is where development is
likely to occur). These are usually located in the tests directory within
the module directory containing the class being tested. In some cases
|yggdrasil| will automatically generate tests if certain class
attributes and/or methods are defined (e.g. serialization, communication,
and connection driver classes).
