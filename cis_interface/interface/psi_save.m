function psi_save(psi_output, varargin)

  nvar = length(varargin);
  data_dict = py.dict();
  for k = 1:nvar
    data_dict{varargin{k}} = matlab2python(evalin('base', varargin{k}));
  end
  psi_output.send(data_dict);

end
