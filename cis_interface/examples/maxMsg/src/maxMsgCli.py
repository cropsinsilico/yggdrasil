import sys
import random
from cis_interface.interface.PsiInterface import PsiRpcClient, PSI_MSG_MAX


def rand_str(length):
    charset = ("0123456789" +
               "abcdefghijklmnopqrstuvwxyz" +
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    out = ''
    while (len(out) < length):
        index = int(random.random() * len(charset))
        out += charset[index]
    return out


print("maxMsgCli(P): Hello PSI_MSG_MAX is %d." % PSI_MSG_MAX)

# Create a max message, send/recv and verify
rpc = PsiRpcClient("maxMsgSrv_maxMsgCli", "%s", "%s")

# Create a max message
output = rand_str(PSI_MSG_MAX - 1)

# Call RPC server
ret, input = rpc.rpcCall(output)
if not ret:
    print("maxMsgCli(P): RPC ERROR")
    sys.exit(-1)

# Check to see if response matches
if (input[0] != output):
    print("maxMsgCli(P): ERROR: input/output do not match")
    sys.exit(-1)
else:
    print("maxMsgCli(P): CONFIRM")

# All done, say goodbye
print("maxMsgCli(P): Goodbye!")
