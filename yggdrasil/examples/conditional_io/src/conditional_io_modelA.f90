subroutine modelA_function(in_val, out_val)
  real, intent(in) :: in_val
  real, intent(out) :: out_val
  out_val = in_val
  print *, "modelA_function(", in_val, ") = ", out_val
end subroutine modelA_function
