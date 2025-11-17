#!/bin/sh
set -euo pipefail
while read p; do
    vcpkg.exe install --triplet=${VCPKG_TRIPLET} --classic "$p"
done <$1;
