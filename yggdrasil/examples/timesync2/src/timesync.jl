using Yggdrasil
using Unitful
using Printf

function timestep_calc(t::Unitful.Quantity, model::String)
  state = Dict()
  if (model == "A")
    state["x"] = sin(2.0 * t / Unitful.Quantity(10.0, u"d"))
    state["y"] = cos(2.0 * t / Unitful.Quantity(5.0, u"d"))
    state["z1"] = -cos(2.0 * t / Unitful.Quantity(20.0, u"d"))
    state["z2"] = -cos(2.0 * t / Unitful.Quantity(20.0, u"d"))
    state["a"] = sin(2.0 * t / Unitful.Quantity(2.5, u"d"))
  else
    state["xvar"] = sin(2.0 * t / Unitful.Quantity(10.0, u"d"))
    state["yvar"] = cos(2.0 * t / Unitful.Quantity(5.0, u"d"))
    state["z"] = -2.0 * cos(2.0 * t / Unitful.Quantity(20.0, u"d"))
    state["b"] = cos(2.0 * t / Unitful.Quantity(2.5, u"d"))
  end
  return state
end

function main(t_step::Float64, t_units::String, model::String)

  @printf("Hello from Julia timesync: timestep = %f %s\n", t_step, t_units)
  t_step = Unitful.Quantity(t_step, Unitful.uparse(t_units))
  t_start = Unitful.Quantity(0.0, Unitful.uparse(t_units))
  t_end = Unitful.Quantity(1.0, u"d")
  state = timestep_calc(t_start, model)

  # Set up connections matching yaml
  # Timestep synchronization connection will default to 'timesync'
  timesync = Yggdrasil.YggInterface("YggTimesync", "statesync")
  out = Yggdrasil.YggInterface("YggOutput", "output")

  # Initialize state and synchronize with other models
  t = t_start
  ret, state = timesync.call(t, state)
  if (!ret)
    error("timesync(Julia): Initial sync failed.")
  end
  @printf("timesync(Julia): t = %s", t)
  for (k, v) in state
    @printf(", %s = %s", k, v)
  end
  @printf("\n")

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
    state = timestep_calc(t, model)

    # Synchronize the state
    ret, state = timesync.call(t, state)
    if (!ret)
      error(@sprintf("timesync(Julia): sync for t=%s failed.", t))
    end
    @printf("timesync(Julia): t = %s", t)
    for (k, v) in state
      @printf(", %s = %s", k, v)
    end
    @printf("\n")

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

main(parse(Float64, ARGS[1]), ARGS[2], ARGS[3])