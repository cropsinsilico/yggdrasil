modelA_function <- function(in_val) {
  out_val1 <- 2 * in_val
  out_val2 <- 3 * in_val
  print(sprintf("modelA_function(%f) = (%f, %f)", in_val, out_val1, out_val2))
  return(list(out_val1,out_val2))
}
