using Unitful
using Printf

function model_function(x)
  y = x .+ 2.0u"g"
  @printf("Model B: %s -> %s\n", x, y)
  return y
end