function model_function(a, b, c, d, e, f) result(retval)
  logical, intent(in) :: a
  real(kind=8), intent(in) :: b
  type(ygggeneric), intent(in) :: c
  logical, intent(out) :: d
  real(kind=8), intent(out) :: e
  real(kind=8), dimension(:), pointer :: f
  real(kind=8), pointer :: cparam
  integer(kind=4) :: i
  logical :: retval

  allocate(f(3))
  d = (.not.a)
  call generic_map_get(c, "c1", cparam)
  e = cparam
  do i = 1, 3
     if (a) then
        call generic_map_get(c, "c1", cparam)
     else
        call generic_map_get(c, "c2", cparam)
     end if
     f(i) = b * ((dble(i - 1) ** cparam))
  end do

  retval = .true.
end function model_function
