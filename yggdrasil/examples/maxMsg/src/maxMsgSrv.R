library(yggdrasil)


print("maxMsgSrv(R): Hello!")
rpc <- YggInterface('YggRpcServer', "maxMsgSrv", "%s", "%s")

while (TRUE) {
  c(ret, input) %<-% rpc$recv()
  if (!ret) {
    break
  }
  fprintf("maxMsgSrv(R): rpcRecv returned %s, input %.10s...", ret, input[[1]])
  flag <- rpc$send(input[[1]])
  if (!flag) {
    stop('maxMsgSrv(R): Error sending reply.')
  }
}

print("maxMsgSrv(R): Goodbye!")
