function modelB_function(in_val, out_val) result(out)
  real(kind=8), intent(in) :: in_val
  real(kind=8), intent(out) :: out_val
  logical :: out
  out = .true.
  out_val = 3 * in_val
  write(*, '("modelB_function(",F10.5,") = (",F10.5,")")') in_val, out_val
end function modelB_function
