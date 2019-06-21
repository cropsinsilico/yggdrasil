bytes_to_R <- function(pyobj) {
  np <- reticulate::import('numpy', convert=FALSE)
  if (is(pyobj, "numpy.ndarray")) {
    pyobj <- reticulate::py_call(np$char$decode, pyobj)
  } else {
    pyobj <- pyobj$decode('utf-8')
  }
  out <- reticulate::py_to_r(pyobj)
  return(out)
}
