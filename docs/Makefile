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
ROXYDIR	      = ../yggdrasil/languages/R

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.PHONY: clean ghpages
ghpages: autodoc

	cp -a $(BUILDDIR)/html/. $(REPODIR)/
	cd $(REPODIR) ; git pull ; git add . ; git commit -m "rebuilt docs" ; git push origin gh-pages

.PHONY: autodoc
autodoc: doxy roxy scripts sphinx
	mv $(SOURCEDIR)/yggdrasil.rst $(SOURCEDIR)/yggdrasil.inc
	make html

.PHONY: sphinx
sphinx:
	sphinx-apidoc -fT -o $(SOURCEDIR)/ ../yggdrasil # ../yggdrasil/tests/* ../yggdrasil/*/tests/*

.PHONY: doxy
doxy:
	cd $(DOXYDIR) ; doxygen doxy.cfg

.PHONY: roxy
roxy:
	cd $(ROXYDIR) ; Rscript -e "library(roxygen2); roxygen2::roxygenise(); library(Rd2md); Rd2markdown(\"man/YggInterface.Rd\", \"man/YggInterface.md\");" ; python -c "import pypandoc; pypandoc.convert_file('man/YggInterface.md', 'rst', outputfile='man/YggInterface.rst')"
	rm $(ROXYDIR)/man/YggInterface.md
	mv $(ROXYDIR)/man/YggInterface.rst $(SOURCEDIR)/advanced/YggInterface_R.rst

.PHONY: scripts
scripts:
	python $(SOURCEDIR)/examples/make_example_rst.py
	python $(SOURCEDIR)/make_tables_rst.py
	python $(SOURCEDIR)/build_schema.py
	python $(SOURCEDIR)/create_cli_docs.py

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
