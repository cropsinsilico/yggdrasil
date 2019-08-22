library(yggdrasil)


fibServer <- function(args) {

  sleeptime <- as.double(args[[1]])
  fprintf('Hello from R rpcFibSrv: sleeptime = %f', sleeptime)

  # Create server-side rpc conneciton using model name
  rpc <- YggInterface('YggRpcServer', "rpcFibSrv", "%d", "%d %d")

  # Continue receiving requests until error occurs (the connection is closed
  # by all clients that have connected).
  while (TRUE) {
    print('rpcFibSrv(R): receiving...')
    c(retval, rpc_in) %<-% rpc$recv()
    if (!retval) {
      print('rpcFibSrv(R): end of input')
      break
    }

    # Compute fibonacci number
    fprintf('rpcFibSrv(R): <- input %d', rpc_in[[1]])
    pprev <- 0
    prev <- 1
    result <- 1
    fib_no <- 1
    arg <- rpc_in[[1]]
    while (fib_no < arg) {
      result <- prev + pprev
      pprev <- prev
      prev <- result
      fib_no <- fib_no + 1
    }
    fprintf(' ::: ->(%2d %2d)', arg, result)

    # Sleep and then send response back
    Sys.sleep(sleeptime)
    flag <- rpc$send(arg, as.integer(result))
    if (!flag) {
      stop('rpcFibSrv(R): ERROR sending')
    }
  }
  print('Goodbye from R rpcFibSrv')

}

args = commandArgs(trailingOnly=TRUE)
fibServer(args)
