modelB_function2 <- function(in_val) {
  # Only valid if in_val > 2
  out_val <- 2 * in_val^2
  print(sprintf("modelB_function2(%f) = %f", in_val, out_val))
  return(list(in_val, out_val))
}
