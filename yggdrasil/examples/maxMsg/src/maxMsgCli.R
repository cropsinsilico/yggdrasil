library(yggdrasil)


charset = strsplit("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", '')[[1]]

msg_size = YggInterface('YGG_MSG_BUF')
fprintf("maxMsgCli(R): Hello message size %d.", msg_size)

# Create a max message, send/recv and verify
rpc <- YggInterface('YggRpcClient', "maxMsgSrv_maxMsgCli", "%s", "%s")

# Create a max message
output <- ygg_bytes(paste(sample(charset, msg_size, replace=TRUE), collapse=''))

# Call RPC server
c(ret, input) %<-% rpc$call(output)
if (!ret) {
  stop("maxMsgCli(R): RPC ERROR")
}

# Check to see if response matches
if (input[[1]] != output) {
  stop("maxMsgCli(R): ERROR: input/output do not match")
} else {
  print("maxMsgCli(R): CONFIRM")
}

# All done, say goodbye
print("maxMsgCli(R): Goodbye!")
