from cis_interface.interface.PsiInterface import PsiRpcServer


print("maxMsgSrv(P): Hello!")
rpc = PsiRpcServer("maxMsgSrv", "%s", "%s")

ret, input = rpc.rpcRecv()
print("maxMsgSrv(P): rpcRecv returned %d, input %s" % (ret, input[0]))
rpc.rpcSend(input[0])

print("maxMsgSrv(P): Goodbye!")
