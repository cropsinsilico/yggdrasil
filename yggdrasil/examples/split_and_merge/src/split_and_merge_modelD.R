modelD_function <- function(in_val1, in_val2) {
  out_val <- in_val1 + in_val2
  print(sprintf("modelD_function(%f, %s) = %f", in_val1, in_val2, out_val))
  return(list(in_val1, in_val2, out_val))
}
