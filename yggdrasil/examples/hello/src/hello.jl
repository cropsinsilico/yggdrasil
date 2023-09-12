# Import library for input/output channels
using Yggdrasil
using Printf

println("Hello from Julia")

# Ins/outs matching with the the model yaml
inf = Yggdrasil.YggInterface("YggInput", "inFile")
outf = Yggdrasil.YggInterface("YggOutput", "outFile")
inq = Yggdrasil.YggInterface("YggInput", "helloQueueIn")
outq = Yggdrasil.YggInterface("YggOutput", "helloQueueOut")
println("hello(Julia): Created I/O channels")

# Receive input from a local file
ret, buf = inf.recv()
if (!ret)
  error("hello(Julia): ERROR FILE RECV")
end
@printf("hello(Julia): Received %d bytes from file: %s\n", length(buf), buf)

# Send output to the output queue
ret = outq.send(buf)
if (!ret)
  error("hello(Julia): ERROR QUEUE SEND")
end
println("hello(Julia): Sent to outq")

# Receive input form the input queue
ret, buf = inq.recv()
if (!ret)
  error("hello(Julia): ERROR QUEUE RECV")
end
@printf("hello(Julia): Received %d bytes from queue: %s\n", length(buf), buf)

# Send output to a local file
ret = outf.send(buf)
if (!ret)
  error("hello(Julia): ERROR FILE SEND")
end
println("hello(Julia): Sent to outf")

println("Goodbye from Julia")
