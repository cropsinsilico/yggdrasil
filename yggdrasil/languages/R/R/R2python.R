

R2python <- function(robj) {
  numpy <- reticulate::import('numpy', convert=FALSE)
  if (is(robj, "list")) {
    robj <- lapply(robj, R2python)
    out <- reticulate::r_to_py(robj)
  } else if (is(robj, "integer64")) {
    out <- call_python_method(numpy, 'int64',
      reticulate::r_to_py(as.integer(robj)))
  } else if (is(robj, "integer")) {
    out <- call_python_method(numpy, 'int32',
      reticulate::r_to_py(robj))
  } else if (is(robj, "float32")) {
    out <- call_python_method(numpy, 'float32',
      reticulate::r_to_py(float::dbl(robj)))
  } else if (is(robj, "double")) {
    # if (length(attributes(robj)) != 0) {
    out <- call_python_method(numpy, 'float32',
      reticulate::r_to_py(robj))
    # }
  } else if (is(robj, "numeric")) {
    out <- call_python_method(numpy, 'float32',
      reticulate::r_to_py(robj))
  } else {
    out <- reticulate::r_to_py(robj)
  }
  # print(class(robj))
  # print(class(out))
  return(out)
}
