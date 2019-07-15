#!/usr/bin/env bash

set -e

echo "Checking that source version matches installed version..."
export YGG_SOURCE_VERSION=$(python -c 'import versioneer; print(versioneer.get_version())')
cd yggdrasil
export YGG_BUILD_VERSION=$(python -c 'import yggdrasil; print(yggdrasil.__version__)')
cd ../
echo "Source version: ${YGG_SOURCE_VERSION}"
echo "Build  version: ${YGG_BUILD_VERSION}"
if [[ "$YGG_SOURCE_VERSION" != "$YGG_BUILD_VERSION" ]]; then
    echo "Versions do not match"
    exit 1
fi

which R
which Rscript
flake8 yggdrasil
if [[ -n "$CONDA" ]]; then
    python create_coveragerc.py
fi
ygginfo --verbose
