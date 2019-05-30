import os
from yggdrasil import doctools
from yggdrasil.metaschema.datatypes.MetaschemaType import MetaschemaType
from yggdrasil.metaschema.datatypes.tests.test_MetaschemaType import (
    TestMetaschemaType)
from yggdrasil.metaschema.properties.MetaschemaProperty import MetaschemaProperty
from yggdrasil.drivers.ModelDriver import ModelDriver
from yggdrasil.drivers.InterpretedModelDriver import InterpretedModelDriver
from yggdrasil.drivers.CompiledModelDriver import (
    CompiledModelDriver, CompilerBase, LinkerBase, ArchiverBase)

tables_dir = os.path.join(os.path.dirname(__file__), 'tables')
dir_list = [tables_dir]
class_list = [ModelDriver, InterpretedModelDriver, CompiledModelDriver,
              CompilerBase, LinkerBase, ArchiverBase,
              MetaschemaType, MetaschemaProperty]


for x in dir_list:
    if not os.path.isdir(x):
        os.mkdir(x)

        
doctools.write_component_table(fname_dir=tables_dir, verbose=False)
for c in class_list:
    doctools.write_classdocs_table(c, fname_dir=tables_dir, verbose=False)
doctools.write_datatype_table(fname_dir=tables_dir, verbose=False)
doctools.write_datatype_mapping_table(fname_dir=tables_dir, verbose=False)
doctools.write_comm_devnotes_table(fname_dir=tables_dir, verbose=False)
