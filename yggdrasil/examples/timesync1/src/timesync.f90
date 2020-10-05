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
  type(ygggeneric) :: state, msg
  real(kind=8), pointer :: x, y

  call get_command_argument(1, arg)
  read(arg, *) t_step
  call get_command_argument(2, arg)
  read(arg, *) t_units
  write (*, '("Hello from Fortran timesync: timestep ",F10.5," ",A)') &
       t_step, trim(t_units)
  t_start = 0.0
  t_end = 5.0
  if (t_units.eq."hr") then
     t_end = 24.0 * t_end
  end if
  state = init_generic_map()
  ret = timestep_calc(t_start, t_units, state)
  if (.not.ret) then
     write (*, '("timesync(Fortran): Error in initial timestep &
          &calculation.")')
  end if

  ! Set up connections matching yaml
  ! Timestep synchronization connection will be 'timesync'
  timesync = ygg_timesync("timesync", t_units)
  out_dtype = create_dtype_json_object(0, dtype_keys, dtype_vals, .true.)
  out = ygg_output_type("output", out_dtype)

  ! Initialize state and synchronize with other models
  t = t_start
  ret = ygg_rpc_call(timesync, [yggarg(t), yggarg(state)], &
       yggarg(state))
  if (.not.ret) then
     write (*, '("timesync(Fortran): Initial sync failed.")')
     stop 1
  end if
  call generic_map_get(state, "x", x)
  call generic_map_get(state, "y", y)
  write (*, '("timesync(Fortran): t = ",F5.1," ",A3,", x = ",&
       &SP,F5.2,", y = ",F5.2)') t, adjustl(t_units), x, y

  ! Send initial state to output
  msg = copy_generic(state)
  call generic_map_set(msg, "time", t, t_units)
  ret = ygg_send_var(out, yggarg(msg))
  if (.not.ret) then
     write (*, '("timesync(Fortran): Failed to send initial output &
          &for t=",F10.5,".")') t
     stop 1
  end if
  call free_generic(msg)

  ! Iterate until end
  do while (t.lt.t_end)

     ! Perform calculations to update the state
     t = t + t_step
     ret = timestep_calc(t, t_units, state)
     if (.not.ret) then
        write (*, '("timesync(Fortran): Error in timestep &
             &calculation for t = ",F10.5,".")') t
        stop 1
     end if

     ! Synchronize the state
     ret = ygg_rpc_call(timesync, [yggarg(t), yggarg(state)], &
          yggarg(state))
     if (.not.ret) then
        write (*, '("timesync(Fortran): sync failed for t=",F10.5,&
             &".")') t
        stop 1
     end if
     call generic_map_get(state, "x", x)
     call generic_map_get(state, "y", y)
     write (*, '("timesync(Fortran): t = ",F5.1," ",A3,", x = ",&
          &SP,F5.2,", y = ",F5.2)') t, adjustl(t_units), x, y

     ! Send output
     msg = copy_generic(state)
     call generic_map_set(msg, "time", t, t_units)
     ret = ygg_send_var(out, yggarg(msg))
     if (.not.ret) then
        write (*, '("timesync(Fortran): Failed to send output for &
             &t=",F10.5,".")') t
        stop 1
     end if
     call free_generic(msg)

  end do

  write (*, '("Goodbye from Fortran timesync")')
  call free_generic(state)

end program main


function timestep_calc(t, t_units, state) result (ret)
  use fygg
  implicit none
  real(kind=8) :: t
  character(len=*) :: t_units
  type(ygggeneric) :: state
  logical :: ret
  real(kind=8) :: x_period = 10.0  ! Days
  real(kind=8) :: y_period = 10.0  ! Days
  real(kind=8) :: x, y
  ret = .true.
  if (t_units.eq."day") then
     ! No conversion necessary
  else if (t_units.eq."hr") then
     x_period = x_period * 24.0
     y_period = y_period * 24.0
  else
     write (*, '("timestep_calc: Unsupported unit ''",A,"''")') t_units
     ret = .false.
  end if
  if (ret) then
     x = sin(2.0 * PI_8 * t / x_period)
     y = cos(2.0 * PI_8 * t / y_period)
     call generic_map_set(state, "x", x)
     call generic_map_set(state, "y", y)
  end if
end function timestep_calc
