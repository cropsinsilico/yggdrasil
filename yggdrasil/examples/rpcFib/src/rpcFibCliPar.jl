using Yggdrasil
using Printf


function fibClientPar(args)
    
  iterations = parse(Int64, args[1])
  @printf("Hello from Julia rpcFibCliPar: iterations = %d\n", iterations)
  
  # Create RPC connection with server
  # RPC client-side connection will be $(server_name)_$(client_name)
  rpc = Yggdrasil.YggInterface("YggRpcClient", "rpcFibSrv_rpcFibCliPar", "%d", "%d %d")

  # Send all of the requests to the server
  for i = 1:iterations
    @printf("rpcFibCliPar(Julia): fib(->%-2d) :::\n", i)
    ret = rpc.send(Int64(i))
    if (!ret)
      error("rpcFibCliPar(Julia): SEND FAILED")
    end
  end
  
  # Receive responses for all requests that were sent
  for i = 1:iterations
    ret, fib = rpc.recv()
    if (!ret)
      error("rpcFibCliPar(Julia): RECV FAILED")
    end
    @printf("rpcFibCliPar(Julia): fib(%2d<-) = %-2d<-\n", fib[1], fib[2])
  end

  println("Goodbye from Julia rpcFibCliPar")
end


fibClientPar(ARGS)
