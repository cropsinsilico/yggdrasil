import os
import textwrap
from yggdrasil.components import _registry
from yggdrasil.schema import get_schema


s = get_schema()


def prop2table(prop, include_required=False):
    r"""Convert a dictionary of component options to a table.

    Args:
        prop (dict): Dictionary of properties that should go in the table.
        include_required (bool, optional): If True, a Required column is
            included. Defaults to False.

    Returns:
        list: Lines comprising the table.

    """
    wrapped_columns = {'Description': 80}
    column_order = ['Option', 'Type', 'Required', 'Description']
    if not include_required:
        column_order.remove('Required')
    columns = {k: [] for k in column_order}
    pos = 0
    for k in sorted(prop.keys()):
        v = prop[k]
        for pk in v.keys():
            if pk not in columns:
                columns[pk] = pos * ['']
        for pk in columns.keys():
            if pk == 'Option':
                columns['Option'].append(k)
            else:
                columns[pk].append(str(v.get(pk, '')))
        pos += 1
    # Add non-standard fields
    for k in sorted(columns.keys()):
        if k not in column_order:
            column_order.append(k)
    # Get sizes
    column_widths = {}
    for k in columns.keys():
        if k in wrapped_columns:
            w = wrapped_columns[k]
        else:
            w = len(max([k] + columns[k], key=len))
        column_widths[k] = w
    # Create format string
    column_sep = '   '
    column_format = column_sep.join(['%-' + str(column_widths[k]) + 's'
                                     for k in column_order])
    divider = column_sep.join(['=' * column_widths[k]
                               for k in column_order])
    header = column_format % tuple(column_order)
    # Table
    pos = len(columns['Description'])
    lines = [divider, header, divider]
    for i in range(pos):
        row = []
        max_row_len = 1
        for k in column_order:
            if k in wrapped_columns:
                row.append(textwrap.wrap(columns[k][i], wrapped_columns[k]))
            else:
                row.append([columns[k][i]])
            max_row_len = max(max_row_len, len(row[-1]))
        for j in range(len(row)):
            row[j] += (max_row_len - len(row[j])) * ['']
        for k in range(max_row_len):
            lines.append(column_format % tuple([row[j][k] for j in range(len(row))]))
    lines.append(divider)
    return lines


def get_general_prop(comp):
    r"""Get a dictionary of component options and descriptions that apply
    to all components of the specified type.

    Args:
        comp (str): Name of component type to get info for.

    Returns:
        dict: Mapping from component option to option description.

    """
    out = {}
    sfull_comp = s[comp].full_schema
    s_comp = sfull_comp['allOf'][0]['properties']
    req = sfull_comp['allOf'][0]['required']
    for k, v in s_comp.items():
        t = v.get('type', '')
        if isinstance(t, (list, tuple)):
            t = t[0]
        out[k] = {'Type': t,
                  'Required': '',
                  'Description': v.get('description', '')}
        if k in req:
            out[k]['Required'] = 'X'
    return out


def get_specific_prop(comp):
    r"""Get a dictionary of component options and descriptions that don't apply
    to all components of the specified type.

    Args:
        comp (str): Name of component type to get info for.

    Returns:
        dict: Mapping from component option to option description.

    """
    out_apply = {}
    out = {}
    subtype_keys = s[comp].subtype_keys
    assert(len(subtype_keys) == 1)
    subtype_key = subtype_keys[0]
    sfull_comp = s[comp].full_schema
    for subcomp in sfull_comp['allOf'][1]['anyOf']:
        s_comp = subcomp['properties']
        req = subcomp.get('required', [])
        subtypes = s_comp[subtype_key]['enum']
        for k, v in s_comp.items():
            if k in subtype_keys:
                continue
            if k in sfull_comp['allOf'][0]['properties']:
                continue
            if k not in out:
                out[k] = {'Type': v.get('type', ''),
                          'Required': '',
                          'Description': v.get('description', '')}
                if k in req:
                    out[k]['Required'] = 'X'
            if k not in out_apply:
                out_apply[k] = []
            out_apply[k] += subtypes
    # Add valid for field
    for k, v in out.items():
        v['Valid for %s of' % subtype_key] = list(set(out_apply[k]))
    return out
    

def write_component_schema_table(comp):
    r"""Write a schema as two tables in restructured text format. One table will
    contain general options applicable to all components of the specified type
    and the other table will contain options applicable to only certain
    components.

    Args:
        comp (str): Name of component type to create tables for.

    Returns:
        tuple: The file where the two tables were saved.

    """
    src_dir = os.path.dirname(__file__)
    fname_gen = os.path.join(src_dir, 'schema_table_%s_general.rst' % comp)
    fname_spe = os.path.join(src_dir, 'schema_table_%s_specific.rst' % comp)
    # Write general
    lines_gen = (['.. _schema_table_%s_general_rst:' % comp, '']
                 + prop2table(get_general_prop(comp), include_required=True))
    with open(fname_gen, 'w') as fd:
        fd.write('\n'.join(lines_gen))
    # Write general
    lines_spe = (['.. _schema_table_%s_specific_rst:' % comp, '']
                 + prop2table(get_specific_prop(comp)))
    with open(fname_spe, 'w') as fd:
        fd.write('\n'.join(lines_spe))
    return fname_gen, fname_spe


def write_all_schema_tables():
    r"""Write tables for all schema components."""
    for k in s.keys():
        print('Writing %s' % k)
        print(write_component_schema_table(k))


write_all_schema_tables()
