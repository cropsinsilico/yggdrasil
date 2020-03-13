ygg_bytes <- function(robj) {
  # if (is(robj, "character")) {
  robj <- structure(robj, class="ygg_bytes")
  # }
  return(robj)
}

bytes_to_R <- function(pyobj) {
  np <- reticulate::import('numpy', convert=FALSE)
  if (is(pyobj, "numpy.ndarray")) {
    pyobj <- reticulate::py_call(np$char$decode, pyobj)
  } else {
    pyobj <- pyobj$decode('utf-8')
  }
  out <- ygg_bytes(reticulate::py_to_r(pyobj))
  return(out)
}
