

python2R <- function(pyobj) {
  # builtins <- reticulate::import_builtins()
  sys <- reticulate::import('sys')
  ver <- reticulate::py_get_attr(sys, 'version_info')
  pyv <- reticulate::py_to_r(reticulate::py_get_attr(ver, 'major'))
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
  } else if (is(pyobj, "pint.quantity.Quantity")
             || is(pyobj, "unyt.array.unyt_quantity")
             || is(pyobj, "unyt.array.unyt_array")) {
    ygg_units <- reticulate::import('yggdrasil.units', convert=FALSE)
    robj_data <- python2R(ygg_units$get_data(pyobj))
    robj_units <- python2R(ygg_units$get_units(pyobj))
    out <- units::set_units(robj_data, robj_units, mode="standard")
  } else if (is(pyobj, "numpy.uint")) {
    out <- uint_to_R(pyobj)
  } else if (is(pyobj, "numpy.float32")) {
    out <- float32_to_R(pyobj)
  } else if (is(pyobj, "numpy.int32")) {
    out <- int32_to_R(pyobj)
  } else if (is(pyobj, "numpy.int64")) {
    out <- int64_to_R(pyobj)
  } else if (is(pyobj, "python.builtin.str") && (pyv == 2)) {
    out <- reticulate::py_to_r(pyobj)
  } else if (is(pyobj, "python.builtin.bytes")) {
    out <- bytes_to_R(pyobj)
  } else if (is(pyobj, "pandas.core.frame.DataFrame")) {
    out <- reticulate::py_to_r(pyobj)
    ncol_data = ncol(out)
    columns <- reticulate::py_get_attr(pyobj, 'columns')
    for (i in 1:ncol_data) {
      icol_name <- call_python_method(columns, '__getitem__',
        R2python(as.integer(i - 1)))
      icol <- reticulate::py_get_attr(call_python_method(pyobj, '__getitem__',
        icol_name), 'values')
      out[, i] <- python2R(icol)
    }
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
    } else {
      dtype <- reticulate::py_to_r(pyobj$dtype$name)
      if (substring(dtype, 1, nchar("uint")) == "uint") {
        out <- uint_to_R(pyobj)
      } else if (dtype == "int32") {
        out <- int32_to_R(pyobj)
      } else if (dtype == "int64") {
        out <- int64_to_R(pyobj)
      } else if (dtype == "float32") {
        out <- float32_to_R(pyobj)
      } else if (substring(dtype, 1, nchar("bytes")) == "bytes") {
        out <- bytes_to_R(pyobj)
      } else {
        out <- reticulate::py_to_r(pyobj)
      }
    }
  } else if (is(pyobj, "python.builtin.NoneType")) {
    out <- NA
  } else {
    # print("Default handling for class:")
    # print(class(pyobj))
    out <- reticulate::py_to_r(pyobj)
  }
  # print(class(pyobj))
  # print(class(out))
  return(out)
}
