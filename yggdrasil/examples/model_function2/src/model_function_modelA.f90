function model_function(x) result(y)
  real(kind=4), intent(in) :: x
  real(kind=4) :: y
  y = x + 1.0
  write(*, '("Model A: ",F10.5," -> ",F10.5)') x, y
end function model_function
