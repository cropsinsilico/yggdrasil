library(yggdrasil)


timestep_calc <- function(t, xname, yname, zname) {
  state = list()
  state[[xname]] = sinpi(2.0 * t / units::set_units(10.0, 'day', mode="standard"))
  state[[yname]] = cospi(2.0 * t / units::set_units(5.0, 'day', mode="standard"))
  if (xname == 'xvar') {
    state[[xname]] = state[[xname]] / 2.0
  }
  if (zname == 'a') {
    state[[zname]] = sinpi(2.0 * t / units::set_units(2.5, 'day', model="standard"))
  } else {
    state[[zname]] = cospi(2.0 * t / units::set_units(2.5, 'day', model="standard"))
  }
  return(state)
}

main <- function(t_step, t_units, model) {

  fprintf('Hello from R timesync: timestep = %f %s', t_step, t_units)
  t_step <- units::set_units(t_step, t_units, mode="standard")
  t_start <- units::set_units(0.0, t_units, mode="standard")
  t_end <- units::set_units(5.0, 'day', mode="standard")
  if (model == 'A') {
    xname = 'x'
    yname = 'y'
    zname = 'a'
  } else {
    xname = 'xvar'
    yname = 'yvar'
    zname = 'b'
  }
  state <- timestep_calc(t_start, xname, yname, zname)

  # Set up connections matching yaml
  # Timestep synchronization connection will be 'statesync'
  timesync <- YggInterface('YggTimesync', 'statesync')
  out <- YggInterface('YggOutput', 'output')

  # Initialize state and synchronize with other models
  t <- t_start
  c(ret, result) %<-% timesync$call(t, state)
  if (!ret) {
    stop('timesync(R): Initial sync failed.')
  }
  state <- result[[1]]
  fprintf('timesync(R): t = %5.1f %-1s',
          units::drop_units(t), units::deparse_unit(t))
  for (key in names(state)) {
    fprintf(', %s = %+ 5.2f', key, state[[key]])
  }
  fprintf('\n')

  # Send initial state to output
  msg = state
  msg[['time']] = t
  flag <- out$send(msg)
  if (!flag) {
    stop(sprintf('timesync(R): Failed to send initial output for t=%s', t))
  }

  # Iterate until end
  while (t < t_end) {
        
    # Perform calculations to update the state
    t <- t + t_step
    state <- timestep_calc(t, xname, yname, zname)

    # Synchronize the state
    c(ret, result) %<-% timesync$call(t, state)
    if (!ret) {
      stop(sprintf('timesync(R): sync for t=%f failed.', t))
    }
    state <- result[[1]]
    fprintf('timesync(R): t = %5.1f %-1s',
            units::drop_units(t), units::deparse_unit(t))
    for (key in names(state)) {
      fprintf(', %s = %+ 5.2f', key, state[[key]])
    }
    fprintf('\n')

    # Send output
    msg = state
    msg[['time']] = t
    flag <- out$send(msg)
    if (!flag) {
      stop(sprintf('timesync(R): Failed to send output for t=%s.', t))
    }
  }

  print('Goodbye from R timesync')
  
}


args = commandArgs(trailingOnly=TRUE)
main(as.double(args[[1]]), args[[2]], args[[3]])