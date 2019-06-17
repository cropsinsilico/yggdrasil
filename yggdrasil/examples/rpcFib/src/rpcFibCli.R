library(yggdrasil)


fibClient <- function(args) {
    
  iterations <- strtoi(args[[1]])
  fprintf('Hello from R rpcFibCli: iterations = %d ', iterations)

  # Set up connections matching yaml
  # RPC client-side connection will be $(server_name)_$(client_name)
  ymlfile <- YggInterface('YggInput', "yaml_in")
  rpc <- YggInterface('YggRpcClient', "rpcFibSrv_rpcFibCli", "%d", "%d %d")
  log <- YggInterface('YggOutput', "output_log")

  # Read entire contents of yaml
  c(ret, ycontent) %<-% ymlfile$recv()
  if (!ret) {
    stop('rpcFibCli(R): RECV ERROR')
  }
  fprintf('rpcFibCli: yaml has %d lines', length(strsplit(ycontent, '\n')))

  for (i in 1:iterations) {
        
    # Call the server and receive response
    fprintf('rpcFibCli(R): fib(->%-2d) ::: ', i)
    c(ret, fib) %<-% rpc$call(as.integer(i))
    if (!ret) {
      stop('rpcFibCli(R): RPC CALL ERROR')
    }

    # Log result by sending it to the log connection
    s <- sprintf('fib(%2d<-) = %-2d<-\n', fib[[1]], fib[[2]])
    print(s)
    ret <- log$send(s)
    if (!ret) {
      stop('rpcFibCli(R): SEND ERROR')
    }
  }

  print('Goodbye from R rpcFibCli')
}

    
args <- commandArgs(trailingOnly=TRUE)
fibClient(args)
