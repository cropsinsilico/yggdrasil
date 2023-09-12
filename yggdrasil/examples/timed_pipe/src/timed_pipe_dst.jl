using Yggdrasil
using Printf


function run(args)
  println("Hello from Julia pipe_dst")

  # Ins/outs matching with the the model yaml
  inq = Yggdrasil.YggInterface("YggInput", "input_pipe")
  outf = Yggdrasil.YggInterface("YggOutput", "output_file")
  println("pipe_dst(Julia): Created I/O channels")

  # Continue receiving input from the queue
  global count = 0
  while (true)
    ret, buf = inq.recv()
    if (!ret)
      println("pipe_dst(Julia): Input channel closed")
      break
    end
    ret = outf.send(buf)
    if (!ret)
      error(@sprintf("pipe_dst(Julia): SEND ERROR ON MSG %d\n", count))
    end
    global count = count + 1
  end

  @printf("Goodbye from Julia destination. Received %d messages.\n", count)
end
    

run(ARGS)
