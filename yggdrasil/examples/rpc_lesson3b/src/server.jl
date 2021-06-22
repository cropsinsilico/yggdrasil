using Printf

function model_function(in_buf)
  @printf("server(Julia): %s\n", in_buf)
  out_buf = in_buf
  return out_buf
end
