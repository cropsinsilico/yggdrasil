function new_x = reduce_dim(x)

  if isa(x, 'cell')
    nd = ndims(x);
    if (nd == 1)
      new_x = x;
    elseif ((nd == 2) && (size(x, 2) == 1))
      new_x = transpose(x);
    else
      % Multi dimensional cell array
      new_x = {};
      fmt_str = 'x(%d';
      per_str = '[';
      for i = 1:(nd-1)
	fmt_str = strcat(fmt_str, ',:');
	if (i == 1)
	  per_str = strcat(per_str, sprintf('%d', i+1));
	else
	  per_str = strcat(per_str, sprintf(',%d', i+1));
	end;
      end;
      fmt_str = strcat(fmt_str, ')');
      per_str = strcat(per_str, ',1]');
      per_ord = eval(per_str);
      
      for i = 1:size(x, 1)
	irow = eval(sprintf(fmt_str, i));
	icol = permute(irow, per_ord);
	new_x{i} = reduce_dim(icol);
      end;
    end;
    
  else
    new_x = x;
  end;
  
end
