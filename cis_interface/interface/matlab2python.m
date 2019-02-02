function x_py = matlab2python(x_ml)
  if isa(x_ml, 'py.object')
    x_py = x_ml;
  elseif isa(x_ml, 'containers.Map');
    keys = matlab2python(x_ml.keys);
    vals = matlab2python(x_ml.values);
    for i = 1:length(keys)
      keys{i} = py.str(keys{i}.decode('utf-8'));
    end
    x_py = py.dict(py.zip(keys, vals));
  elseif isscalar(x_ml);
    if isa(x_ml, 'complex');
      x_py = x_ml;
    elseif isa(x_ml, 'single');
      x_py = py.numpy.float32(py.float(double(x_ml)));
    elseif isa(x_ml, 'double');
      x_py = py.numpy.float64(py.float(x_ml));
    elseif isa(x_ml, 'float');
      if isreal(x_ml)
	x_py = py.float(x_ml);
      else
	x_py = x_ml;
      end
    elseif isa(x_ml, 'int32');
      x_py = py.numpy.int32(py.int(x_ml));
    elseif isa(x_ml, 'int64');
      x_py = py.numpy.int64(py.int(x_ml));
    elseif isa(x_ml, 'integer');
      x_py = py.int(x_ml);
    elseif isa(x_ml, 'string');
      x_py = py.str(x_ml);
    elseif isa(x_ml, 'char');
      try
	x_py = py.str(x_ml);
      catch
	x_py = py.unicode(x_ml);
      end
      x_py = x_py.encode('utf-8');
    elseif isa(x_ml, 'logical');
      x_py = py.bool(x_ml);
    elseif isa(x_ml, 'struct');
      x_py = py.dict(x_ml);
    elseif isa(x_ml, 'cell');
      for i = 1:length(x_ml)
	x_ml{i} = matlab2python(x_ml{i});
      end
      x_py = py.list(x_ml);
    else;
      disp('Could not convert scalar matlab type to python type');
      disp(x_ml);
      disp(class(x_ml));
      x_py = x_ml;
    end;
  elseif isvector(x_ml);
    if isa(x_ml, 'string');
      x_py = py.str(x_ml);
    elseif isa(x_ml, 'char');
      try
        x_py = py.str(x_ml);
      catch
        x_py = py.unicode(x_ml);
      end;
      x_py = x_py.encode('utf-8');
    elseif isa(x_ml, 'cell');
      for i = 1:length(x_ml)
	x_ml{i} = matlab2python(x_ml{i});
      end
      x_py = py.list(x_ml);
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
    else
      data_size = int16(size(x_ml));
      transpose = x_ml';
      x_py = py.numpy.reshape(transpose(:)', data_size).tolist();
    end;
  else;
    disp('Could not convert matlab type to python type');
    disp(x_ml);
    disp(class(x_ml));
    x_py = x_ml;
  end;
end
