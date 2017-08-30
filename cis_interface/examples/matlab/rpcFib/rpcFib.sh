
export PSI_DEBUG="DEBUG"
export PSI_NAMESPACE="rpcFib_Matlab"
export FIB_ITERATIONS=3
export FIB_SERVER_SLEEP_SECONDS=1

cisrun rpcFibCli.yml rpcFibCliPar.yml rpcFibSrv.yml
