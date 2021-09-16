import os
from yggdrasil import doctools


fname = os.path.join(os.path.dirname(__file__), "cli.rst")
doctools.document_cli(fname)
