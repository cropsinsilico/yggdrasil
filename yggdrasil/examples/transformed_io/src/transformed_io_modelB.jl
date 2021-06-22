using Printf
function modelB_function(in_val)
  out_val = 3 * in_val
  @printf("modelB_function(%s) = %s\n", in_val, out_val)
  return in_val, out_val
end