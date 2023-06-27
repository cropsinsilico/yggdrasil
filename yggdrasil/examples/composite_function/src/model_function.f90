function model_function(a, b, c, out) result(retval)
  logical, intent(in) :: a
  real(kind=8), intent(in) :: b
  type(ygggeneric), intent(in) :: c
  real(kind=8), dimension(:), pointer :: out
  real(kind=8), pointer :: cparam
  integer(kind=4) :: i
  logical :: retval

  allocate(out(3))
  do i = 1, 3
     if (a) then
        call generic_map_get(c, "c1", cparam)
     else
        call generic_map_get(c, "c2", cparam)
     end if
     out(i) = b * ((dble(i - 1) ** cparam))
  end do

  retval = .true.
end function model_function
