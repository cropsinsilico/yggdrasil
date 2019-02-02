import copy


_conversion_registry = {}


def register_conversion(from_type, to_type):
    r"""Register a conversion function for going between types.

    Args:
        from_type (str): Name of type being converted from.
        to_type (str): Name of type being converted to.

    Returns:
        function: Decorator that will register the conversion.

    """
    global _conversion_registry
    key = (from_type, to_type)
    if key in _conversion_registry:
        raise ValueError("Conversion '%s' to '%s' already in registry." % key)

    def decorator(function):
        _conversion_registry[key] = function
        return function

    return decorator


def get_conversion(from_type, to_type):
    r"""Get a conversion function for moving from one type to the other.

    Args:
        from_type (str): Name of type being converted from.
        to_type (str): Name of type being converted to.

    Returns:
         function: Method for performing the conversion. If there is no known
             conversion between the specified types, None will be returned.

    """
    key = (from_type, to_type)
    return _conversion_registry.get(key, None)


@register_conversion('ply', 'obj')
def ply2obj(ply):
    r"""Convert a Ply object to an Obj object.

    Args:
        ply (dict): Ply type object.

    Returns:
        dict: Obj data container.

    """
    out = {'material': ply['material']}
    # Vertices
    if 'vertices' in ply:
        out['vertices'] = copy.deepcopy(ply['vertices'])
    # Faces
    if 'faces' in ply:
        out['faces'] = []
        for f in ply['faces']:
            out['faces'].append([{'vertex_index': q} for q in f['vertex_index']])
    # Edges
    if 'edges' in ply:
        out['lines'] = []
        for e in ply['edges']:
            x = [{'vertex_index': e['vertex%d' % q]} for q in [1, 2]]
            out['lines'].append(x)
    return out


@register_conversion('obj', 'ply')
def obj2ply(obj):
    r"""Convert an Obj object to a Ply object.

    Args:
        obj (dict): Obj type object.

    Returns:
        dict: Ply data container.

    """
    out = {'material': obj['material']}
    # Vertices
    if 'vertices' in obj:
        out['vertices'] = copy.deepcopy(obj['vertices'])
        for v in out['vertices']:
            if 'w' in v:
                del v['w']
    # Faces
    if 'faces' in obj:
        out['faces'] = []
        for f in obj['faces']:
            out['faces'].append({'vertex_index': [x['vertex_index'] for x in f]})
    # Edges
    if 'lines' in obj:
        out['edges'] = []
        for e in obj['lines']:
            # Ply dosn't have arbitrary edges
            for ii in range(len(e) - 1):
                iedge = {'vertex1': e[ii]['vertex_index'],
                         'vertex2': e[ii + 1]['vertex_index']}
                out['edges'].append(iedge)
    return out
