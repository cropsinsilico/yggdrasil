

python2R <- function(pyobj) {
  # Uncomment if special treatment required
  np <- reticulate::import('numpy', convert=FALSE)
  if (is(pyobj, "python.builtin.tuple")
      || is(pyobj, "python.builtin.list")) {
    pyobj_len = reticulate::py_len(pyobj)
    out = list()
    for (i in 1L:pyobj_len) {
      x = python2R(reticulate::py_call(
        reticulate::py_get_attr(pyobj, '__getitem__'), i-1L))
      out[[i]] <- x
    }
    return(out)
  } else if (is(pyobj, "numpy.ndarray")) {
    type_len <- reticulate::py_len(pyobj$dtype)
    if (type_len > 1) {
      nrows <- reticulate::py_len(pyobj)
      out <- list()
      for (i in 1:nrows) {
        x <- reticulate::py_call(
	  reticulate::py_get_attr(pyobj, '__getitem__'), i-1L)
        out[[i]] <- python2R(x$tolist())
      }
    }
    return(out)
  # } else if (is(pyobj, "numpy.int32")) {
  # TODO: There dosn't seem to be variable integer precision in R
  }
  out <- reticulate::py_to_r(pyobj)
  return(out)
}
