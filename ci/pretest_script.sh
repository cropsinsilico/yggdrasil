#!/usr/bin/env bash

set -e

echo "Checking that source version matches installed version..."
export YGG_SOURCE_VERSION=$(python -c 'import versioneer; print(versioneer.get_version())')
cd ../
export YGG_BUILD_VERSION=$(python -c 'import yggdrasil; print(yggdrasil.__version__)')
cd yggdrasil
echo "Source version: ${YGG_SOURCE_VERSION}"
echo "Build  version: ${YGG_BUILD_VERSION}"
if [ $YGG_SOURCE_VERSION != $YGG_BUILD_VERSION ]; then
    echo "Versions do not match"
    exit 1
fi

if [ "$INSTALLR" = "1" ]; then
    which R
    which Rscript
fi
flake8 yggdrasil
if [ -n $YGG_CONDA ]; then
    python create_coveragerc.py
fi
if [ ! -f ".coveragerc" ]; then
    echo ".coveragerc file dosn't exist."
    exit 1
fi
cat .coveragerc
ygginfo --verbose
