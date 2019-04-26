

python2R <- function(pyobj) {
  # print(class(pyobj))
  np <- reticulate::import('numpy', convert=FALSE)
  if (is(pyobj, "python.builtin.tuple")
      || is(pyobj, "python.builtin.list")) {
    pyobj_len <- reticulate::py_len(pyobj)
    out <- list()
    for (i in 1L:pyobj_len) {
      x <- python2R(reticulate::py_call(
        reticulate::py_get_attr(pyobj, '__getitem__'), i-1L))
      out[[i]] <- x
    }
    return(out)
  } else if (is(pyobj, "python.builtin.dict")) {
    out <- list()
    pyobj_len <- reticulate::py_len(pyobj)
    keys <- reticulate::iterate(
      call_python_method(pyobj, 'keys'))
    for (i in 1L:pyobj_len) {
      k <- keys[[i]]
      x <- python2R(call_python_method(pyobj, 'get', k))
      out[[reticulate::py_to_r(k)]] <- x
    }
    return(out)
  } else if (is(pyobj, "numpy.float32")) {
    # out <- as.single(reticulate::py_to_r(pyobj))
    out <- float::fl(reticulate::py_to_r(pyobj))
    return(out)
  } else if (is(pyobj, "numpy.int64")) {
    out <- bit64::as.integer64(reticulate::py_to_r(pyobj))
    return(out)
  } else if (is(pyobj, "python.builtin.bytes")) {
    pyobj <- pyobj$decode('utf-8')
  # TODO: There dosn't seem to be variable integer precision in R
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
  }
  out <- reticulate::py_to_r(pyobj)
  return(out)
}
