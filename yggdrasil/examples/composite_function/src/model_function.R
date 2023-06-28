model_function <- function(a, b, c) {
  out <- double(3)
  for (i in 1L:3) {
    if (a) {
      out[[i]] <- b * (i-1)^c[["c1"]]
    } else {
      out[[i]] <- b * (i-1)^c[["c2"]]
    }
  }
  return(out)
}
