#!/bin/sh
set -euo pipefail
while read p; do
    echo "vcpkg.exe install --triplet=${VCPKG_TRIPLET} --classic \"$p\""
    # vcpkg.exe install --triplet=${VCPKG_TRIPLET} --classic "$p"
    vcpkg.exe install --classic "$p"
done <$1;
