uint_to_R <- function(pyobj) {
  tmp <- reticulate::py_to_r(pyobj)
  out <- as.integer(tmp)
  dim(out) <- dim(tmp)
  return(out)
}
