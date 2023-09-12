using Yggdrasil
using Printf


function fibServer(args)

  sleeptime = parse(Float64, args[1])
  @printf("Hello from Julia rpcFibSrv: sleeptime = %f\n", sleeptime)

  # Create server-side rpc conneciton using model name
  rpc = Yggdrasil.YggInterface("YggRpcServer", "rpcFibSrv", "%d", "%d %d")

  # Continue receiving requests until error occurs (the connection is closed
  # by all clients that have connected).
  while (true)
    println("rpcFibSrv(Julia): receiving...")
    retval, rpc_in = rpc.recv()
    if (!retval)
      println("rpcFibSrv(Julia): end of input")
      break
    end

    # Compute fibonacci number
    @printf("rpcFibSrv(Julia): <- input %d", rpc_in[1])
    pprev = 0
    prev = 1
    result = 1
    fib_no = 1
    arg = rpc_in[1]
    while (fib_no < arg)
      result = prev + pprev
      pprev = prev
      prev = result
      fib_no = fib_no + 1
    end
    @printf(" ::: ->(%2d %2d)\n", arg, result)

    # Sleep and then send response back
    Sys.sleep(sleeptime)
    flag = rpc.send(arg, Int64(result))
    if (!flag)
      error("rpcFibSrv(Julia): ERROR sending")
    end
  end
  println("Goodbye from Julia rpcFibSrv")

end

fibServer(ARGS)
