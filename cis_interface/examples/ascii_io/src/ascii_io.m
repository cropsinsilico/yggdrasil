% Input & output to an ASCII file line by line 
in_file = PsiInterface('PsiAsciiFileInput', 'inputM_file');
out_file = PsiInterface('PsiAsciiFileOutput', 'outputM_file');
% Input & output from a table row by row
in_table = PsiInterface('PsiAsciiTableInput', 'inputM_table');
out_table = PsiInterface('PsiAsciiTableOutput', 'outputM_table', ...
			 '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n');
% Input & output from a table as an array
in_array = PsiInterface('PsiAsciiTableInput', 'inputM_array');
out_array = PsiInterface('PsiAsciiTableOutput', 'outputM_array', ...
			 '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n');

% Read lines from ASCII text file until end of file is reached.
% As each line is received, it is then sent to the output ASCII file.
disp('ascii_io(M): Receiving/sending ASCII file.')
res = py.tuple({logical(1), logical(1)});
while res{1}
  % Receive a single line
  res = in_file.recv_line();
  if res{1}
    % If the receive was succesful, send the line to output
    fprintf('File: %s', char(res{2}));
    ret = out_file.send_line(res{2});
    if (~ret);
      disp('ascii_io(M): ERROR SENDING LINE');
      break;
    end;
  else
    % If the receive was not succesful, send the end-of-file message to
    % close the output file. 
    disp('End of file input (Matlab)');
    out_file.send_eof();
  end;
end;

% Read rows from ASCII table until end of file is reached.
% As each row is received, it is then sent to the output ASCII table
res = py.tuple({logical(1), logical(1)});
while res{1}
  % Receive a single row
  res = in_table.recv_row();
  if res{1}
    % If the receive was succesful, send the values to output.
    % Formatting is taken care of on the output driver side.
    line = res{2};
    fprintf('Table: %s, %d, %3.1f, %3.1f%+3.1f\n', char(line{1}), ...
	    line{2}, line{3}, real(line{4}), imag(line{4}));
    ret = out_table.send_row(res{2});
    if (~ret);
      disp('ascii_io(M): ERROR SENDING ROW');
      break;
    end;
  else
    % If the receive was not succesful, send the end-of-file message to
    % close the output file.
    disp('End of table input (Matlab)');
    out_table.send_eof();
  end;
end;

% Read entire array from ASCII table into an array
res = in_array.recv_array();
if (~res{1});
  disp('ascii_io(M): ERROR RECVING ARRAY');
  exit(-1);
end;
arr = res{2};
fprintf('Array: (%d rows)\n', arr.size);
% Print each line in the array
for i = 1:arr.size
  line = arr.item(i-1);
  fprintf('%5s, %d, %3.1f, %3.1f%+3.1f\n', char(line{1}), line{2}, line{3}, ...
	  real(line{4}), imag(line{4}));
end;
% Send the array to output. Formatting is handled on the output driver side.
ret = out_array.send_array(arr);
if (~ret);
  disp('ascii_io(M): ERROR SENDING ARRAY');
end;


exit(0);
