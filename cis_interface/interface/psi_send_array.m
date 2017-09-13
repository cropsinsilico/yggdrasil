function psi_send_array(psi_output, mat);

  % TODO: Handle mixed types
  % Single array of single type
  data_size = size(mat);
  transpose = mat';
  pyarr = py.numpy.reshape(transpose(:)', data_size);

  psi_output.send_array(pyarr);

end;
