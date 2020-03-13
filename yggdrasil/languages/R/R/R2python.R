

R2python <- function(robj, not_bytes=FALSE) {
  sys <- reticulate::import('sys')
  ver <- reticulate::py_get_attr(sys, 'version_info')
  pyv <- reticulate::py_to_r(reticulate::py_get_attr(ver, 'major'))
  np <- reticulate::import('numpy', convert=FALSE)
  ygg_tool <- reticulate::import('yggdrasil.tools', convert=FALSE)
  if (is.element("ygg_type", names(attributes(robj)))) {
    if (attr(robj, "ygg_type") == "bytes") {
      out <- ygg_tool$str2bytes(reticulate::r_to_py(robj),
        recurse=reticulate::r_to_py(TRUE))
    } else if (attr(robj, "ygg_type") == "float32") {
      out <- call_python_method(np, 'float32',
        reticulate::r_to_py(robj))
    } else if (attr(robj, "ygg_type") == "uint") {
      out <- call_python_method(np, 'uint',
        reticulate::r_to_py(robj))
    } else {
      print(attr(robj, "ygg_type"))
      stop("Unsupported ygg_type.")
    }
  } else if (is(robj, "list")) {
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
    out <- call_python_method(np, 'float64',
      reticulate::r_to_py(robj))
    # }
  } else if (is(robj, "ygg_float32")) {
    out <- call_python_method(np, 'float32',
      reticulate::r_to_py(robj))
  } else if (is(robj, "numeric")) {
    out <- call_python_method(np, 'float64',
      reticulate::r_to_py(robj))
  } else if (is(robj, "raw") || is(robj, "ygg_bytes")) {
    if (not_bytes) {
      out <- ygg_tool$bytes2str(reticulate::r_to_py(robj),
        recurse=reticulate::r_to_py(TRUE))
    } else {
      out <- ygg_tool$str2bytes(reticulate::r_to_py(robj),
        recurse=reticulate::r_to_py(TRUE))
    }
  } else if (is(robj, "character")) {
    out <- ygg_tool$bytes2str(reticulate::r_to_py(robj),
      recurse=R2python(TRUE))
  } else if (is(robj, "data.frame")) {
    out <- reticulate::r_to_py(robj)
    columns <- reticulate::py_get_attr(out, 'columns')
    if (is.element("ygg_types", names(attributes(robj)))) {
      for (i in names(attr(robj, "ygg_types"))) {
        name = call_python_method(columns, '__getitem__',
          R2python(as.integer(as.integer(i) - 1)))
        new_col = call_python_method(out, '__getitem__', name)
        if (attr(robj, "ygg_types")[[i]] == "bytes") {
          new_col = call_python_method(new_col, 'apply', ygg_tool$str2bytes)
	} else if (attr(robj, "ygg_types")[[i]] == "float32") {
          new_col = call_python_method(new_col, 'apply', np$float32)
	}
        call_python_method(out, '__setitem__', name, new_col)
      }
    }
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
