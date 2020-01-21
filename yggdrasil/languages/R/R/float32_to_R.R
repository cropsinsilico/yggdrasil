ygg_float32 <- function(robj) {
  robj <- structure(robj, class="ygg_float32")
  return(robj)
}


float32_to_R <- function(pyobj) {
  np <- reticulate::import('numpy', convert=FALSE)
  # out <- as.single(reticulate::py_to_r(pyobj))
  # out <- float::fl(reticulate::py_to_r(pyobj))
  out <- reticulate::py_to_r(call_python_method(np, 'float64', pyobj))
  return(ygg_float32(out))
}
