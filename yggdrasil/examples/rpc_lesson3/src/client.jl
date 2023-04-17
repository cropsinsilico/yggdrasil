using Yggdrasil
using Printf

function model_function(in_buf)
  # The global_scope keyword is required to ensure that the comm persists
  # between function calls
  rpc = Yggdrasil.YggInterface("YggRpcClient", "server_client", global_scope=true)
  @printf("client(Julia): %s\n", in_buf)
  ret, result = rpc.call(in_buf)
  if (!ret)
    error("client(Julia): RPC CALL ERROR")
  end
  out_buf = result
  return out_buf
end