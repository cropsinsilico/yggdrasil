classdef YggInterfaceClass
  properties
    pyobj
  end
  methods
    function obj = YggInterfaceClass(pyobj)
      if nargin > 0
	obj.pyobj = pyobj;
      end
    end
    function delete(obj)
      obj.pyobj.language_atexit();
    end
    function ml_res = eval_pyobj(obj, cmd, nargs, args)
      py_cmd = sprintf('obj.pyobj.%s(', cmd);
      for i = 1:nargs
	if (i == 1)
	  iarg_str = sprintf('args{%d}', i);
	else
	  iarg_str = sprintf(',args{%d}', i);
	end
	py_cmd = strcat(py_cmd, iarg_str);
	args{i} = matlab2python(args{i});
      end
      py_cmd = strcat(py_cmd, ')');
      py_res = eval(py_cmd);
      ml_res = python2matlab(py_res);
    end
    function [flag, res] = recv(obj, varargin)
      ml_res = obj.eval_pyobj('recv', nargin-1, varargin);
      flag = ml_res{1};
      res = ml_res{2};
    end
    function flag = send(obj, varargin)
      flag = obj.eval_pyobj('send', nargin-1, varargin);
    end
    function [flag, res] = recv_dict(obj, varargin)
      ml_res = obj.eval_pyobj('recv_dict', nargin-1, varargin);
      flag = ml_res{1};
      res = ml_res{2};
    end
    function flag = send_dict(obj, varargin)
      flag = obj.eval_pyobj('send_dict', nargin-1, varargin);
    end
    function [flag, res] = recv_array(obj, varargin)
      ml_res = obj.eval_pyobj('recv_array', nargin-1, varargin);
      flag = ml_res{1};
      res = ml_res{2};
    end
    function flag = send_array(obj, varargin)
      flag = obj.eval_pyobj('send_array', nargin-1, varargin);
    end
    function flag = send_eof(obj, varargin)
      flag = obj.eval_pyobj('send_eof', nargin-1, varargin);
    end
    function [flag, res] = call(obj, varargin)
      ml_res = obj.eval_pyobj('call', nargin-1, varargin);
      flag = ml_res{1};
      res = ml_res{2};
    end
  end
end
