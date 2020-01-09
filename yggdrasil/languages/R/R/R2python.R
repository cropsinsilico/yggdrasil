

R2python <- function(robj, not_bytes=FALSE) {
  sys <- reticulate::import('sys')
  ver <- reticulate::py_get_attr(sys, 'version_info')
  pyv <- reticulate::py_to_r(reticulate::py_get_attr(ver, 'major'))
  np <- reticulate::import('numpy', convert=FALSE)
  if (is(robj, "list")) {
    robj <- lapply(robj, R2python, not_bytes=not_bytes)
    out <- reticulate::r_to_py(robj)
  } else if (is(robj, "units")) {
    x <- units(robj)
    ygg_units <- reticulate::import('yggdrasil.units', convert=FALSE)
    pyunits <- ygg_units$convert_R_unit_string(R2python(units::deparse_unit(robj), not_bytes=TRUE))
    pydata <- R2python(units::drop_units(robj))
    out <- ygg_units$add_units(pydata, pyunits)
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
  } else if (is(robj, "raw") || is(robj, "ygg_bytes")) {
    ygg_back <- reticulate::import('yggdrasil.backwards', convert=FALSE)
    if (not_bytes) {
      out <- ygg_back$as_str(reticulate::r_to_py(robj))
    } else {
      out <- ygg_back$as_bytes(reticulate::r_to_py(robj))
    }
  } else if (is(robj, "character")) {
    ygg_back <- reticulate::import('yggdrasil.backwards', convert=FALSE)
    out <- ygg_back$as_str(reticulate::r_to_py(robj))
  } else if (is(robj, "data.frame")) {
    out <- reticulate::r_to_py(robj)
  } else if (is.na(robj)) {
    out <- reticulate::r_to_py(NULL)
  } else {
    # print("Default handling for class:")
    # print(class(robj))
    out <- reticulate::r_to_py(robj)
  }
  # print(class(robj))
  # print(class(out))
  return(out)
}
