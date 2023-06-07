function model_function(a, b, c)
  out = Array{Float64}(undef, 3)
  for i = 1:3
    if (a)
      out[i] = b * ((i - 1) ^ c["c1"])
    else
      out[i] = b * ((i - 1) ^ c["c2"])
    end
  end
  return out
end