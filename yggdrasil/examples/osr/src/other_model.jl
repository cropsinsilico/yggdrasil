using Yggdrasil
using Unitful
using Printf

function timestep_calc(t::Unitful.Quantity)
  state = Dict("carbonAllocation2Roots"=>Unitful.Quantity(10.0, u"g"),
               "saturatedConductivity"=>Unitful.Quantity(10.0, u"cm/d"))
  return state
end

function main(t_step::Float64, t_units::String)

  @printf("Hello from Julia other_model: timestep = %f %s\n", t_step, t_units)
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
    error("other_model(Julia): Initial sync failed.")
  end
  @printf("other_model(Julia): t = %s", t)
  for (k, v) in state
    @printf(", %s = %s", k, v)
  end
  @printf("\n")

  # Send initial state to output
  msg = state
  msg["time"] = t
  flag = out.send(msg)
  if (!flag)
    error(@sprintf("other_model(Julia): Failed to send initial output for t=%s\n", t))
  end

  # Iterate until end
  while (t < t_end)

    # Perform calculations to update the state
    t = t + t_step
    state = timestep_calc(t)

    # Synchronize the state
    ret, state = timesync.call(t, state)
    if (!ret)
      error(@sprintf("other_model(Julia): sync for t=%s failed.", t))
    end
    @printf("other_model(Julia): t = %s", t)
    for (k, v) in state
      @printf(", %s = %s", k, v)
    end
    @printf("\n")

    # Send output
    msg = state
    msg["time"] = t
    flag = out.send(msg)
    if (!flag)
      error(@sprintf("other_model(Julia): Failed to send output for t=%s.", t))
    end

    println("Goodbye from Julia other_model")

  end

end

main(parse(Float64, ARGS[1]), ARGS[2])