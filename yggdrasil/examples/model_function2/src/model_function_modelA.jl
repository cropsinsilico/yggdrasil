using Unitful
using Printf

function model_function(x)
  y = x .+ 1.0u"g"
  @printf("Model A: %s -> %s\n", x, y)
  return y
end