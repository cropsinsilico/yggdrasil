

R2python <- function(robj) {
  sys <- reticulate::import('sys')
  ver <- reticulate::py_get_attr(sys, 'version_info')
  pyv <- reticulate::py_to_r(reticulate::py_get_attr(ver, 'major'))
  np <- reticulate::import('numpy', convert=FALSE)
  if (is(robj, "list")) {
    robj <- lapply(robj, R2python)
    out <- reticulate::r_to_py(robj)
  } else if (is(robj, "integer64")) {
    out <- call_python_method(np, 'int64',
      reticulate::r_to_py(as.integer(robj)))
  } else if (is(robj, "integer")) {
    out <- call_python_method(np, 'int32',
      reticulate::r_to_py(robj))
  } else if (is(robj, "float32")) {
    out <- call_python_method(np, 'float32',
      reticulate::r_to_py(float::dbl(robj)))
  } else if (is(robj, "double")) {
    # if (length(attributes(robj)) != 0) {
    out <- call_python_method(np, 'float32',
      reticulate::r_to_py(robj))
    # }
  } else if (is(robj, "numeric")) {
    out <- call_python_method(np, 'float32',
      reticulate::r_to_py(robj))
  } else if (is(robj, "character")) {
    out <- reticulate::r_to_py(charToRaw(robj))
  } else if (is(robj, "data.frame")) {
    out <- reticulate::r_to_py(robj)
  } else {
    # print("Default handling for class:")
    # print(class(robj))
    out <- reticulate::r_to_py(robj)
  }
  # print(class(robj))
  # print(class(out))
  return(out)
}
