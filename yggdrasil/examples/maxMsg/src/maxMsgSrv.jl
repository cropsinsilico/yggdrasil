# Import library for input/output channels
using Yggdrasil
using Printf


println("maxMsgSrv(Julia): Hello!")
rpc = Yggdrasil.YggInterface("YggRpcServer", "maxMsgSrv", "%s", "%s")

while true
    ret, input = rpc.recv()
    if (!ret)
	break
    end
    @printf("maxMsgSrv(Julia): rpcRecv returned %s, input %.10s...\n", ret, input[1])
    flag = rpc.send(input[1])
    if (!flag)
        error("maxMsgSrv(Julia): Error sending reply.")
    end
end  # while

println("maxMsgSrv(Julia): Goodbye!")