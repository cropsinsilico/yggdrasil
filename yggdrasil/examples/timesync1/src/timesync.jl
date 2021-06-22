using Yggdrasil
using Unitful
using Printf

function timestep_calc(t::Unitful.Quantity)
  state = Dict("x"=>sin(2.0 * t / Unitful.Quantity(10.0, u"d")),
               "y"=>cos(2.0 * t / Unitful.Quantity(5.0, u"d")))
  return state
end

function main(t_step::Float64, t_units::String)

  @printf("Hello from Julia timesync: timestep = %f %s\n", t_step, t_units)
  t_step = Unitful.Quantity(t_step, Unitful.uparse(t_units))
  t_start = Unitful.Quantity(0.0, Unitful.uparse(t_units))
  t_end = Unitful.Quantity(1.0, u"d")
  state = timestep_calc(t_start)

  # Set up connections matching yaml
  # Timestep synchronization connection will default to 'timesync'
  timesync = Yggdrasil.YggInterface("YggTimesync", "timesync")
  out = Yggdrasil.YggInterface("YggOutput", "output")

  # Initialize state and synchronize with other models
  t = t_start
  ret, state = timesync.call(t, state)
  if (!ret)
    error("timesync(Julia): Initial sync failed.")
  end
  @printf("timesync(Julia): t = %s, x = %s, y = %s\n", t, state["x"], state["y"])

  # Send initial state to output
  msg = state
  msg["time"] = t
  flag = out.send(msg)
  if (!flag)
    error(@sprintf("timesync(Julia): Failed to send initial output for t=%s\n", t))
  end

  # Iterate until end
  while (t < t_end)

    # Perform calculations to update the state
    t = t + t_step
    state = timestep_calc(t)

    # Synchronize the state
    ret, state = timesync.call(t, state)
    if (!ret)
      error(@sprintf("timesync(Julia): sync for t=%s failed.", t))
    end
    @printf("timesync(Julia): t = %s, x = %s, y = %s\n", t, state["x"], state["y"])

    # Send output
    msg = state
    msg["time"] = t
    flag = out.send(msg)
    if (!flag)
      error(@sprintf("timesync(Julia): Failed to send output for t=%s.", t))
    end

  end

  println("Goodbye from Julia timesync")

end

main(parse(Float64, ARGS[1]), ARGS[2])