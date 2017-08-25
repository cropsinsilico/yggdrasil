function mat = psi_recv_array(psi_input)

  % TODO: Handle mixed data types
  out = psi_input.recv_array();
  res = out{1};
  if res
    pyarr = out{2};
    double(py.array.array('d', pyarr.item(0)));
    nrows = pyarr.size;
    ncols = length(pyarr.dtype.names);
    mat = zeros(nrows, ncols);
    for i=1:nrows
      mat(i, :) = double(py.array.array('d', pyarr.item(i-1)));
    end

  else
    mat = zeros();
  end

end
