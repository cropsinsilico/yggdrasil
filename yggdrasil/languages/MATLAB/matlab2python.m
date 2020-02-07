% =============================================================================
%> @brief A wrapper for conversion from Matlab datatypes to Python datatypes.
%>
%> This function takes a Matlab object as input and converts it into an
%> equivalent Python object.
%>
%> @param x_ml Matlab object that should be converted.
%>
%> @return x_py Python version of x_ml.
% =============================================================================
function x_py = matlab2python(x_ml)
  [version, executable, isloaded] = pyversion;
  if isa(x_ml, 'py.object')
    x_py = x_ml;
  elseif isa(x_ml, 'containers.Map');
    keys = matlab2python(x_ml.keys);
    vals = matlab2python(x_ml.values);
    for i = 1:length(keys)
      keys{i} = py.str(keys{i});  %.decode('utf-8'));
    end
    x_py = py.dict(py.zip(keys, vals));
  elseif isscalar(x_ml);
    if isa(x_ml, 'complex');
      x_py = x_ml;
    elseif isa(x_ml, 'single');
      if isreal(x_ml)
        x_py = py.numpy.float32(py.float(double(x_ml)));
      else
        x_py = x_ml;
      end
    elseif isa(x_ml, 'double');
      if isreal(x_ml)
        x_py = py.numpy.float64(py.float(x_ml));
      else
        x_py = x_ml;
      end;
    elseif isa(x_ml, 'float');
      if isreal(x_ml)
	x_py = py.float(x_ml);
      else
	x_py = x_ml;
      end
    elseif isa(x_ml, 'uint8');
      x_py = py.numpy.uint8(py.int(x_ml));
    elseif isa(x_ml, 'uint32');
      x_py = py.numpy.uint32(py.int(x_ml));
    elseif isa(x_ml, 'uint64');
      x_py = py.numpy.uint64(py.int(x_ml));
    elseif isa(x_ml, 'int32');
      x_py = py.numpy.int32(py.int(x_ml));
    elseif isa(x_ml, 'int64');
      x_py = py.int(x_ml);
    elseif isa(x_ml, 'integer');
      x_py = py.int(x_ml);
    elseif isa(x_ml, 'string');
      try
	x_py = py.str(x_ml);
      catch
	x_py = py.unicode(x_ml);
      end
      x_py = x_py.encode('utf-8');
    elseif isa(x_ml, 'char');
      try
	x_py = py.str(x_ml);
      catch
	x_py = py.unicode(x_ml);
      end
    elseif isa(x_ml, 'logical');
      x_py = py.bool(x_ml);
    elseif isa(x_ml, 'struct');
      x_py = py.dict(x_ml);
    elseif isa(x_ml, 'cell');
      for i = 1:length(x_ml)
	x_ml{i} = matlab2python(x_ml{i});
      end
      x_py = py.list(x_ml);
    elseif isa(x_ml, 'sym')
      [x_ml_data, x_ml_unit] = separateUnits(x_ml);
      x_py_data = matlab2python(double(subs(x_ml_data)));
      x_py_unit = matlab2python(symunit2str(x_ml_unit));
      if (x_ml_unit == 1)
        x_py = x_py_data;
      else
        x_py = py.yggdrasil.units.add_units(x_py_data, x_py_unit);
      end
    else;
      disp('Could not convert scalar matlab type to python type');
      disp(x_ml);
      disp(class(x_ml));
      x_py = x_ml;
    end;
  elseif isvector(x_ml);
    if (isa(x_ml, 'string') || isa(x_ml, 'double'));
      x_py = py.list();  
      for i = 1:length(x_ml)
	x_py.append(matlab2python(x_ml(i)));
      end
      x_py = py.numpy.array(x_py);
    elseif isa(x_ml, 'char');
      try
        x_py = py.str(x_ml);
      catch
        x_py = py.unicode(x_ml);
      end;
    elseif isa(x_ml, 'cell');
      [nr, nc] = size(x_ml);
      for i = 1:nr
	for j = 1:nc
	  if (isa(x_ml{i, j}, 'char') && (length(x_ml{i, j}) == 0))
            x_ml{i, j} = py.str('');
          else
	    x_ml{i, j} = matlab2python(x_ml{i, j});
          end;
	end;
      end;
      x_py = py.list(x_ml);
    elseif isa(x_ml, 'single');
      if isreal(x_ml)
        x_py = py.numpy.array(x_ml, 'float32');
      else
        x_py = py.numpy.array(x_ml, 'complex64');
      end
    elseif isa(x_ml, 'double');
      if isreal(x_ml)
        x_py = py.numpy.array(x_ml, 'float64');
      else
        x_py = py.numpy.array(x_ml, 'complex128');
      end;
    elseif isa(x_ml, 'float');
      if isreal(x_ml)
        x_py = py.numpy.array(x_ml, 'float');
      else
        x_py = py.numpy.array(x_ml, 'complex');
      end
    elseif isa(x_ml, 'uint8');
      x_py = py.numpy.array(x_ml, 'uint8');
    elseif isa(x_ml, 'uint32');
      x_py = py.numpy.array(x_ml, 'uint32');
    elseif isa(x_ml, 'uint64');
      x_py = py.numpy.array(x_ml, 'uint64');
    elseif isa(x_ml, 'int32');
      x_py = py.numpy.array(x_ml, 'int32');
    elseif isa(x_ml, 'int64');
      x_py = py.numpy.array(x_ml, 'int64');
    elseif isa(x_ml, 'integer');
      x_py = py.numpy.array(x_ml, 'int');
    else
      x_py = py.numpy.array(x_ml);
    end;
  elseif ismatrix(x_ml);
    if isa(x_ml, 'cell')
      if isa(x_ml{1}, 'numeric')
	cl0 = class(x_ml{1});
	all_match = true;
	for i = 2:numel(x_ml)
	  if (~isa(x_ml, cl0))
	    all_match = false;
	    break;
	  end;
	end;
      else
	all_match = false;
      end;
      if all_match
        x_py = matlab2python(cell2mat(x_ml))
      else
	x_py = matlab2python(reduce_dim(x_ml));
      end;
    elseif isa(x_ml, 'table')
      arr_dict = py.dict();
      order = py.list();
      names = x_ml.Properties.VariableNames;
      for i = 1:length(names)
	iname = names{i};
        iarr = matlab2python(x_ml{:, iname});
        arr_dict{py.str(iname)} = iarr;
        order.append(py.str(iname));
      end
      x_py = py.yggdrasil.serialize.dict2numpy(arr_dict, order);
    else
      data_size = int16(size(x_ml));
      transpose = x_ml';
      x_py = py.numpy.reshape(transpose(:)', data_size).tolist();
    end;
  else
    disp('Could not convert matlab type to python type');
    disp(x_ml);
    disp(class(x_ml));
    x_py = x_ml;
  end;
end
