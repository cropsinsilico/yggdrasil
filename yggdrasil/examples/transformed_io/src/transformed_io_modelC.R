modelC_function <- function(in_val) {
  out_val <- 2 * in_val
  print(sprintf("modelC_function(%f) = %f", in_val, out_val))
  return(list(in_val, out_val))
}
