PsiInterface = py.importlib.import_module('cis_interface.interface.PsiInterface');

% IO Objects
in_file = PsiInterface.PsiAsciiFileInput('inputM_file');
out_file = PsiInterface.PsiAsciiFileOutput('outputM_file');
in_table = PsiInterface.PsiAsciiTableInput('inputM_table');
out_table = PsiInterface.PsiAsciiTableOutput('outputM_table', '%5s\t%ld\t%f\n');
in_array = PsiInterface.PsiAsciiTableInput('inputM_array');
out_array = PsiInterface.PsiAsciiTableOutput('outputM_array', '%5s\t%ld\t%f\n');
	  
% Generic text file
res = py.tuple({logical(1), logical(1)});
while res{1}
  res = in_file.recv_line();
  if res{1}
    disp(res);
    out_file.send_line(res{2});
  else
    disp('End of file input (Matlab)');
    out_file.send_eof();
  end;
end;

% Table
res = py.tuple({logical(1), logical(1)});
while res{1}
  res = in_table.recv_row();
  if res{1}
    disp(res);
    out_table.send_row(res{2});
  else
    disp('End of table input (Matlab)');
    out_table.send_eof();
  end;
end;

% Array
res = in_array.recv_array();
disp(res);
out_array.send_array(res{2});

exit();
