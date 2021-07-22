model_function <- function(x) {
  y <- x + units::set_units(1.0, "g", mode="standard")
  print(sprintf("Model A: %f -> %f", x, y))
  return(y)
}
