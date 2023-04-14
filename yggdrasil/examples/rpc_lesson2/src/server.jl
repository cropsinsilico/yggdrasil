using Yggdrasil
using Printf


function get_fibonacci(n)
  global pprev = 0
  global prev = 1
  global result = 1
  global fib_no = 1
  while (fib_no < n)
    global result = prev + pprev
    global pprev = prev
    global prev = result
    global fib_no = fib_no + 1
  end
  return Int64(result)
end


function main()

  println("Hello from Julia server!")

  # Create server-side rpc conneciton using model name
  rpc = Yggdrasil.YggInterface("YggRpcServer", "server", "%d", "%d")

  # Continue receiving requests until the connection is closed when all
  # clients have disconnected.
  while (true)
    println("server(Julia): receiving...")
    retval, rpc_in = rpc.recv()
    if (!retval)
      println("server(Julia): end of input")
      break
    end

    # Compute fibonacci number
    n = rpc_in[1]
    @printf("server(Julia): Received request for Fibonacci number %d\n", n)
    result = get_fibonacci(n)
    @printf("server(Julia): Sending response for Fibonacci number %d: %d\n", n, result)

    # Send response back
    flag = rpc.send(result)
    if (!flag)
      error("server(Julia): ERROR sending")
    end
  end
  
  println("Goodbye from Julia server")
end

main()
