#!/usr/bin/env bash

set -e

if [ "$YGG_RUN_TYPES_EXAMPLES" = "1" ]; then
    echo "Testing types example for language(s) ${YGG_TYPES_LANGUAGE} ..."
    yggtest -c setup.cfg --cov-config=.coveragerc examples/tests/test_types.py --with-examples --long-running --language $YGG_TYPES_LANGUAGES
fi
if [ "$YGG_RUN_EXAMPLES" = "1" ]; then
    echo "Testing examples..."
    yggtest -c setup.cfg --cov-config=.coveragerc examples --with-examples
fi
if [ "$YGG_RUN_ALL_TESTS" = "1" ]; then
    echo "Running general tests..."
    yggtest -c setup.cfg --cov-config=.coveragerc
fi
if [ "$YGG_RUN_TIME_TESTS" = "1" ]; then
    echo "Running timing tests..."
    yggtest -c setup.cfg --cov-config=.coveragerc --long-running tests/test_timing.py
fi
