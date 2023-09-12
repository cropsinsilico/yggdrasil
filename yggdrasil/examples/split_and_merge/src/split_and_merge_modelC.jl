using Printf

function modelC_function(in_val)
  out_val = 4 * in_val
  @printf("modelC_function(%s) = %s\n", in_val, out_val)
  return out_val
end
