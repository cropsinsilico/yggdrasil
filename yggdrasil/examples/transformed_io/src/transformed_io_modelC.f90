subroutine modelC_function(in_val, in_val_copy, out_val)
  real(kind=4), intent(in) :: in_val
  real(kind=4), intent(out) :: in_val_copy
  real(kind=4), intent(out) :: out_val
  in_val_copy = in_val
  out_val = 2 * in_val
  write(*, '("modelC_function(",F10.5,") = ",F10.5)') in_val, out_val
end subroutine modelC_function
