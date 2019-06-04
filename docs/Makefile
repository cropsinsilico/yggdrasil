# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = yggdrasil
SOURCEDIR     = source
BUILDDIR      = build
REPODIR       = ../../yggdrasil_docs
DOXYDIR       = doxy

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.PHONY: clean ghpages
ghpages: autodoc

	cp -a $(BUILDDIR)/html/. $(REPODIR)/
	cd $(REPODIR) ; git pull ; git add . ; git commit -m "rebuilt docs" ; git push origin gh-pages

.PHONY: autodoc
autodoc: doxy scripts
	sphinx-apidoc -fT -o $(SOURCEDIR)/ ../yggdrasil # ../yggdrasil/tests/* ../yggdrasil/*/tests/*
	mv $(SOURCEDIR)/yggdrasil.rst $(SOURCEDIR)/yggdrasil.inc
	make html

.PHONY: doxy
doxy:
	cd $(DOXYDIR) ; doxygen doxy.cfg

.PHONY: scripts
scripts:
	python $(SOURCEDIR)/examples/make_example_rst.py
	python $(SOURCEDIR)/make_tables_rst.py

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
