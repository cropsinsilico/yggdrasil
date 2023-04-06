
function yggarr2ygggeneric(input) result(out)
  type(yggarr) :: input
  type(ygggeneric) :: out
  out%obj = input%obj
end function yggarr2ygggeneric
  
function yggmap2ygggeneric(input) result(out)
  type(yggmap) :: input
  type(ygggeneric) :: out
  out%obj = input%obj
end function yggmap2ygggeneric
  
function yggschema2ygggeneric(input) result(out)
  type(yggschema) :: input
  type(ygggeneric) :: out
  out%obj = input%obj
end function yggschema2ygggeneric
  
function yggpyinst2ygggeneric(input) result(out)
  type(yggpyinst) :: input
  type(ygggeneric) :: out
  out%obj = input%obj
end function yggpyinst2ygggeneric

function ygggeneric2yggarr(input) result(out)
  type(ygggeneric) :: input
  type(yggarr) :: out
  out%obj = input%obj
end function ygggeneric2yggarr

function ygggeneric2yggmap(input) result(out)
  type(ygggeneric) :: input
  type(yggmap) :: out
  out%obj = input%obj
end function ygggeneric2yggmap

function ygggeneric2yggschema(input) result(out)
  type(ygggeneric) :: input
  type(yggschema) :: out
  out%obj = input%obj
end function ygggeneric2yggschema

function ygggeneric2yggpyinst(input) result(out)
  type(ygggeneric) :: input
  type(yggpyinst) :: out
  out%obj = input%obj
end function ygggeneric2yggpyinst

function yggpython2yggpython(input) result(out)
  type(yggpython) :: input
  type(yggpython) :: out
  out%obj = input%obj
end function yggpython2yggpython

function yggpyfunc2yggpython(input) result(out)
  type(yggpyfunc) :: input
  type(yggpython) :: out
  out%obj = input%obj
end function yggpyfunc2yggpython

function yggpython2yggpyfunc(input) result(out)
  type(yggpython) :: input
  type(yggpyfunc) :: out
  out%obj = input%obj
end function yggpython2yggpyfunc
