modelB_function <- function(in_val) {
  out_val <- 3 * in_val
  print(sprintf("modelB_function(%f) = %f", in_val, out_val))
  return(list(in_val, out_val))
}
