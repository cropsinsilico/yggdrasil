int64_to_R <- function(pyboj) {
  out <- bit64::as.integer64(reticulate::py_to_r(pyobj))
  return(out)
}
