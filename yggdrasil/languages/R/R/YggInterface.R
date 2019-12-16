fprintf <- function(...) {
  print(sprintf(...))
}


finalize_comm <- function(pyobj) {
  # pyobj$eval_pyobj('atexit', ...)
  pyobj$atexit()
}


call_python_method <- function(pyobj, method_name, ...) {
  method = reticulate::py_get_attr(pyobj, method_name)
  if (length(list(...)) == 0) {
    return(reticulate::py_call(method))
  } else {
    return(reticulate::py_call(method, ...))
  }
}


YggInterfaceClass <- R6::R6Class("YggInterfaceClass", list(
    pyobj = NULL,
    initialize = function(pyobj) {
    	self$pyobj <- pyobj
	reg.finalizer(pyobj, finalize_comm, onexit=TRUE)
    },
    eval_pyobj = function(cmd, ...) {
      args <- list(...)
      nargs <- length(args)
      new_args <- list(self$pyobj, cmd)
      if (nargs > 0) {
        for (i in 1:nargs) {
          new_args[[2 + i]] = R2python(args[[i]])
        }
      }
      py_res <- do.call('call_python_method', new_args)
      r_res <- python2R(py_res)
      return(r_res)
    },
    recv = function(...) {
      return(self$eval_pyobj('recv', ...))
    },
    send = function(...) {
      return(self$eval_pyobj('send', ...))
    },
    recv_dict = function(...) {
      return(self$eval_pyobj('recv_dict', ...))
    },
    send_dict = function(...) {
      return(self$eval_pyobj('send_dict', ...))
    },
    recv_array = function(...) {
      return(self$eval_pyobj('recv_array', ...))
    },
    send_array = function(...) {
      return(self$eval_pyobj('send_array', ...))
    },
    send_eof = function(...) {
      return(self$eval_pyobj('send_eof', ...))
    },
    call = function(...) {
      return(self$eval_pyobj('call', ...))
    # },
    # finalize = function(...) {
    #   return(self$eval_pyobj('atexit', ...))
    }
  )
)

YggInterface <- function(type, ...) {
  # print(reticulate::py_config())
  ygg <- reticulate::import('yggdrasil.languages.Python.YggInterface', convert=FALSE)
  varargin <- list(...)
  nargin <- length(varargin)
  pyobj <- ygg$YggInit(R2python(type, not_bytes=TRUE),
    R2python(varargin, not_bytes=TRUE))
  if (nargin > 0) {
    out <- YggInterfaceClass$new(pyobj)
  } else {
    out <- python2R(pyobj)
  }
  return(out);
}
