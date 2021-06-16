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

#' Create an object for sending/receiving messages to/from an yggdrasil channel.
#'
#' This function wraps functions from yggdrasil's [Python interface](interface_py.html), 
#' so refer to that documentation for additional details.
#'
#' @param type The name of the Python interface that should be called
#'   (e.g. [YggInput](interface_py.html#yggdrasil.languages.Python.YggInterface.YggInput),
#'   [YggOutput](interface_py.html#yggdrasil.languages.Python.YggInterface.YggOutput),
#'   [YggRpcClient](interface_py.html#yggdrasil.languages.Python.YggInterface.YggRpcClient),
#'   [YggRpcServer](interface_py.html#yggdrasil.languages.Python.YggInterface.YggRpcServer),
#'   [YggTimesync](interface_py.html#yggdrasil.languages.Python.YggInterface.YggTimesync))
#' @param ... Additional parameters will be passed to the Python interface
#'   function.
#'
#' @returns A Python comm that can be used to send/receive messages via
#'   send/recv methods.
#'
#' @export
#'
#' @examples
#'
#' \dontrun{
#'    in_channel = YggInterface('YggInput', 'input_channel_name')
#'    # Use zeallot '%<-%' syntax to expand multiple variables
#'    c(flag, input) %<-% in_channel$recv()
#' }
#'
#' \dontrun{
#'    out_channel = YggInterface('YggOutput', 'output_channel_name')
#'    flag <- out_channel$send(output1, output2, ...)
#' }
YggInterface <- function(type, ...) {
  # print(reticulate::py_config())
  if (!exists("ygg")) {
    ygg <- reticulate::import('yggdrasil.languages.Python.YggInterface', convert=FALSE)
    assign("ygg", ygg, envir = .GlobalEnv)
  }
  
  varargin <- list(...)
  nargin <- length(varargin)
  arg_names <- names(varargin)
  if (is.null(arg_names)) {
    args <- unname(varargin)
    kwargs <- NULL
  } else {
    first_named <- 0
    for (i in length(arg_names):1) {
      if (arg_names[i] == '') {
        first_named <- i + 1
	break
      }
    }
    if (first_named == 0) {
      args <- NULL
      kwargs <- varargin
    } else {
      args <- unname(varargin[1:(first_named - 1)])
      kwargs <- varargin[first_named:length(varargin)]
    }
  }
  pyobj <- ygg$YggInit(R2python(type, not_bytes=TRUE),
    R2python(args, not_bytes=TRUE), R2python(kwargs, not_bytes=TRUE))
  if (nargin > 0) {
    out <- YggInterfaceClass$new(pyobj)
  } else {
    out <- python2R(pyobj)
  }
  return(out);
}
