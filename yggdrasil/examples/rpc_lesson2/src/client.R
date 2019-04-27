library(yggdrasil)


main <- function(iterations, client_index) {

  fprintf('Hello from Python client: iterations = %d ', iterations)

  # Set up connections matching yaml
  # RPC client-side connection will be $(server_name)_$(client_name)
  rpc <- YggInterface('YggRpcClient',
                      sprintf("server_client%d", client_index), "%d", "%d")
  log <- YggInterface('YggOutput',
                      sprintf("output_log%d", client_index), 'fib(%-2d) = %-2d\n')

  # Iterate over Fibonacci sequence
  for (i in 1:iterations) {
        
    # Call the server and receive response
    fprintf('client%d(R): Calling fib(%d)', client_index, i)
    c(ret, result) %<-% rpc$call(i)
    if (!ret) {
      stop(sprintf('client%d(R): RPC CALL ERROR', client_index))
    }
    fib <- result[[1]]
    fprintf('client%d(R): Response fib(%d) = %d', client_index, i, fib)

    # Log result by sending it to the log connection
    ret <- log$send(i, fib)
    if (!ret) {
      stop(sprintf('client%d(R): SEND ERROR', client_index))
    }
  }

  fprintf('Goodbye from R client%d', client_index)
}


args = commandArgs(trailingOnly=TRUE)
main(strtoi(args[[1]]), strtoi(args[[2]]))
