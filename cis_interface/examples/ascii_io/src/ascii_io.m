% Input & output to an ASCII file line by line 
in_file = YggInterface('YggAsciiFileInput', 'inputM_file');
out_file = YggInterface('YggAsciiFileOutput', 'outputM_file');
% Input & output from a table row by row
in_table = YggInterface('YggAsciiTableInput', 'inputM_table');
out_table = YggInterface('YggAsciiTableOutput', 'outputM_table', ...
			 '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n');
% Input & output from a table as an array
in_array = YggInterface('YggAsciiArrayInput', 'inputM_array');
out_array = YggInterface('YggAsciiArrayOutput', 'outputM_array', ...
			 '%5s\t%ld\t%3.1f\t%3.1lf%+3.1lfj\n');

% Read lines from ASCII text file until end of file is reached.
% As each line is received, it is then sent to the output ASCII file.
disp('ascii_io(M): Receiving/sending ASCII file.');
flag = true;
while flag
  % Receive a single line
  [flag, line] = in_file.recv();
  if flag
    % If the receive was succesful, send the line to output
    fprintf('File: %s', char(line));
    ret = out_file.send(line);
    if (~ret);
      error('ascii_io(M): ERROR SENDING LINE');
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
flag = true;
while flag
  % Receive a single row
  [flag, line] = in_table.recv();
  if flag
    % If the receive was succesful, send the values to output.
    % Formatting is taken care of on the output driver side.
    fprintf('Table: %s, %d, %3.1f, %3.1f%+3.1fi\n', char(line{1}), ...
	    line{2}, line{3}, real(line{4}), imag(line{4}));
    ret = out_table.send(line);
    if (~ret);
      error('ascii_io(M): ERROR SENDING ROW');
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
flag = true;
while flag
  [flag, arr] = in_array.recv_array();
  if flag
    nr = size(arr, 1);
    fprintf('Array: (%d rows)\n', nr);
    % Print each line in the array
    for i = 1:nr
      fprintf('%5s, %d, %3.1f, %3.1f%+3.1fi\n', ...
              char(arr{i,1}), arr{i,2}, arr{i,3}, ...
              real(arr{i,4}), imag(arr{i,4}));
    end;
    % Send the array to output. Formatting is handled on the output driver side.
    ret = out_array.send_array(arr);
    if (~ret);
      error('ascii_io(M): ERROR SENDING ARRAY');
      break;
    end;
  else
    % If the receive was not succesful, send the end-of-file message to
    % close the output file.
    disp('End of array input (Matlab)');
  end;
end;
