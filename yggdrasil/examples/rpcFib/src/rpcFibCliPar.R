library(yggdrasil)


fibClientPar <- function(args) {
    
  iterations <- strtoi(args[[1]])
  fprintf('Hello from R rpcFibCliPar: iterations = %d ', iterations)
  
  # Create RPC connection with server
  # RPC client-side connection will be $(server_name)_$(client_name)
  rpc <- YggInterface('YggRpcClient', "rpcFibSrv_rpcFibCliPar", "%d", "%d %d")

  # Send all of the requests to the server
  for (i in 1:iterations) {
    fprintf('rpcFibCliPar(R): fib(->%-2d) ::: ', i)
    ret <- rpc$send(as.integer(i))
    if (!ret) {
      stop('rpcFibCliPar(R): SEND FAILED')
    }
  }
  
  # Receive responses for all requests that were sent
  for (i in 1:iterations) {
    c(ret, fib) %<-% rpc$recv()
    if (!ret) {
      stop('rpcFibCliPar(R): RECV FAILED')
    }
    fprintf('rpcFibCliPar(R): fib(%2d<-) = %-2d<-', fib[[1]], fib[[2]])
  }

  print('Goodbye from R rpcFibCliPar')
}


args <- commandArgs(trailingOnly=TRUE)
fibClientPar(args)
