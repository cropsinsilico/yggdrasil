import sys
from cis_interface.interface.PsiInterface import PsiRpcServer


print("maxMsgSrv(P): Hello!")
rpc = PsiRpcServer("maxMsgSrv", "%s", "%s")

while True:
    ret, input = rpc.rpcRecv()
    if not ret:
        break
    print("maxMsgSrv(P): rpcRecv returned %s, input %s" % (ret, input[0]))
    rpc.rpcSend(input[0])

print("maxMsgSrv(P): Goodbye!")
sys.exit(0)
