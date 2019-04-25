

R2python <- function(robj) {
  numpy <- reticulate::import('numpy', convert=FALSE)
  if (is(robj, "list")) {
    robj <- lapply(robj, R2python)
    return(robj)
  } else if (is(robj, "float32")) {
    out <- call_python_method(numpy, 'float32',
      reticulate::r_to_py(float::dbl(robj)))
    return(out)
  } else if (is(robj, "double")) {
    if (length(attributes(robj)) != 0) {
      return(call_python_method(numpy, 'float32',
        reticulate::r_to_py(robj)))
    }
  } else if (is(robj, "integer64")) {
    return(call_python_method(numpy, 'int64',
      reticulate::r_to_py(as.integer(robj))))
  } else if (is(robj, "integer")) {
    return(call_python_method(numpy, 'int32',
      reticulate::r_to_py(robj)))
  }
  return(reticulate::r_to_py(robj))
}
