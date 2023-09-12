function model_function(a, b, c)
  d = !a
  e = c["c1"]
  f = Array{Float64}(undef, 3)
  for i = 1:3
    if (a)
      f[i] = b * ((i - 1) ^ c["c1"])
    else
      f[i] = b * ((i - 1) ^ c["c2"])
    end
  end
  return d, e, f
end