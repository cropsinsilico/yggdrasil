model_function <- function(in_buf) {
  # The global_scope keyword is required to ensure that the comm persists
  # between function calls
  rpc <- YggInterface('YggRpcClient', 'server_client', global_scope=TRUE)
  print(sprintf("client(R): %s", in_buf))
  c(ret, result) %<-% rpc$call(in_buf)
  if (!ret) {
    stop('client(R): RPC CALL ERROR')
  }
  out_buf <- result[[1]]
  return(out_buf)
}
