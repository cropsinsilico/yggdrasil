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

  model_copy = ENV["YGG_MODEL_COPY"]
  @printf("Hello from Julia server%s!\n", model_copy)

  # Create server-side rpc conneciton using model name
  rpc = Yggdrasil.YggInterface("YggRpcServer", "server", "%d", "%d")

  # Continue receiving requests until the connection is closed when all
  # clients have disconnected.
  while (true)
    @printf("server%s(Julia): receiving...\n", model_copy)
    retval, rpc_in = rpc.recv()
    if (!retval)
      @printf("server%s(Julia): end of input\n", model_copy)
      break
    end

    # Compute fibonacci number
    n = rpc_in[1]
    @printf("server%s(Julia): Received request for Fibonacci number %d\n", model_copy, n)
    result = get_fibonacci(n)
    @printf("server%s(Julia): Sending response for Fibonacci number %d: %d\n", model_copy, n, result)

    # Send response back
    flag = rpc.send(result)
    if (!flag)
      error(sprintf("server%s(Julia): ERROR sending\n", model_copy))
    end
  end
  
  println("Goodbye from Julia server")
end

main()
