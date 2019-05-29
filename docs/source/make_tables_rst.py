import os
from yggdrasil import doctools
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, LinkerBase, ArchiverBase)

schema_dir = os.path.join(os.path.dirname(__file__), 'schema_tables')
class_dir = os.path.join(os.path.dirname(__file__), 'class_tables')
datatype_dir = os.path.join(os.path.dirname(__file__), 'datatype_tables')
dir_list = [schema_dir, class_dir, datatype_dir]
class_list = [ModelDriver, InterpretedModelDriver, CompiledModelDriver,
              CompilerBase, LinkerBase, ArchiverBase,
              MetaschemaType, MetaschemaProperty]


for x in dir_list:
    if not os.path.isdir(x):
        os.mkdir(x)

doctools.write_component_table(fname_dir=schema_dir)
for c in class_list:
    doctools.write_classdocs_table(c, fname_dir=class_dir)
doctools.write_datatype_table(fname_dir=datatype_dir, verbose=True)
