fprintf <- function(...) {
  print(sprintf(...))
}


YggInterfaceClass <- setRefClass("YggInterfaceClass",
  fields=list(pyobj="ANY"),
  methods=list(
    eval_pyobj = function(cmd, ...) {
      args <- list(...)
      nargs <- length(args)
      rapply(args, R2python, classes='ANY', how='replace')
      arg_name <- vector("list", length = nargs)
      if (nargs > 0) {
        for (i in 1:nargs) {
          arg_name[i] = sprintf('args[[%d]]', i)
        }
      }
      py_cmd <- sprintf('pyobj$%s(%s)', cmd, paste(arg_name, sep=',', collapse=','))
      py_res <- eval(parse(text=py_cmd))
      r_res <- python2R(py_res)
      return(r_res)
    },
    recv = function(...) {
      return(eval_pyobj('recv', ...))
    },
    send = function(...) {
      return(eval_pyobj('send', ...))
    },
    recv_dict = function(...) {
      return(eval_pyobj('recv_dict', ...))
    },
    send_dict = function(...) {
      return(eval_pyobj('send_dict', ...))
    },
    recv_array = function(...) {
      return(eval_pyobj('recv_array', ...))
    },
    send_array = function(...) {
      return(eval_pyobj('send_array', ...))
    },
    send_eof = function(...) {
      return(eval_pyobj('send_eof', ...))
    },
    call = function(...) {
      return(eval_pyobj('call', ...))
    }
  )
)

YggInterface <- function(type, ...) {
  ygg <- reticulate::import('yggdrasil.interface.YggInterface', convert=FALSE)
  varargin <- list(...)
  nargin <- length(varargin)
  pyobj <- ygg$YggInit(type, varargin)
  if (nargin > 0) {
    out <- YggInterfaceClass(pyobj=pyobj)
  } else {
    out <- python2R(pyobj)
  }
  return(out);
}
