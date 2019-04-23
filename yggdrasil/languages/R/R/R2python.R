

R2python <- function(robj) {
  # Uncomment if special treatment required
  # np <- reticulate::import('numpy', convert=FALSE)
  # if (is(robj, "list")) {
  #   rapply(robj, R2python, classes='ANY', how='replace')
  # } else if (is(robj, "integer")) {
  # TODO: This seems to be cast as int when passing to Python
  #   out = np$int32(reticulate::r_to_py(robj))
  #   return(out)
  # }
  return(reticulate::r_to_py(robj))
}
