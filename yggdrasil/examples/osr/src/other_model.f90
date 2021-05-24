program main
  use fygg

  ! Declare resulting variables and create buffer for received message
  logical :: timestep_calc
  logical :: ret = .true.
  type(yggcomm) :: timesync, out
  character(len=32) :: arg
  character(len=0), dimension(0) :: dtype_keys
  type(yggdtype), dimension(0) :: dtype_vals
  type(yggdtype) :: out_dtype
  real(kind=8) :: t_step, t_start, t_end, t
  character(len=32) :: t_units
  character(len=20), dimension(:), pointer :: keys
  type(ygggeneric) :: state_send, state_recv, msg
  real(kind=8), pointer :: x
  integer :: i

  call get_command_argument(1, arg)
  read(arg, *) t_step
  call get_command_argument(2, arg)
  read(arg, *) t_units
  call get_command_argument(3, arg)
  write (*, '("Hello from Fortran other_model: timestep ",F10.5," ",A3)') &
       t_step, trim(t_units)
  t_start = 0.0
  t_end = 5.0
  if (t_units.eq."hr") then
     t_end = 24.0 * t_end
  end if
  state_send = init_generic_map()
  state_recv = init_generic_map()
  ret = timestep_calc(t_start, t_units, state_send)
  if (.not.ret) then
     write (*, '("other_model(Fortran): Error in initial timestep &
          &calculation.")')
  end if

  ! Set up connections matching yaml
  ! Timestep synchronization connection will be 'timesync'
  timesync = ygg_timesync("timesync", t_units)
  out_dtype = create_dtype_json_object(0, dtype_keys, dtype_vals, .true.)
  out = ygg_output_type("output", out_dtype)

  ! Initialize state and synchronize with other models
  t = t_start
  ret = ygg_rpc_call(timesync, [yggarg(t), yggarg(state_send)], &
       yggarg(state_recv))
  if (.not.ret) then
     write (*, '("other_model(Fortran): Initial sync failed.")')
     stop 1
  end if
  write (*, '("other_model(Fortran): t = ",F5.1," ",A3)', advance="no") &
       t, adjustl(t_units)
  call generic_map_get_keys(state_recv, keys)
  do i = 1, size(keys)
     call generic_map_get(state_recv, trim(keys(i)), x)
     write (*, '(SP,", ",A," = ",F5.2)', advance="no") &
          trim(keys(i)), x
  end do
  write (*, '("")')

  ! Send initial state to output
  msg = copy_generic(state_recv)
  call generic_map_set(msg, "time", t, t_units)
  ret = ygg_send_var(out, yggarg(msg))
  if (.not.ret) then
     write (*, '("other_model(Fortran): Failed to send initial output &
          &for t=",F10.5,".")') t
     stop 1
  end if
  call free_generic(msg)

  ! Iterate until end
  do while (t.lt.t_end)

     ! Perform calculations to update the state
     t = t + t_step
     ret = timestep_calc(t, t_units, state_send)
     if (.not.ret) then
        write (*, '("other_model(Fortran): Error in timestep &
             &calculation for t = ",F10.5,".")') t
        stop 1
     end if

     ! Synchronize the state
     ret = ygg_rpc_call(timesync, [yggarg(t), yggarg(state_send)], &
          yggarg(state_recv))
     if (.not.ret) then
        write (*, '("other_model(Fortran): sync failed for t=",F10.5,&
             &".")') t
        stop 1
     end if
     write (*, '("other_model(Fortran): t = ",F5.1," ",A3)', advance="no") &
          t, adjustl(t_units)
     call generic_map_get_keys(state_recv, keys)
     do i = 1, size(keys)
        call generic_map_get(state_recv, keys(i), x)
        write (*, '(SP,", ",A," = ",F5.2)', advance="no") &
             trim(keys(i)), x
     end do
     write (*, '("")')

     ! Send output
     msg = copy_generic(state_recv)
     call generic_map_set(msg, "time", t, t_units)
     ret = ygg_send_var(out, yggarg(msg))
     if (.not.ret) then
        write (*, '("other_model(Fortran): Failed to send output for &
             &t=",F10.5,".")') t
        stop 1
     end if
     call free_generic(msg)

  end do

  write (*, '("Goodbye from Fortran other_model")')
  call free_generic(state_send)
  call free_generic(state_recv)

end program main


function timestep_calc(t, t_units, state) result (ret)
  use fygg
  implicit none
  real(kind=8) :: t
  character(len=*) :: t_units
  type(ygggeneric) :: state
  logical :: ret
  ret = .true.
  if (ret) then
     call generic_map_set(state, "carbonAllocation2Roots", 10.0, "g")
     call generic_map_set(state, "saturatedConductivity", 10.0, "cm/day")
  end if
end function timestep_calc
