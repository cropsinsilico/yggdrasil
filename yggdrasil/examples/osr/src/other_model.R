library(yggdrasil)


timestep_calc <- function(t) {
  state = list(carbonAllocation2Roots=units::set_units(10.0, 'g', mode="standard"),
               saturatedConductivity=units::set_units(10.0, 'cm/day', mode="standard"))
  return(state)
}

main <- function(t_step, t_units) {

  fprintf('Hello from R other_model: timestep = %f %s', t_step, t_units)
  t_step <- units::set_units(t_step, t_units, mode="standard")
  t_start <- units::set_units(0.0, t_units, mode="standard")
  t_end <- units::set_units(1.0, 'day', mode="standard")
  state <- timestep_calc(t_start)

  # Set up connections matching yaml
  # Timestep synchronization connection will default to 'timesync'
  timesync <- YggInterface('YggTimesync', 'timesync')
  out <- YggInterface('YggOutput', 'output')

  # Initialize state and synchronize with other models
  t <- t_start
  c(ret, state) %<-% timesync$call(t, state)
  if (!ret) {
    stop('other_model(R): Initial sync failed.')
  }
  fprintf('other_model(R): t = %5.1f %-1s',
          units::drop_units(t), units::deparse_unit(t))
  for (k in names(state)) {
    fprintf(', %s = %+ 5.2f', k, state[[k]])
  }
  fprintf('\n')

  # Send initial state to output
  msg = state
  msg[['time']] = t
  flag <- out$send(msg)
  if (!flag) {
    stop(sprintf('other_model(R): Failed to send initial output for t=%s', t))
  }

  # Iterate until end
  while (t < t_end) {
        
    # Perform calculations to update the state
    t <- t + t_step
    state <- timestep_calc(t)

    # Synchronize the state
    c(ret, state) %<-% timesync$call(t, state)
    if (!ret) {
      stop(sprintf('other_model(R): sync for t=%f failed.', t))
    }
    fprintf('other_model(R): t = %5.1f %-1s',
            units::drop_units(t), units::deparse_unit(t))
    for (k in names(state)) {
      fprintf(', %s = %+ 5.2f', k, state[[k]])
    }
    fprintf('\n')

    # Send output
    msg = state
    msg[['time']] = t
    flag <- out$send(msg)
    if (!flag) {
      stop(sprintf('other_model(R): Failed to send output for t=%s.', t))
    }
  }

  print('Goodbye from R other_model')
  
}


args = commandArgs(trailingOnly=TRUE)
main(as.double(args[[1]]), args[[2]])
