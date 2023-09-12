using Printf

function modelA_function(in_val)
  out_val = in_val
  @printf("modelA_function(%s) = %s", in_val, out_val)
  return out_val
end