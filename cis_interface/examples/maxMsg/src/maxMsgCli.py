import sys
import random
from yggdrasil.interface.YggInterface import YggRpcClient, YGG_MSG_BUF


def rand_str(length):
    charset = ("0123456789"
               + "abcdefghijklmnopqrstuvwxyz"
               + "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    out = ''
    while (len(out) < (length - 1)):
        index = int(random.random() * len(charset))
        out += charset[index]
    if sys.version_info[0] == 3:
        out = out.encode("utf-8")
    return out


msg_size = YGG_MSG_BUF

print("maxMsgCli(P): Hello message size %d." % msg_size)

# Create a max message, send/recv and verify
rpc = YggRpcClient("maxMsgSrv_maxMsgCli", "%s", "%s")

# Create a max message
output = rand_str(msg_size)

# Call RPC server
ret, input = rpc.rpcCall(output)
if not ret:
    raise RuntimeError("maxMsgCli(P): RPC ERROR")

# Check to see if response matches
if (input[0] != output):
    raise RuntimeError("maxMsgCli(P): ERROR: input/output do not match")
else:
    print("maxMsgCli(P): CONFIRM")

# All done, say goodbye
print("maxMsgCli(P): Goodbye!")
