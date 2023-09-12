using Yggdrasil
using Printf
using Random


msg_size = Yggdrasil.YggInterface("YGG_MSG_BUF")
@printf("maxMsgCli(Julia): Hello message size %d.\n", msg_size)

# Create a max message, send/recv and verify
rpc = Yggdrasil.YggInterface("YggRpcClient", "maxMsgSrv_maxMsgCli", "%s", "%s")

# Create a max message
output = Yggdrasil.Bytes(Random.randstring(msg_size))

# Call RPC server
ret, input = rpc.call(output)
if (!ret)
    error("maxMsgCli(Julia): RPC ERROR")
end

# Check to see if response matches
if (input[1] != output)
    error("maxMsgCli(Julia): ERROR: input/output do not match")
else
    println("maxMsgCli(Julia): CONFIRM")
end

# All done, say goodbye
println("maxMsgCli(Julia): Goodbye!")