subroutine modelB_function2(in_val, in_val_copy, out_val)
  ! Only valid if in_val > 2
  real, intent(in) :: in_val
  real, intent(out) :: in_val_copy
  real, intent(out) :: out_val
  in_val_copy = in_val
  out_val = 2 * (in_val**2)
  print *, "modelB_function2(", in_val, ") = ", out_val
end subroutine modelB_function2
