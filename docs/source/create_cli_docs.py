import os
from yggdrasil.dev import doctools


fname = os.path.join(os.path.dirname(__file__), "cli.rst")
doctools.document_cli(fname)
