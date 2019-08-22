.onAttach <- function(libname, pkgname) {
  if (is_attached("reticulate")) {
    reticulate::use_condaenv(Sys.getenv("CONDA_DEFAULT_ENV"))
  } else {
    setHook(packageEvent("reticulate", "attach"), function(...) {
      reticulate::use_condaenv(Sys.getenv("CONDA_DEFAULT_ENV"))
    })
  }
}

.onDetach <- function(libpath) {
  setHook(packageEvent("reticulate", "attach"), NULL, "replace")
}

is_attached <- function(pkg) paste0("package:", pkg) %in% search()
