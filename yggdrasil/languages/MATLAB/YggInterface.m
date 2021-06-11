% =============================================================================
%> @brief A simple wrapper for importing Python classes & functions.
%>
%> This function wraps functions from yggdrasil's [Python interface](interface_py.html),
%> so refer to that documentation for additional details.
%>
%> @param type The name of the Python interface that should be called
%>   (e.g. [YggInput](interface_py.html#yggdrasil.languages.Python.YggInterface.YggInput), [YggOutput](interface_py.html#yggdrasil.languages.Python.YggInterface.YggOutput), [YggRpcClient](interface_py.html#yggdrasil.languages.Python.YggInterface.YggRpcClient), [YggRpcServer](interface_py.html#yggdrasil.languages.Python.YggInterface.YggRpcServer), [YggTimesync](interface_py.html#yggdrasil.languages.Python.YggInterface.YggInterface.YggTimesync))
%> @param varargin Additional parameters will be passed to the Python 
%>   interface function.
%>
%> @return out python object returned by the called class/function.
%>
%> ```
%> in_channel = YggInterface('YggInput', 'input_channel_name');
%> [flag, input] = in_channel.recv();
%> ```
%>
%> ```
%> out_channel = YggInterface('YggOutput', 'output_channel_name');
%> flag = out_channel.send(output1, output2, ...);
%> ```
% =============================================================================
function out = YggInterface(type, varargin)
  YggInterface = py.importlib.import_module('yggdrasil.languages.Python.YggInterface');
  keyword_names = {'global_scope', 'format_str', 'infmt', 'outfmt', ...
		   'as_array', 'fmt'};
  args = {};
  kwargs = containers.Map();
  i = 1;
  while (i <= length(varargin));
    if (ischar(varargin{i}));
      if any(strcmp(varargin{i},keyword_names));
        kwargs(varargin{i}) = varargin{i+1};
        i = i + 2;
      else;
        args{length(args)+1} = varargin{i};
        i = i + 1;
      end;
    else;
      i = i + 1;
    end;
  end;
  pyobj = YggInterface.YggInit(type, matlab2python(args), ...
			       matlab2python(kwargs));
  if (nargin > 1);
    out = YggInterfaceClass(pyobj);
  else;
    out = python2matlab(pyobj);
  end;
end
