#!/bin/bash

export PSI_DEBUG="DEBUG"
export RMQ_DEBUG="DEBUG"
export PSI_NAMESPACE="rpcFib_c"
export FIB_ITERATIONS=3
export FIB_SERVER_SLEEP_SECONDS=1

make

cisrun rpcFibCli.yml rpcFibSrv.yml rpcFibCliPar.yml

