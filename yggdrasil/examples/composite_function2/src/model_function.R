model_function <- function(a, b, c) {
  d <- (!a)
  e <- c[["c1"]]
  f <- double(3)
  for (i in 1L:3) {
    if (a) {
      f[[i]] <- b * (i-1)^c[["c1"]]
    } else {
      f[[i]] <- b * (i-1)^c[["c2"]]
    }
  }
  return(list(d,e,f))
}
