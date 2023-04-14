using Yggdrasil
using Printf

# Get input and output channels matching yaml
in1 = Yggdrasil.YggInterface("YggInput", "input1_julia")
in2 = Yggdrasil.YggInterface("YggInput", "static_julia")
out1 = Yggdrasil.YggInterface("YggOutput", "output_julia")

# Get input from input1 channel
ret, adata = in1.recv()
if (!ret)
   error("SaM(julia): ERROR RECV from input1")
end
a = parse(Int32, adata)
@printf("SaM(julia): Received %d from input1\n", a)

# Get input from static channel
ret, bdata = in2.recv()
if (!ret)
   error("SaM(julia): ERROR RECV from static")
end
b = parse(Int32, bdata)
@printf("SaM(julia): Received %d from static\n", b)

# Compute sum and send message to output channel
sum = a + b
outdata = @sprintf("%d", sum)
ret = out1.send(outdata)
if (!ret)
   error("SaM(julia): ERROR SEND to output")
end
println("SaM(julia): Sent to output")