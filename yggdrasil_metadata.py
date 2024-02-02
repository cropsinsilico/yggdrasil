# TODO: Access utils/manage_requirements.py directly
import json


def dynamic_metadata(field, settings=None):
    _allowed = ["dependencies", "optional-dependencies", "scripts"]
    out = None
    if settings:
        raise RuntimeError("Inline settings are not supported by this plugin")
    if field not in _allowed:
        raise RuntimeError(f"This plugin only supports dynamic "
                           f"{_allowed} (not {field})")
    if field == "dependencies":
        with open("requirements.txt", "r") as fd:
            out = [x.split('#')[0].strip() for x in fd.read().splitlines()]
    elif field == "optional-dependencies":
        with open("utils/requirements/requirements_extras.json", "r") as fd:
            out = json.load(fd)
    elif field == "scripts":
        with open("console_scripts.txt", "r") as fd:
            out = {k: v for k, v in
                   [x.split('=') for x in fd.read().splitlines()]}
    return out
