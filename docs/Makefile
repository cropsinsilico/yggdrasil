# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = cis_interface
SOURCEDIR     = source
BUILDDIR      = build
REPODIR       = ../../cropsinsilico.github.io/cis_interface
DOXYDIR       = doxy

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

.PHONY: ghpages
ghpages: clean autodoc
	cp -a $(BUILDDIR)/html/. $(REPODIR)/
	cd $(REPODIR) ; git pull ; git add . ; git commit -m "rebuilt docs" ; git push origin master

.PHONY: autodoc
autodoc: doxy
	python $(SOURCEDIR)/examples/make_example_rst.py
	sphinx-apidoc -fT -o $(SOURCEDIR)/ ../cis_interface
	mv $(SOURCEDIR)/cis_interface.rst $(SOURCEDIR)/cis_interface.inc
	make html
	make mvjekyll

.PHONY: doxy
doxy:
	cd $(DOXYDIR) ; doxygen doxy.cfg

.PHONY: mvjekyll
mvjekyll:
	$(foreach jdir, \
	    images modules static sources, \
	    mv $(BUILDDIR)/html/_$(jdir) $(BUILDDIR)/html/$(jdir); \
	    $(foreach jext, html, \
		find build/html/ -iname "*.$(jext)" -type f -exec sed -Ei '.bak' 's|(["\/])_($(jdir)["\/])|\1\2|g' "{}" +; \
		find build/html/ -iname "*.$(jext).bak" -type f -delete;))

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
