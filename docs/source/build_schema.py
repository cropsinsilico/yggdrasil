import os
import json
from yggdrasil import schema, rapidjson
from yggdrasil.serialize.JSONSerialize import encode_json


schema_dir = os.path.join(os.path.dirname(__file__), 'schema')
if not os.path.isdir(schema_dir):
    os.mkdir(schema_dir)


indent = '    '
s = schema.get_schema()
with open(os.path.join(schema_dir, 'metaschema.json'), 'w') as fd:
    json.dump(rapidjson.get_metaschema(), fd, indent=indent)
with open(os.path.join(schema_dir, 'integration.json'), 'w') as fd:
    encode_json(s.schema, fd=fd, indent=indent, sort_keys=False)
schema.get_json_schema(
    os.path.join(schema_dir, 'integration_strict.json'),
    indent=indent)
schema.get_model_form_schema(
    os.path.join(schema_dir, 'model_form.json'),
    indent=indent)
