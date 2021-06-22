using Printf

function modelA_function(in_val)
  out_val1 = 2 * in_val
  out_val2 = 3 * in_val
  @printf("modelA_function(%s) = (%s, %s)\n", in_val, out_val1, out_val2)
  return out_val1, out_val2
end
