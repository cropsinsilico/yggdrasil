from cis_interface.interface.CisInterface import CisRpcServer


print("maxMsgSrv(P): Hello!")
rpc = CisRpcServer("maxMsgSrv", "%s", "%s")

while True:
    ret, input = rpc.rpcRecv()
    if not ret:
        break
    print("maxMsgSrv(P): rpcRecv returned %s, input %.10s..." % (ret, input[0]))
    flag = rpc.rpcSend(input[0])
    if not flag:
        raise RuntimeError('maxMsgSrv(P): Error sending reply.')

print("maxMsgSrv(P): Goodbye!")
