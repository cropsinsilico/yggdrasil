model_function <- function(x) {
  y <- x + units::set_units(2.0, "g", mode="standard")
  print(sprintf("Model B: %f -> %f", x, y))
  return(y)
}
