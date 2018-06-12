# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = cis_interface
SOURCEDIR     = source
BUILDDIR      = build
REPODIR       = ../../cis_interface_docs
DOXYDIR       = doxy

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.PHONY: ghpages
ghpages: autodoc

	cp -a $(BUILDDIR)/html/. $(REPODIR)/
	cd $(REPODIR) ; git add . ; git commit -m "rebuilt docs" ; git push origin gh-pages

.PHONY: autodoc
autodoc: doxy
	python $(SOURCEDIR)/examples/make_example_rst.py
	sphinx-apidoc -fT -o $(SOURCEDIR)/ ../cis_interface ../cis_interface/tests/* ../cis_interface/*/tests/*
	make html

.PHONY: doxy
doxy:
	cd $(DOXYDIR) ; doxygen doxy.cfg

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
