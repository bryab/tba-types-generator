import textwrap
import typing
import re

MAX_WIDTH = 100
RESERVED_WORDS = ['void']


def _convert_single_type(type_name):
    # Cleanup whitespace and remove pointer/reference symbols
    type_name = re.sub('[\*&]', '', type_name)
    # FIXME: May want static (but is not part of type in TS)
    type_name = type_name.replace("virtual", "").replace("static", "")
    type_name = type_name.strip()
    if "unsigned" in type_name or type_name == "integer":
        type_name = "int"
    if not type_name:
        type_name = "void"
    if type_name == "...":
        type_name = "any"
    assert type_name != "virtual"
    # Convert native types to Javascript types
    if type_name == 'String':
        type_name = 'string'
    elif type_name == 'bool':
        type_name = 'boolean'
    return type_name


def convert_type(type_name):
    if ' or ' in type_name:
        types = [t.strip() for t in type_name.split(' or ')]
    else:
        types = [type_name]
    types = [_convert_single_type(t) for t in types]
    if len(types) == 1:
        return types[0]
    else:
        return '|'.join(types)


def convert_desc(desc):
    desc = desc.split("\n")
    new_desc = []
    for line in desc:
        line = line.strip()
        if line:
            new_desc.append(line)
    return '\n'.join(new_desc)


VALUE_LITERAL_MAP = {
    'QScriptValue()': '{}',
    'String()': '""'
}


def convert_value(value):
    return VALUE_LITERAL_MAP.get(value, value)


def write_jsdoc(f, obj):
    f.write("\n/**")
    # f.write("\n* {}".format(obj['name']))
    if "desc" in obj:
        for line in obj['desc'].split("\n"):
            desc = '\n* '.join(textwrap.wrap(line, width=MAX_WIDTH))
            f.write("\n* {}".format(desc))
    for param in obj.get('params', []):
        f.write("\n* @param {{{0}}}".format(convert_type(param['type'])))
        if 'default' in param:
            f.write(" [{0}={1}]".format(param['name'],
                    convert_value(param['default'])))
        else:
            f.write(" {0}".format(param['name']))
        if 'desc' in param:
            f.write(" {0}".format(convert_desc(param['desc'])))
    if obj.get('type', None):
        f.write('\n* @returns {{{0}}}'.format(convert_type(obj['type'])))
    if obj.get('url', None):
        f.write("\n* {{@link {0}}}".format(obj['url']))
    if obj.get('note', None):
        f.write("\n* Note: {0}".format(obj['note']))
    if obj.get('example', None):
        f.write("\n* @example")
        for line in obj['example'].split("\n"):
            f.write("\n* {0}".format(line))

    f.write("\n*/")


def is_optional(p):
    return p.get('default', None) or 'default' in p.get('desc', "").lower()


def build_type(prop):
    if 'object_schema' in prop:
        type_str = "{"
        for field_data in prop['object_schema']:
            if field_data.get('desc', None):
                type_str += "\n/**\n* {0}\n*/".format(field_data['desc'])
            type_str += "\n{}:{}".format(field_data['name'],
                                         convert_type(field_data['type']))
        type_str += "}"
    else:
        type_str = convert_type(prop['type'])
    return type_str


def build_signal_type(signal):
    params = build_params_list(signal)
    sig = ",".join(["{}: {}".format(s[0], s[1]) for s in params])
    type_str = build_type(signal)
    return "QSignal<({0}) => {1}>".format(sig, type_str)


def build_params_list(slot):
    params = []
    broke_optional = False
    for p in slot['params']:
        if not broke_optional:
            if is_optional(p):
                broke_optional = True
        param_name = p['name']
        if broke_optional:
            param_name += "?"
        param_type = build_type(p)
        params.append((param_name, param_type))
    return params


def write_ts_from_interface(data: dict, f: typing.TextIO):
    type_str = build_type(data)
    write_jsdoc(f, data)
    f.write(f"\ndeclare interface {data['name']} {type_str}")


def write_ts_from_class(cls: dict, f: typing.TextIO):
    is_module = cls.get('is_namespace', False)
    is_static = not 'parent' in cls or cls['parent'] in [
        'GlobalObject', 'BAPP_SpecialFolders']
    has_namespace = cls.get('namespace', None) != None
    if has_namespace:
        f.write('\ndeclare namespace {} {{'.format(cls['namespace']))
    static_str = ""
    if is_static:
        static_str = "static "
    # is_module = not 'parent' in cls or cls['parent'] in ['GlobalObject', 'BAPP_SpecialFolders']
    write_jsdoc(f, cls)
    if is_module:
        f.write('\ndeclare module {} {{'.format(cls['name']))
    else:
        # if cls['name'] == 'File':
        #     f.write('\ndeclare interface {} extends {} {{'.format(cls['name'], cls['parent']))
        # else:
        declare_prefix = 'declare '
        if has_namespace:
            declare_prefix = ''
        if cls.get('parent', None):
            f.write('\n{}class {} extends {} {{'.format(declare_prefix,
                                                        cls['name'], cls['parent']))
        else:
            f.write('\n{}class {} {{'.format(declare_prefix, cls['name']))
    used_names = []
    for slot in cls['slots']:
        if slot['name'].startswith('~'):
            continue  # Ignore destructor
        prefix = ""
        if not slot['name'] in used_names:
            used_names.append(slot['name'])
        if slot['name'] in RESERVED_WORDS:
            prefix = "// /* Invalid - Reserved word */"
        if slot.get('invalid', False):
            prefix = '// /* Invalid - Overriding method in parent class with different parameters */'
        write_jsdoc(f, slot)
        params = build_params_list(slot)
        sig = ",".join(["{}: {}".format(p[0], p[1]) for p in params])
        type_str = build_type(slot)
        if is_module:
            f.write('\n{prefix}function {name} ({sig}): {type};\n'.format(
                prefix=prefix, name=slot['name'], sig=sig, type=type_str))
        else:
            if slot['name'] == cls['name']:
                f.write('\nconstructor ({sig});\n'.format(
                    name=slot['name'], sig=sig, type=type_str))
            else:
                f.write('\n{prefix}public {static}{name} ({sig}): {type};\n'.format(
                    prefix=prefix, static=static_str, name=slot['name'], sig=sig, type=type_str))
    for signal in cls.get('signals', []):
        if not signal['name'] in used_names:
            used_names.append(signal['name'])
        prefix = ""
        if signal['name'] in RESERVED_WORDS:
            prefix = "// /* Invalid - Reserved word */"
        # sig = ",".join(["{}: {}".format(s['name'], build_type(s)) for s in slot['params']])
        # type_str = build_type(signal)
        write_jsdoc(f, signal)
        type_str = build_signal_type(signal)
        f.write('\n{prefix}public {name}: {type};\n'.format(
            prefix=prefix, name=signal['name'], type=type_str))
    for prop in cls.get('props', []):
        prefix = ''
        if prop['name'] in RESERVED_WORDS:
            prefix = "// /* Invalid - Reserved word */"
        elif prop['name'] in used_names:
            prefix = '// /* Invalid - Duplicate property name */ '
        elif not prop['name'] in used_names:
            used_names.append(prop['name'])
        write_jsdoc(f, prop)
        type_str = build_type(prop)
        if is_module:
            f.write('\n{prefix}var {name}: {type};\n'.format(
                prefix=prefix, name=prop['name'], type=type_str))
        else:
            f.write('\n{prefix}{static}{name}: {type};\n'.format(
                prefix=prefix, static=static_str, name=prop['name'], type=type_str))
    if has_namespace:
        f.write('\n}')
    f.write("\n}\n\n")
