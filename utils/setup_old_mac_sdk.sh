#!/bin/bash
conda info -a
# Install older Mac SDK so that conda llvm (7) can be used
# https://github.com/conda-forge/mpi-feedstock/issues/4
export MACOSX_DEPLOYMENT_TARGET=${MACOSX_DEPLOYMENT_TARGET:-10.9}
export CONDA_BUILD_SYSROOT="$(xcode-select -p)/Platforms/MacOSX.platform/Developer/SDKs/MacOSX${MACOSX_DEPLOYMENT_TARGET}.sdk"
export SDKROOT=${CONDA_BUILD_SYSROOT}
echo "MACOSX_DEPLOYMENT_TARGET = ${MACOSX_DEPLOYMENT_TARGET}"
echo "CONDA_BUILD_SYSROOT = ${CONDA_BUILD_SYSROOT}"
echo "SDKROOT = ${SDKROOT}"
	
if [[ ! -d ${CONDA_BUILD_SYSROOT} || "$OSX_FORCE_SDK_DOWNLOAD" == "1" ]]; then
    echo "Downloading ${MACOSX_DEPLOYMENT_TARGET} sdk to ${CONDA_BUILD_SYSROOT}"
    curl -L -O https://github.com/phracker/MacOSX-SDKs/releases/download/10.13/MacOSX${MACOSX_DEPLOYMENT_TARGET}.sdk.tar.xz
    tar -xf MacOSX${MACOSX_DEPLOYMENT_TARGET}.sdk.tar.xz -C "$(dirname "$CONDA_BUILD_SYSROOT")"
    ls "$(dirname "$CONDA_BUILD_SYSROOT")"
    # set minimum sdk version to our target
    plutil -replace MinimumSDKVersion -string ${MACOSX_DEPLOYMENT_TARGET} $(xcode-select -p)/Platforms/MacOSX.platform/Info.plist
    plutil -replace DTSDKName -string macosx${MACOSX_DEPLOYMENT_TARGET}internal $(xcode-select -p)/Platforms/MacOSX.platform/Info.plist
    printf "CONDA_BUILD_SYSROOT:\n  - ${CONDA_BUILD_SYSROOT}  # [osx]\n" > ~/conda_build_config.yaml
fi

# Propagate environment variables to subsequent steps
if [[ -n $GITHUB_ACTIONS ]]; then
    echo -n "MACOSX_DEPLOYMENT_TARGET=" >> $GITHUB_ENV
    echo $MACOSX_DEPLOYMENT_TARGET >> $GITHUB_ENV
    echo -n "CONDA_BUILD_SYSROOT=" >> $GITHUB_ENV
    echo $CONDA_BUILD_SYSROOT >> $GITHUB_ENV
    echo -n "SDKROOT=" >> $GITHUB_ENV
    echo $SDKROOT >> $GITHUB_ENV
fi
