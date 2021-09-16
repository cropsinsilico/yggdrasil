import os
import shutil
from yggdrasil import schema, metaschema


schema_dir = os.path.join(os.path.dirname(__file__), 'schema')
if not os.path.isdir(schema_dir):
    os.mkdir(schema_dir)


indent = '    '
s = schema.get_schema()
shutil.copy(metaschema._metaschema_fname,
            os.path.join(schema_dir, 'metaschema.json'))
with open(os.path.join(schema_dir, 'integration.json'), 'w') as fd:
    metaschema.encoder.encode_json(s.schema, fd=fd, indent=indent,
                                   sort_keys=False)
schema.get_json_schema(os.path.join(schema_dir, 'integration_strict.json'),
                       indent=indent)
schema.get_model_form_schema(os.path.join(schema_dir, 'model_form.json'),
                             indent=indent)
