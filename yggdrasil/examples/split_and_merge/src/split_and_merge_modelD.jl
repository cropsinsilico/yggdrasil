using Printf

function modelD_function(in_val1, in_val2)
  out_val = in_val1 + in_val2
  @printf("modelD_function(%s, %s) = %s\n", in_val1, in_val2, out_val)
  return in_val1, in_val2, out_val
end
