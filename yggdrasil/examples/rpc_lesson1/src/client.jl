using Yggdrasil
using Printf


function main(iterations)
    
  @printf("Hello from Julia client: iterations = %d\n", iterations)

  # Set up connections matching yaml
  # RPC client-side connection will be $(server_name)_$(client_name)
  rpc = Yggdrasil.YggInterface("YggRpcClient", "server_client", "%d", "%d")
  log = Yggdrasil.YggInterface("YggOutput", "output_log", "fib(%-2d) = %-2d\n")

  # Iterate over Fibonacci sequence
  for i = 1:iterations
        
    # Call the server and receive response
    @printf("client(Julia): Calling fib(%d)\n", i)
    ret, result = rpc.call(i)
    if (!ret)
      error("client(Julia): RPC CALL ERROR")
    end
    fib = result[1]
    @printf("client(Julia): Response fib(%d) = %d\n", i, fib)

    # Log result by sending it to the log connection
    ret = log.send(i, fib)
    if (!ret)
      error("client(Julia): SEND ERROR")
    end
  end

  println("Goodbye from Julia client")
end

    
main(parse(Int64, ARGS[1]))
