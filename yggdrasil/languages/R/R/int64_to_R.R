int64_to_R <- function(pyobj) {
  tmp <- reticulate::py_to_r(pyobj)
  out <- bit64::as.integer64(tmp)
  dim(out) <- dim(tmp)
  return(out)
}
