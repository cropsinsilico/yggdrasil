#!/bin/sh
set -euo pipefail
while read p; do
    p0="$(sed -e 's/\ *$//g'<<<"${p}")"
    echo "vcpkg.exe install --triplet=${VCPKG_TRIPLET} --classic \"$p0\""
    vcpkg.exe install --triplet=${VCPKG_TRIPLET} --classic "$p0"
    # vcpkg.exe install --classic "$p"
done <$1;
