using Printf

function modelB_function2(in_val)
  # Only valid if in_val > 2
  out_val = 2 * in_val^2
  @printf("modelB_function2(%s) = %s", in_val, out_val)
  return in_val, out_val
end