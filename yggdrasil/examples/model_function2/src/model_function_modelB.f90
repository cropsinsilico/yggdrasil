function model_function(x) result(y)
  real(kind=4), dimension(:), intent(in) :: x
  real(kind=4), dimension(:), allocatable :: y
  integer :: i
  allocate(y(size(x, 1)))
  do i = 1, size(x, 1)
     y(i) = x(i) + 2.0
  end do
  write(*, '("Model B: [")', advance="no")
  do i = 1, size(x, 1)
     write(*, '(F10.5," ")', advance="no") x(i)
  end do
  write(*, '("] -> [")', advance="no")
  do i = 1, size(y, 1)
     write(*, '(F10.5," ")', advance="no") y(i)
  end do
  write(*, '("]")')
end function model_function
