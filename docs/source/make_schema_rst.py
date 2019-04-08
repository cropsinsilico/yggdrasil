import os
import textwrap
from yggdrasil.components import _registry
from yggdrasil.schema import get_schema


s = get_schema()


def prop2table(prop, include_required=False, column_order=None,
               wrapped_columns=None, sort_properties=True,
               key_column_name='Option', prune_empty_columns=False):
    r"""Convert a dictionary of component options to a table.

    Args:
        prop (dict): Dictionary of properties that should go in the table.
        include_required (bool, optional): If True, a Required column is
            included. Defaults to False.
        column_order (list, optional): List specifying the order that fields
            should be added to the table as columns. Defaults to None and
            is set to [key_column_name, 'Type', 'Required', 'Description'].
            If a column is missing from an entry in prop, an empty value will
            be added to the table in its place. Columns in prop that are not
            in column_order are appended to column_order in sorted order.
        wrapped_columns (dict, optional): Dictionary specifying fields that
            should be wrapped as columns and the widths that the corresponding
            column should be wrapped to. Defaults to {'Description': 80}.
        sort_properties (bool, optional): If True, the entries in prop are
            added as rows in the order determined by sorting on the keys.
            If False, the order will be determine by prop (which is not
            deterministic if a Python 2 dictionary). Defaults to True.
        key_column_name (str, optional): Title that should be used for the
            first column containing the keys in prop. Defaults to 'Option'.
        prune_empty_columns (bool, optional): If True, empty columns will be
            removed. If False, they will be included. Defaults to False.

    Returns:
        list: Lines comprising the table.

    """
    if wrapped_columns is None:
        wrapped_columns = {'Description': 80}
    # Determine column order
    if column_order is None:
        column_order = [key_column_name, 'Type', 'Required', 'Description']
        if not include_required:
            column_order.remove('Required')
    # Create dictionary of columns
    columns = {k: [] for k in column_order}
    pos = 0
    prop_order = list(prop.keys())
    if sort_properties:
        prop_order = sorted(prop_order)
    for k in prop_order:
        v = prop[k]
        for pk in v.keys():
            if pk not in columns:
                columns[pk] = pos * ['']
        for pk in columns.keys():
            if pk == key_column_name:
                columns[key_column_name].append(k)
            else:
                columns[pk].append(str(v.get(pk, '')))
        pos += 1
    # Add non-standard fields
    for k in sorted(columns.keys()):
        if k not in column_order:
            column_order.append(k)
    # Prune empty columns
    column_widths = {}
    for k in list(columns.keys()):
        if len(columns[k]) == 0:
            column_widths[k] = 0
        else:
            column_widths[k] = len(max(columns[k], key=len))
        if prune_empty_columns and (column_widths[k] == 0):
            del column_widths[k]
            del columns[k]
            column_order.remove(k)
    # Get sizes that include headers and wrapping
    for k in columns.keys():
        if k in wrapped_columns:
            w = wrapped_columns[k]
        else:
            w = column_widths[k]
        column_widths[k] = max(w, len(k))
    # Create format string
    column_sep = '   '
    column_format = column_sep.join(['%-' + str(column_widths[k]) + 's'
                                     for k in column_order])
    divider = column_sep.join(['=' * column_widths[k]
                               for k in column_order])
    header = column_format % tuple(column_order)
    # Table
    if len(columns) == 0:
        pos = 0
    else:
        pos = len(columns[list(columns.keys())[0]])
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


def get_subtype_prop(comp):
    r"""Get a dictionary of subtype options and descriptions for components of
    the specified type.

    Args:
        comp (str): Name of component type to get info for.

    Returns:
        dict: Mapping from component subtype option to option description.

    """
    out = {}
    subtype_key = s[comp].subtype_key
    for x, subtypes in s[comp].schema_subtypes.items():
        s_comp = s[comp].get_subtype_schema(x, unique=True)
        subt = subtypes[0]
        out[subt] = {
            'Description': s_comp['properties'][subtype_key].get('description', '')}
        if len(subtypes) > 1:
            out[subt]['Aliases'] = subtypes[1:]
        if s_comp['properties'][subtype_key].get('default', None) in subtypes:
            out[subt]['Description'] = '[DEFAULT] ' + out[subt]['Description']
    return out


def get_general_prop(comp, subtype_ref=None):
    r"""Get a dictionary of component options and descriptions that apply
    to all components of the specified type.

    Args:
        comp (str): Name of component type to get info for.
        subtype_ref (str, optional): Reference for the subtype table for the
            specified component that should be used in the description for the
            subtype property. Defaults to None and is ignored.

    Returns:
        dict: Mapping from component option to option description.

    """
    out = {}
    subtype_key = s[comp].subtype_key
    s_comp = s[comp].get_subtype_schema('base', unique=True)
    for k, v in s_comp['properties'].items():
        t = v.get('type', '')
        if isinstance(t, (list, tuple)):
            t = t[0]
        out[k] = {'Type': t,
                  'Required': '',
                  'Description': v.get('description', '')}
        if (subtype_ref is not None) and (k == subtype_key):
            out[k]['Description'] += (' (Options described :ref:`here <%s>`)'
                                      % subtype_ref)
        if k in s_comp['required']:
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
    subtype_key = s[comp].subtype_key
    for x in s[comp].classes:
        s_comp = s[comp].get_subtype_schema(x, unique=True)
        for k, v in s_comp['properties'].items():
            if k == subtype_key:
                continue
            if k not in out:
                out[k] = {'Type': v.get('type', ''),
                          'Required': '',
                          'Description': v.get('description', '')}
                if k in s_comp.get('required', []):
                    out[k]['Required'] = 'X'
            if k not in out_apply:
                out_apply[k] = []
            out_apply[k] += s_comp['properties'][subtype_key]['enum']
    # Add valid for field
    for k, v in out.items():
        v['Valid for %s of' % subtype_key] = list(set(out_apply[k]))
    return out
    

def write_component_schema_table(comp):
    r"""Write a schema as three tables in restructured text format. One table
    will contain general options applicable to all components of the specified
    type, one table will contain options applicable to only certain components,
    and one table will contain descriptions of the component subtypes.

    Args:
        comp (str): Name of component type to create tables for.

    Returns:
        tuple: The files where the three tables were saved.

    """
    src_dir = os.path.dirname(__file__)
    fname_gen = os.path.join(src_dir, 'schema_table_%s_general.rst' % comp)
    fname_spe = os.path.join(src_dir, 'schema_table_%s_specific.rst' % comp)
    fname_sub = os.path.join(src_dir, 'schema_table_%s_subtype.rst' % comp)
    # Write subtype
    lines_sub = (
        ['.. _schema_table_%s_subtype_rst:' % comp, '']
        + prop2table(
            get_subtype_prop(comp),
            key_column_name=s[comp].subtype_key,
            prune_empty_columns=True))
    with open(fname_sub, 'w') as fd:
        fd.write('\n'.join(lines_sub))
    # Write general
    lines_gen = (
        ['.. _schema_table_%s_general_rst:' % comp, '']
        + prop2table(
            get_general_prop(comp,
                             subtype_ref='schema_table_%s_subtype_rst' % comp),
            include_required=True))
    with open(fname_gen, 'w') as fd:
        fd.write('\n'.join(lines_gen))
    # Write specific
    lines_spe = (
        ['.. _schema_table_%s_specific_rst:' % comp, '']
        + prop2table(
            get_specific_prop(comp),
            prune_empty_columns=True))
    with open(fname_spe, 'w') as fd:
        fd.write('\n'.join(lines_spe))
    return fname_gen, fname_spe, fname_sub


def write_all_schema_tables():
    r"""Write tables for all schema components."""
    for k in s.keys():
        print('Writing %s' % k)
        print(write_component_schema_table(k))


write_all_schema_tables()
