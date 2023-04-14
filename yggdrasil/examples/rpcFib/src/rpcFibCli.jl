using Yggdrasil
using Printf


function fibClient(args)
    
  iterations = parse(Int64, args[1])
  @printf("Hello from Julia rpcFibCli: iterations = %d\n", iterations)

  # Set up connections matching yaml
  # RPC client-side connection will be $(server_name)_$(client_name)
  ymlfile = Yggdrasil.YggInterface("YggInput", "yaml_in")
  rpc = Yggdrasil.YggInterface("YggRpcClient", "rpcFibSrv_rpcFibCli", "%d", "%d %d")
  log = Yggdrasil.YggInterface("YggOutput", "output_log")

  # Read entire contents of yaml
  ret, ycontent = ymlfile.recv()
  if (!ret)
    error("rpcFibCli(Julia): RECV ERROR")
  end
  @printf("rpcFibCli: yaml has %d lines\n", countlines(IOBuffer(ycontent)))

  for i = 1:iterations
        
    # Call the server and receive response
    @printf("rpcFibCli(Julia): fib(->%-2d) ::: ", i)
    ret, fib = rpc.call(Int64(i))
    if (!ret)
      error("rpcFibCli(Julia): RPC CALL ERROR")
    end

    # Log result by sending it to the log connection
    s = @sprintf("fib(%2d<-) = %-2d<-\n", fib[1], fib[2])
    println(s)
    ret = log.send(s)
    if (!ret)
      error("rpcFibCli(Julia): SEND ERROR")
    end
  end

  println("Goodbye from Julia rpcFibCli")
end

    
fibClient(ARGS)
